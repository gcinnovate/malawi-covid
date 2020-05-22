import os
import random

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'some random string'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in \
        ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    FLASKY_MAIL_SUBJECT_PREFIX = '[COVID]'
    FLASKY_MAIL_SENDER = 'COVID Admin <covid@example.com>'
    FLASKY_ADMIN = os.environ.get('COVID_ADMIN')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL')
    CELERY_BROKER_URL = os.environ.get('REDIS_URL')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL')
    GLOBAL_STATS_ENDPOINT = os.environ.get('GLOBAL_STATS_ENDPOINT', 'https://api.covid19api.com/summary')
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
            'postgresql://postgres:postgres@localhost:5431/covid'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite://'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

RAPIDPRO_API_TOKEN = ""
RAPIDPRO_API_URL = ""
SUSPECTS_MESSAGE_TEMPLATE = (
    "Hello, ${name} (${phone}) from ${district} district ${address} "
    "has been identified as a COVID-19 suspect")
CASE_MESSAGE_TEMPLATE = (
    "Hello, ${name} (${phone}) from ${district} district ${address} "
    "has been confirmed as a COVID-19 case ")

# Flows and their associated flow variables. keys represent flows
INDICATORS = {
    'covid': [
        'month', 'year', 'name', 'dob', 'sex', 'nationality', 'district', 'address',
        'status',
    ]
}

REPORT_AGGREGATE_INIDICATORS = {
    'covid': [
    ],

}

# The following are used for generating dummy data

INDICATOR_CATEGORY_MAPPING = {
    'covid': {
    }
}

# the guide random generation for the flow variables
INDICATOR_THRESHOLD = {

}

# Flow names that use a month generated from reporting date
AUTO_MONTH_FLOWS = []
INDICATORS_TO_SWAP_KEYVALS = ['referredfrom']
GLOBAL_STATS_ENDPOINT = 'https://api.covid19api.com/summary'
try:
    from local_config import *
except ImportError:
    pass
