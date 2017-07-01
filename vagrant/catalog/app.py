import datetime
import json
import os
from flask import Flask, render_template, request, \
    redirect, url_for, jsonify, session, flash
from flask_login import LoginManager,  login_required, login_user, \
    logout_user, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from config import config, Auth
from requests_oauthlib import OAuth2Session
from requests.exceptions import HTTPError
from forms import BookForm

"""avoid to run Flask App over https"""
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

""" Flask App Creation """

app = Flask(__name__)
app.config.from_object(config['dev'])
# supress warnings caused possibly by Flask-SQLAlchemy Extension
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret46 key'  # CSRF Protection
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.session_protection = "strong"


""" DB Models """


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=True)
    avatar = db.Column(db.String(200))
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


@app.route('/form')
def show_book():
    return render_template('form.html')


@app.route('/collection')
def show_collection():
    return render_template('collection.html')


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


@app.route('/index')
@login_required
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    google = get_google_auth()
    auth_url, state = google.authorization_url(
        Auth.AUTH_URI, access_type='offline')
    session['oauth_state'] = state
    return render_template('login.html', auth_url=auth_url)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('show_landing'))


@app.route('/add', methods=['GET', 'POST'])
def add():
    form = BookForm()
    if request.method == 'POST':
        if form.validate() is False:
            flash('All fields are required')
            return render_template('form.html', form=form)
        else:
            return 'Book added'
    elif request.method == 'GET':
        return render_template('form.html', form=form)


@app.route('/callback')
def callback():
    if current_user is not None and current_user.is_authenticated:
        return redirect(url_for('index'))
    if 'error' in request.args:
        if request.args.get('error') == 'access_denied':
            return 'You denied access.'
        return 'Error encountered.'
    if 'code' not in request.args and 'state' not in request.args:
        return redirect(url_for('login'))
    else:
        google = get_google_auth(state=session['oauth_state'])
        try:
            token = google.fetch_token(
                Auth.TOKEN_URI,
                client_secret=Auth.CLIENT_SECRET,
                authorization_response=request.url)
        except HTTPError:
            return 'HTTPError occurred.'
        google = get_google_auth(token=token)
        resp = google.get(Auth.USER_INFO)
        if resp.status_code == 200:
            user_data = resp.json()
            email = user_data['email']
            user = User.query.filter_by(email=email).first()
            if user is None:
                user = User()
                user.email = email
            user.name = user_data['name']
            print(token)
            user.tokens = json.dumps(token)
            user.avatar = user_data['picture']
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('index'))
        return 'Could not fetch your information.'


if __name__ == '__main__':
    app.debug = True
    app.run(port=5003)
