import datetime

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from config import config, Auth, ProdConfig, DevConfig
from requests_oauthlib import OAuth2Session
from requests.exceptions import HTTPError

""" Flask App Creation """

app = Flask(__name__)
app.config.from_object(config['dev'])
# supress warnings caused possibly by Flask-SQLAlchemy Extension
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.session_protection = "strong"


""" DB Models """


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(250), nullable=False)
    last_name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False)
    active = db.Column(db.Boolean, default=False)
    tokens = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship(User)

    @property
    def serialize(self):
        """return object data in easily serializeable format"""
        return {'name': self.name, 'id': self.id}


class Item(db.Model):
    __tablename__ = 'book'
# Add Column for Date added Timestamp
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    author = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    url = db.Column(db.String(250))
    pic_url = db.Column(db.String(250))
    release_date = db.Column(db.String(250))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship(User)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'))
    genre = db.relationship(Genre)

    @property
    def serialize(self):
        """return object data in easily serializeable format"""
        return {'id': self.id,
                'title': self.title,
                'genre': self.genre,
                'item_type': self.item_type}


"""helper function to create Oauth2 Session """


def get_google_auth(state=None, token=None):
    if token:
        return OAuth2Session(Auth.CLIENT_ID, token=token)
    if state:
        return OAuth2Session(
            Auth.CLIENT_ID,
            state=state,
            redirect_uri=Auth.REDIRECT_URI)
    oauth = OAuth2Session(
        Auth.CLIENT_ID,
        redirect_uri=Auth.REDIRECT_URI,
        scope=Auth.SCOPE)
    return oauth


@app.route('/')
@app.route('/home')
def show_landing():
    return render_template('layout.html')


@app.route('/genre/JSON')
def get_genre_json():
    items = db.session.query(Genre).all()
    return jsonify(GenreItems=[i.serialize for i in items])


@app.route('/genre/new', methods=['GET', 'POST'])
def new_genre():
    if request.method == 'POST':
        genre_item = Genre(name=request.form['name'])
        db.session.add(genre_item)
        db.session.commit()

        return redirect(url_for('get_genre_json'))


@app.route('/login')
def show_login():
    return render_template('login.html')


if __name__ == '__main__':
    app.debug = True
    app.run(port=5003)