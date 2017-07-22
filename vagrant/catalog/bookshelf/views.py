import datetime
import json
import forms
from bookshelf import app, db, login_manager, images, google
from sqlalchemy import desc
from flask import render_template, request, \
    redirect, url_for, jsonify, session, flash
from flask_login import login_required, login_user, \
    logout_user, current_user, UserMixin
from config import Auth


""" DB Models """


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=True)
    avatar = db.Column(db.String(200))
    email = db.Column(db.String(250), nullable=False)
    auth_id = db.Column(db.String(250), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    active = db.Column(db.Boolean, default=False)


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


@app.route('/')
@app.route('/collection')
def show_collection():
    genres = db.session.query(Genre).all()
    books = db.session.query(Item).all()

    return render_template('collection.html', genres=genres,
                           books=books)


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
                           genre_name=name)


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
@login_required
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
            flash('Book added')
            return redirect(url_for('show_collection'))
        else:
            flash('All fields are required')
            return render_template('add_form.html', form=form)
    elif request.method == 'GET':
        return render_template('add_form.html', form=form)


@app.route('/book/<bookid>/edit', methods=['GET', 'POST'])
@login_required
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


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('show_collection'))

    return google.authorize(callback=url_for('callback', _external=True))


@app.route('/callback')
def callback():
    resp = google.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['google_token'] = (resp['access_token'], '')
    resp = google.get('userinfo')
    # look for user in db
    user = User.query.filter_by(auth_id=resp.data['id']).first()

    if user is None:
        user = User()
        user.name = resp.data['name']
        user.email = resp.data['email']
        user.avatar = resp.data['picture']
        user.auth_id = resp.data['id']
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect(url_for('show_collection'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('show_landing'))


@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')
