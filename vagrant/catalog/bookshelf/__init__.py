import os
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_uploads import configure_uploads, UploadSet, IMAGES

"""avoid to run Flask App over https"""
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

""" Flask App Creation """

app = Flask(__name__)
app.config.from_object(config['dev'])
# supress warnings caused by Flask-SQLAlchemy Extension
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.session_protection = "strong"

# Configuration for flask-uploads
images = UploadSet('images', IMAGES)
configure_uploads(app, images)

import bookshelf.views
import bookshelf.forms

