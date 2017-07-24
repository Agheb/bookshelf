import os
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from config import config, Auth
from flask_uploads import configure_uploads, UploadSet, IMAGES
from flask_oauthlib.client import OAuth

"""avoid to run Flask App over https"""
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

""" Flask App Creation """

app = Flask(__name__)
app.config.from_object(config['dev'])
# supress warnings caused by Flask-SQLAlchemy Extension
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Flask-Uploads
images = UploadSet('images', IMAGES)
configure_uploads(app, images)

# Flask-OAuth
oauth = OAuth(app)
google = oauth.remote_app(
    'google',
    consumer_key=Auth.CLIENT_ID,
    consumer_secret=Auth.CLIENT_SECRET,
    request_token_params=Auth.SCOPE,
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url=Auth.TOKEN_URI,
    authorize_url=Auth.AUTH_URI,
)


login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.session_protection = "strong"

"""
Ignore PEP8 Violation because modules must be imported after the application
object is created (http://flask.pocoo.org/docs/0.12/patterns/packages/)
"""

import bookshelf.views
import bookshelf.forms
