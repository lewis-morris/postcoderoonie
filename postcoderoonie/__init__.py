#test deploy
#test
#test
#test
#test


import datetime

from flask_migrate import Migrate

from postcoderoonie.config import *
from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import limits.storage
from flask_redis import FlaskRedis

from postcoderoonie.functions import get_remote_ip

db = SQLAlchemy()
migrate = Migrate()
redis_client = FlaskRedis()
limiter = Limiter(key_func=get_remote_ip)
# scheduler = APScheduler()

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    with app.app_context() as app_cont:

        if test_config is None:
            # load the instance config, if it exists, when not testing
            app.config.from_object(DevelopmentConfig)
        else:
            app.config.from_object(ProductionConfig)

        # ensure the instance folder exists
        try:
            os.makedirs(app.instance_path)
        except OSError:
            pass

        from postcoderoonie.main import main
        from postcoderoonie.api import api

        from postcoderoonie.models import Places

        app.register_blueprint(main)
        app.register_blueprint(api)

        db.init_app(app)
        migrate.init_app(app, db)
        limiter.init_app(app)
        redis_client.init_app(app)

    return app


# def get_check():
#     from coleman.tasks import check_reminders
#     check_reminders()
