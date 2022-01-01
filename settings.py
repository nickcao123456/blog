import os


class Config:
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@127.0.0.1:3306/Blogtest'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    # secret_key
    SECRET_KEY = 'kdjklfjkd87384hjdhjh'
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_DIR = os.path.join(BASE_DIR,'static')
    TEMPLATE_DIR = os.path.join(BASE_DIR,'templates')
    UPLOAD_ICON_DIR = os.path.join(STATIC_DIR, 'upload/icon')
    UPLOAD_PHONE_DIR = os.path.join(STATIC_DIR, 'upload/phone')

class DevelopmentConfig(Config):
    ENV = 'development'


class ProductionConfig(Config):
    ENV = 'production'