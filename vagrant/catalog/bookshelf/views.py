import datetime
import json
import forms
from bookshelf import app, db, login_manager, images
from sqlalchemy import desc
from flask import render_template, request, \
    redirect, url_for, jsonify, session, flash
from flask_login import login_required, login_user, \
    logout_user, current_user, UserMixin
from config import Auth
from requests_oauthlib import OAuth2Session
from requests.exceptions import HTTPError


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
    items = db.relationship('Item', backref=db.backref(
        'genre', lazy='joined'), lazy='dynamic')

    def __str__(self):
        return self.name

    @property
    def serialize(self):
        """return object data in easily serializeable format"""
        return {'name': self.name, 'id': self.id}


class Item(db.Model):
    __tablename__ = 'book'
    id = db.Column(db.Integer, primary_key=True)
    added_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    title = db.Column(db.String(250), nullable=False)
    author = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(250), default=None, nullable=True)
    img_filename = db.Column(db.String(250), default=None, nullable=True)
    img_url = db.Column(db.String(250), default=None, nullable=True)
    # user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # user = db.relationship(User)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'))

    @property
    def serialize(self):
        """return object data in easily serializeable format"""
        return {'item_id': self.id,
                'title': self.title,
                'author': self.author,
                'description': self.description,
                'genre': self.genre.serialize,
                'img_filename': self.img_filename,
                'img_url': self.img_url
                }


""" Main View """

@app.route('/collection')
def show_collection():
    genres = db.session.query(Genre).all()
    books = db.session.query(Item).all()

    return render_template('collection.html', genres=genres,
                           books=books, user=current_user)


@app.route('/')
@app.route('/home')
def show_landing():
    return render_template('layout.html')


""" Genre """


@app.route('/genre/<genreid>')
def show_genre_items(genreid):
    genres = Genre.query.all()
    books = Genre.query.get(genreid).items.all()
    name = Genre.query.get(genreid).name
    return render_template('collection.html', genres=genres, books=books,
                           genre_name=name, user=current_user)



@app.route('/genre/new', methods=['GET', 'POST'])
def new_genre():
    if request.method == 'POST':
        genre_item = Genre(name=request.form['name'])
        db.session.add(genre_item)
        db.session.commit()

        return redirect(url_for('get_genre_json'))


@app.route('/genre/JSON')
def get_genre_json():
    items = db.session.query(Genre).all()
    return jsonify(GenreItems=[i.serialize for i in items])


""" Books View """


@app.route('/book/add', methods=['GET', 'POST'])
def add():
    form = forms.BookForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            img_filename = images.save(request.files['image'])
            img_url = images.url(img_filename)
            new_book = Item(title=form.title.data,
                            author=form.author.data,
                            genre_id=form.genre.data.id,
                            description=form.description.data,
                            img_url=img_url,
                            img_filename=img_filename)
            db.session.add(new_book)
            db.session.commit()
            return redirect(url_for('show_collection'))
        else:
            flash('All fields are required')
            return render_template('add_form.html', form=form)
    elif request.method == 'GET':
        return render_template('add_form.html', form=form)


@app.route('/book/<bookid>/edit', methods=['GET', 'POST'])
def edit_book(bookid):
    book = Item.query.get(bookid)
    img_url = Item.query.get(bookid).img_url
    form = forms.EditForm(obj=book)
    if request.method == 'POST':
        if form.validate_on_submit():
            if request.files:
                img_filename = images.save(request.files['image'])
                img_url = images.url(img_filename)
                book.img_filename = img_filename
                book.img_url = img_url

            form.populate_obj(book)
            db.session.commit()
            return redirect(url_for('show_collection'))
        else:
            flash('All fields are required')
            return render_template('edit_form.html', form=form, id=bookid,
                                   img=img_url)
    elif request.method == 'GET':
        return render_template('edit_form.html', form=form, id=bookid,
                               img=img_url)


@app.route('/books/<bookid>')
def show_book(bookid):
    # TODO: add 404 Page first_or_404()
    # TODO: template file add DB Query Results
    book = Item.query.filter_by(id=bookid).first()
    return render_template('book_view.html', book=book)


@app.route('/books/<bookid>/delete', methods=['POST'])
# AJAX Post
def delete_book(bookid):
    book = Item.query.get(bookid)
    db.session.delete(book)
    db.session.commit()
    return jsonify({
        'status': 'OK',
        'response': 'Book removed from shelf',
        'success': True})


""" Authenfication/Authorization """


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

@app.route('/index')
@login_required
def index():
    return render_template('index.html')


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
