import datetime
from functools import wraps

from flask import request


def inject_start(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        return func(*args, **kwargs, start_date=datetime.datetime.utcnow())

    return decorated_view

def get_remote_ip():
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR']