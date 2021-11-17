import os

basedir = os.path.abspath(os.path.dirname(__file__))

class AppConfig:

    CRM_NAME = "Colemans CRM"

    FLASK_DEBUG = True
    DEBUG = True
    TESTING = True

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False

    RATELIMIT_STORAGE_URL = "redis://127.0.0.1:6379"

    SECRET_KEY = "ySHi2aYU0NetjvqHRpgN9m0iaOPSN7z2VN3jNT2RYmv2pDgSBv"
    SALT = "Bbu1oYjtanoODkTmzCZYSSdZY4zWbBOVwXpoAzs1j2ZvYyGTk0"
    MAX_CONTENT_LENGTH = 94 * 1024 * 1024
    NAME = "coleman"
    SQLALCHEMY_DATABASE_URI = "postgresql://postcodes:!¬dsalklSD56$bA58@18.134.236.107:5433/postcode"

    # SQLALCHEMY_ECHO = True
class ProductionConfig(AppConfig):
    pass
    # DATABASE_URI = 'mysql://user@localhost/foo'
    # BASE_URL = "colemanbros.co.uk"
    SERVER_NAME = "https://colemanbros.co.uk"

class DevelopmentConfig(AppConfig):
    SERVER_NAME = "localhost:5000"