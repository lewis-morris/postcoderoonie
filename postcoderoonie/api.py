import datetime
from collections import OrderedDict

from flask import Blueprint, request, jsonify
import json
import logging
from sqlalchemy.sql import or_

from postcoderoonie import limiter
from postcoderoonie.functions import inject_start
from postcoderoonie.models import Places, Request

from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)
api = Blueprint('api', __name__, url_prefix="/api")

result_limit = 25

@api.errorhandler(Exception)
def server_error_unknown(err):
    return build_response(status=400, error="Bad request", message="Please reformat your request")

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
                   result_length=None, current_page=None, error=None, date_start=None):

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


    return response, status

def get_bool(val):
    return val in [1,"1",True,"true","True"]

def do_extra_requests(q):
    active = request.args.get("active", request.args.get("?active", None))
    if active:
        q = q.filter(Places.active==get_bool(active))
    return q


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


def check_postcodes_search(page, total_pages, limit, postcode, sal=None):
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
    params_invalid_response = check_postcodes_search(page, total_pages, limit, code, (start,end))
    if params_invalid_response:
        return params_invalid_response

    # proceed if ok
    pl = q.limit(limit).offset(page).all()

    if count > 0:
        return build_response(pl, result_count=count, total_pages=total_pages, result_length=limit,
                              current_page=page, date_start=kwargs["start_date"])

    return build_response(status=200, message="Requested content not found", date_start=kwargs["start_date"])
