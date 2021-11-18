import os

basedir = os.path.abspath(os.path.dirname(__file__))

class AppConfig:
    FLASK_DEBUG = True
    DEBUG = True
    TESTING = True

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    SECRET_KEY=os.getenv("SECRET_KEY")
    RATELIMIT_STORAGE_URL = "redis://127.0.0.1:6379"
    SQLALCHEMY_DATABASE_URI = f"postgresql://postcodes:{os.getenv('SQLPASS')}@18.134.236.107:5433/postcode"

    # SQLALCHEMY_ECHO = True
class ProductionConfig(AppConfig):
    SERVER_NAME = "https://postcoderoonie.co.uk"

class DevelopmentConfig(AppConfig):
    SERVER_NAME = "localhost:5000"