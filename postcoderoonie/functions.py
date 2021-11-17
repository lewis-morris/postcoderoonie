import datetime
from functools import wraps


def inject_start(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        return func(*args, **kwargs, start_date=datetime.datetime.utcnow())

    return decorated_view
