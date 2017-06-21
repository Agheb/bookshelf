import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Auth:
    CLIENT_ID = ('7ot1r4jri1qmlkqadnj0ksrfci8ql034'
                 '.apps.googleusercontent.com')
    CLIENT_SECRET = 'JXf7Ic_jfCam1S7lBJalDyPZ'
    REDIRECT_URI = 'https://localhost:5000/gCallback'
    AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
    TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'
    USER_INFO = 'https://www.googleapis.com/userinfo/v2/me'
    SCOPE = ['profile', 'email']


class Config:
    APP_NAME = "Bookshelf Client"
    SECRET_KEY = os.environ.get("SECRET_KEY") or "Wl17sm090nFlvE-cmx9Q4hRm"


class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, "dev.db")


class ProdConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, "prod.db")


config = {
    "dev": DevConfig,
    "prod": ProdConfig,
    "default": DevConfig
}