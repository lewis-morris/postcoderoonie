import datetime

from postcoderoonie import db
from collections import OrderedDict

class Places(db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True,info={"show":False})
    postcode = db.Column(db.String(100), unique=False, nullable=True, info={"type": "id"})
    postcode_trim = db.Column(db.String(100), unique=False, nullable=True, info={"type": "id"})
    active = db.Column(db.Boolean, unique=False, nullable=True, info={"type": "id"})

    lat = db.Column(db.Float, unique=False, nullable=True, info={"type": "location"})
    long = db.Column(db.Float, unique=False, nullable=True, info={"type": "location"})
    easting = db.Column(db.Float, unique=False, nullable=True, info={"type": "location", "extra": True})
    northing = db.Column(db.Float, unique=False, nullable=True, info={"type": "location", "extra": True})
    plus_code = db.Column(db.String(100), unique=False, nullable=True, info={"type": "location", "extra": True})
    altitude = db.Column(db.Float, unique=False, nullable=True, info={"type": "location", "extra": True})

    county = db.Column(db.String(50), unique=False, nullable=True, info={"type": "zones"})
    district = db.Column(db.String(50), unique=False, nullable=True, info={"type": "zones", "extra": True})
    ward = db.Column(db.String(100), unique=False, nullable=True, info={"type": "zones"})
    country = db.Column(db.String(100), unique=False, nullable=True, info={"type": "zones"})
    parish = db.Column(db.String(100), unique=False, nullable=True, info={"type": "zones", "extra": True})
    region = db.Column(db.String(100), unique=False, nullable=True, info={"type": "zones", "extra": True})
    itl_one = db.Column(db.String(100), unique=False, nullable=True, info={"type": "zones", "extra": True})
    itl_two = db.Column(db.String(100), unique=False, nullable=True, info={"type": "zones", "extra": True})
    type = db.Column(db.String(100), unique=False, nullable=True, info={"type": "zones", "extra": True})

    date_introduced = db.Column(db.DateTime, unique=False, nullable=True, info={"type": "dates"})
    date_terminated = db.Column(db.DateTime, unique=False, nullable=True, info={"type": "dates"})
    last_updated = db.Column(db.DateTime, unique=False, nullable=True, info={"type": "dates", "extra": True})

    population = db.Column(db.Float, nullable=True, info={"type": "stats", "extra": True})
    households = db.Column(db.Float, nullable=True, info={"type": "stats", "extra": True})
    average_income = db.Column(db.Float, unique=False, nullable=True, info={"type": "stats", "extra": True})

    nearest_train = db.Column(db.String(100), unique=False, nullable=True, info={"type": "amenities", "extra": True})
    distance_to_train = db.Column(db.Float, unique=False, nullable=True, info={"type": "amenities", "extra": True})
    police = db.Column(db.String(100), unique=False, nullable=True, info={"type": "amenities", "extra": True})
    sewage_company = db.Column(db.String(100), unique=False, nullable=True, info={"type": "amenities", "extra": True})
    water_company = db.Column(db.String(100), unique=False, nullable=True, info={"type": "amenities", "extra": True})
    def get_latlon(self):
        return (self.lat, self.long)
    def json(self, extra=0):
        output = {}
        # loop all fields
        for k, v in self.__dict__.items():
            # get the field from the model
            if k in Places.__dict__:
                sql_field = Places.__dict__[k]
                # check if its valid (i.e has info attribute)
                if hasattr(sql_field,"info"):
                    # used for if we are displaying extra results or not
                    is_extra = sql_field.info.get("extra",False)
                    show = sql_field.info.get("show", True)
                    record_type = sql_field.info.get("type")
                    if show and (extra == 1 or (extra ==0 and not is_extra)):
                        # create the dic key if not already
                        if record_type not in output:
                            output[record_type] = {}
                        if type(v) == datetime.datetime:
                            output[record_type][k] = v.strftime("%Y-%m-%d")
                        else:
                            output[record_type][k] = v


        return {self.postcode:output}

class Request(db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    endpoint = db.Column(db.String(200), unique=False, nullable=True)
    base_url = db.Column(db.String(200), unique=False, nullable=True)
    full_url = db.Column(db.String(200), unique=False, nullable=True)
    ip = db.Column(db.String(100), unique=False, nullable=True)
    ms = db.Column(db.Integer, unique=False, nullable=True)
    message = db.Column(db.String(200), unique=False, nullable=True)
    error = db.Column(db.String(200), unique=False, nullable=True)
    complete = db.Column(db.Boolean, unique=False, nullable=True)
    status = db.Column(db.Integer, unique=False, nullable=True)
    time = db.Column(db.DateTime, unique=False, default=datetime.datetime.utcnow)
