import datetime
from collections import OrderedDict
from operator import itemgetter

from flask import Blueprint, request, jsonify
import json
import logging

from haversine import haversine, Unit
from sqlalchemy import func
from sqlalchemy.sql import or_

from postcoderoonie import limiter, db
from postcoderoonie.functions import inject_start
from postcoderoonie.models import Places, Request

from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)
api = Blueprint('api', __name__, url_prefix="/api")

result_limit = 25


@api.errorhandler(Exception)
def server_error_unknown(err):
    return build_response(status=400, error="Bad request", message="Please reformat your request")


@api.errorhandler(TypeError)
def server_error_type_error(err):
    return build_response(status=400, error="Bad request", message="Required parameter missing from query")


@api.errorhandler(500)
@inject_start
def server_error(e, *args, **kwargs):
    return build_response(status=500, error="Server error", message="An unhandled exception occurred")


@api.errorhandler(429)
@inject_start
def ratelimit_handler(e, *args, **kwargs):
    return build_response(status=429, error="Rate hit", message="Rate limit exceeded")


@api.errorhandler(404)
@inject_start
def notfound_handler(e, *args, **kwargs):
    return build_response(status=404, error="Resource not found", message="Endpoint not found")


def build_response(result=None, status=200, message=None, result_count=None, total_pages=None,
                   result_length=None, current_page=None, error=None, date_start=None, extra=None):
    # get extras that work on all queries
    depth = int(request.args.get("extra", request.args.get("?extra", 0)))

    # build the data
    if not result:
        result_data = None
        result_text = "There were no results"
    elif type(result) is list:
        result_data = [x.json(depth) for x in result]
        result_text = "results"
    else:
        result_data = result.json(depth)
        result_text = "result"

    # get status
    text_status = "ok"
    complete = True
    if str(status)[0] != "2" and not error:
        complete = False
        text_status = "error"
    elif error:
        complete = False
        text_status = error

    # create the base response

    response = OrderedDict({"status": text_status, "url": request.url})

    if date_start:
        runtime = str(int((datetime.datetime.now() - date_start).total_seconds() * 1000)) + "ms"
        response["date_start"] = date_start.utcnow().isoformat()
        response["runtime"] = runtime

    # add message if there is one
    if message:
        response["message"] = message
    # add result messages
    if result:
        response[result_text] = result_data
    # add result count if there is pagination
    if result_count:
        response["result_count"] = result_count
    # add pages if pages
    if total_pages:
        response["total_pages"] = total_pages
    # add pages if pages
    if result_length:
        response["result_length"] = result_length
    # add pages if pages
    if current_page or current_page == 0:
        response["current_page"] = current_page

    # extra results information
    if extra:
        response["details"] = extra

    # save the request into the database
    req = Request(endpoint=request.endpoint, full_url=request.full_path, base_url=request.base_url,
                  ip=get_remote_address(), complete=complete, message=message if message else None,
                  error=error if error else None, status=status,
                  ms=int(runtime.replace("ms", "")) if date_start else None)
    db.session.add(req)
    db.session.commit()

    return response, status


def get_bool(val):
    return val in [1, "1", True, "true", "True"]


def do_extra_requests(q):
    """
    All requests can be filtered by the "Extra requests" and these happen here.
    :param q: sqlalchemy query
    :return: sqlalchemy filtered query
    """
    active = request.args.get("active", request.args.get("?active", None))
    if active:
        q = q.filter(Places.active == get_bool(active))
    return q


@api.route("/status")
@inject_start
def get_status(*args, **kwargs):
    """
    Returns postcodes based on exact matches, can be used for validation of postcodes.
    :return:
    """

    return build_response(status=200, date_start=kwargs["start_date"], message= "all systems are go")


@api.route("/postcode")
@limiter.limit("10000/hour")
@limiter.limit("3/second")
@inject_start
def get_postcode(*args, **kwargs):
    """
    Returns postcodes based on exact matches, can be used for validation of postcodes.
    :return:
    """

    # get the request params
    code = request.args.get("postcode", request.args.get("?postcode", "").upper())

    if code:
        # make sure that the postcode is upper as thats how its stored
        code = code.upper()
        # if pipes are used then user expects a list
        if "|" in code:
            code = code.split("|")
            pl = Places.query.filter(or_(Places.postcode.in_(code), Places.postcode_trim.in_(code)))
            pl = do_extra_requests(pl).all()
        else:
            pl = Places.query.filter(or_(Places.postcode == code, Places.postcode_trim == code))
            pl = do_extra_requests(pl).first()

        if pl:
            return build_response(pl, date_start=kwargs["start_date"])
        return build_response(status=200, message="Requested content not found", date_start=kwargs["start_date"])

    return server_error_type_error(TypeError("Params missing"))

@api.route("/postcodes")
@limiter.limit("10200/hour")
@limiter.limit("30/second")
@inject_start
def get_postcodes(*args, **kwargs):
    """
    Used to search for wildcard entries for location search
    :return
    """

    # get the request params
    code = request.args.get("postcode", request.args.get("?postcode", "").upper())
    limit = int(request.args.get("results", request.args.get("?results", 10)))
    page = int(request.args.get("page", request.args.get("?page", 0)))

    if code:
        # make sure that the postcode is upper as thats how its stored
        code = code.upper()

        # get the query
        q = Places.query.filter(
            or_(Places.postcode.like("%" + code + "%")))

        # used for any extra requests we might have missed
        q = do_extra_requests(q)

        # get total page counts
        count = q.count()
        total_pages = int(count / limit)

        # check the query
        params_invalid_response = check_postcodes_search(page, total_pages, limit, code)
        if params_invalid_response:
            return params_invalid_response

        # proceed if ok
        pl = q.limit(limit).offset(page).all()

        if count > 0:
            return build_response(pl, result_count=count, total_pages=total_pages, result_length=limit,
                                  current_page=page, date_start=kwargs["start_date"])

        return build_response(status=200, message="Requested content not found", date_start=kwargs["start_date"])

    return server_error_type_error(TypeError("Params missing"))


def check_postcodes_search(page, total_pages, limit, postcode, sal=None):
    """
    Validates the request and returns response if not valid
    :param page: page number of the paginated request
    :param total_pages: Total page count of paginated request
    :param limit: limit of the sql query - fails if too high
    :param postcode: postcode length checker
    :param sal: salary min/ max
    :return: Response / None
    """
    if limit > result_limit:
        return build_response(status=400, message=f"Results parameter > {result_limit}")
    if page > total_pages:
        return build_response(status=400, message="Requested page > page count")
    if postcode is not None and len(postcode) < 3:
        return build_response(status=400, message="Postcode search too broad, please increase length of query")
    if sal:
        if sal[0] > sal[1]:
            return build_response(status=400, message="Start Salary > End Salary")


@api.route("/salary")
@limiter.limit("10200/hour")
@limiter.limit("30/second")
@inject_start
def get_salary(*args, **kwargs):
    """
    Used to search for wildcard entries for location search
    :return
    """

    # get the request params
    code = request.args.get("postcode", request.args.get("?postcode", None))
    start = int(request.args.get("start_sal", request.args.get("?start_sal", "")))
    end = int(request.args.get("end_sal", request.args.get("?end_sal", "")))
    page = int(request.args.get("page", request.args.get("?page", 0)))
    limit = int(request.args.get("limit", request.args.get("?limit", 10)))

    # Query the salary
    q = Places.query.filter(Places.average_income >= start, Places.average_income <= end)

    # filter postcode if needed
    if code:
        code = code.upper()
        q = q.filter(
            or_(Places.postcode.like("%" + code + "%")))

    # deal with any extra requests
    q = do_extra_requests(q)

    # get total page counts
    count = q.count()
    total_pages = int(count / limit)

    # check the query
    params_invalid_response = check_postcodes_search(page, total_pages, limit, code, (start, end))
    if params_invalid_response:
        return params_invalid_response

    # proceed if ok
    pl = q.limit(limit).offset(page).all()

    if count > 0:
        return build_response(pl, result_count=count, total_pages=total_pages, result_length=limit,
                              current_page=page, date_start=kwargs["start_date"])

    return build_response(status=200, message="Requested content not found", date_start=kwargs["start_date"])

@api.route("/distance")
@limiter.limit("10200/hour")
@limiter.limit("30/second")
@inject_start
def get_distance(*args, **kwargs):
    """
    Used to search for wildcard entries for location search
    :return
    """

    # get the request params
    code_one = request.args.get("postcode_one", request.args.get("?postcode_one", None)).upper().replace(" ","")
    code_two = request.args.get("postcode_two", request.args.get("?postcode_two", None)).upper().replace(" ","")
    unit = request.args.get("unit", request.args.get("?unit", "m"))

    # Query the two postcodes
    q = Places.query.filter(Places.postcode_trim.in_([code_one,code_two]))

    # deal with any extra requests
    results = do_extra_requests(q).all()

    if len(results) == 2:
        unit = Unit.KILOMETERS if unit.lower() == "km" else Unit.MILES
        distance = round(haversine(results[0].get_latlon(), results[1].get_latlon(), unit),3)
        return build_response(results,  date_start=kwargs["start_date"], extra={"distance":distance, "unit":unit.name.lower()})

    return build_response(status=200, message="One or more of requested content not found", date_start=kwargs["start_date"])


@api.route("/api-use-review/<q>")
def get_avg_ms(q):
    """
    Used to get the avg ms response time and count -> displayed on frontend
    :param q:
    :return:
    """
    query = db.session.query(Request).filter(Request.base_url == f"{request.url_root}api/{q}", Request.complete == True)
    avg = query.with_entities(func.avg(Request.ms)).first()
    return {"avg": int(avg[0]), "count": query.count()}, 200


@api.route("/api-response/<q>")
def get_api_response(q):
    """
    Used to get a list of response times for each endpoint -> plots chart on the frontend
    :param q:
    :return:
    """
    query = db.session.query(Request.ms, Request.time).filter(Request.base_url == f"{request.url_root}api/{q}",
                                                              Request.complete == True).order_by(Request.time).limit(
        100).all()
    data = [[i, x[0]] for i, x in enumerate(query)]
    return {"data": list(map(itemgetter(1), data)), "time": list(map(itemgetter(0), data))}, 200
