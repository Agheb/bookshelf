#!/bin/env python

from functools import wraps
from flask import (jsonify, redirect, render_template, request, session,
                   url_for)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import desc
from model import Genre, Item, User
import forms
from bookshelf import app, db, google, images, login_manager


def owner(bookid):
    """helper to return owner of book in unicode"""


def authorize_required(func):
    """ Decorator for user authorization"""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        owner = Item.query.get(kwargs['bookid']).owner
        if int(current_user.get_id()) == owner:
            return func(*args, **kwargs)
        else:
            owner = Item.query.get(kwargs['bookid']).owner
            return render_template('unauthorized.html',
                                   name=User.query.get(owner).name)

    return decorated_view


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/collection/JSON')
def catalogJSON():
    """ return all bookshelf data in JSON """
    genres = db.session.query(Item).all()
    return jsonify(Items=[i.serialize for i in genres])


@app.route('/book/<int:bookid>/JSON')
def book_JSON(bookid):
    """ return book data by given book_id in JSON """
    item = Item.query.get(bookid)
    return jsonify(item.serialize)


@app.route('/')
@app.route('/collection')
@app.route('/collection/<int:page>')
def show_collection(page=1):
    """ Main view """
    genres = Genre.query.all()
    count = Item.query.count()
    # descending order by date
    book_q = Item.query.order_by(desc(Item.added_at))
    # handle pagination with Flask-SQLAlchemy
    books = book_q.paginate(page, 3, False)
    return render_template('collection.html', genres=genres,
                           books=books, count=count)


@app.route('/genre/<int:genreid>')
@app.route('/genre/<int:genreid>/<int:page>')
def show_genre_items(genreid, page=1):
    """ Genre View (all items per genre) """
    all_genres = Genre.query.all()
    curr_genre = Genre.query.get(genreid)
    count = Item.query.count()
    books = Genre.query.get(genreid).items.paginate(page, 3, False)
    return render_template('genre.html', genres=all_genres, books=books,
                           curr_genre=curr_genre, count=count)


@app.route('/genre/new', methods=['GET', 'POST'])
def new_genre():
    """ Add new genre """
    if request.method == 'POST':
        genre_item = Genre(name=request.form['name'])
        db.session.add(genre_item)
        db.session.commit()

        return redirect(url_for('show_collection'))


@app.route('/book/add', methods=['GET', 'POST'])
@login_required
def add():
    """ Add book form view """
    form = forms.BookForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            # store actual image in filesystem (not in db !)
            img_filename = images.save(request.files['image'])
            img_url = images.url(img_filename)

            new_book = Item(title=form.title.data,
                            author=form.author.data,
                            genre_id=form.genre.data.id,
                            description=form.description.data,
                            img_url=img_url,
                            owner=current_user.get_id(),
                            img_filename=img_filename)
            db.session.add(new_book)
            db.session.commit()
            return redirect(url_for('show_collection'))
        else:

            return render_template('add_form.html', form=form)

    elif request.method == 'GET':
        return render_template('add_form.html', form=form)


@app.route('/book/<int:bookid>/edit', methods=['GET', 'POST'])
@login_required
@authorize_required
def edit_book(bookid):
    """ Edit book form view """
    book = Item.query.get(bookid)
    # pass existing image url for preview in form
    img_url = Item.query.get(bookid).img_url

    # pre-populate edit form
    form = forms.EditForm(obj=book)

    if request.method == 'POST':
        if form.validate_on_submit():

            # check for new image and update it in db
            if request.files['image']:
                img_filename = images.save(request.files['image'])
                img_url = images.url(img_filename)
                book.img_filename = img_filename
                book.img_url = img_url

            form.populate_obj(book)
            db.session.commit()
            return redirect(url_for('show_collection'))
        else:
            return render_template('edit_form.html', form=form, id=bookid,
                                   img=img_url)
    elif request.method == 'GET':
        return render_template('edit_form.html', form=form, id=bookid,
                               img=img_url)


@app.route('/book/<int:bookid>/delete', methods=['POST'])
@login_required
def delete_book(bookid):
    """ Delete book """
    # user authorization
    if int(current_user.get_id()) == Item.query.get(bookid).owner:
        book = Item.query.get(bookid)
        db.session.delete(book)
        db.session.commit()
        return jsonify({
                       'status': 'OK',
                       'response': 'Book removed from shelf',
                       'success': True})
    else:
        return ('UNAUTHORIZED', 401)


@app.route('/book/<int:bookid>')
def show_book(bookid):
    """ Book detail View """
    book = Item.query.filter_by(id=bookid).first()
    return render_template('book_view.html', book=book)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('show_collection'))
    # redirect user to google for authorization
    return google.authorize(callback=url_for('callback', _external=True))


@app.route('/callback')
def callback():
    """ Handle authorization response """
    resp = google.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    # save access token in session
    session['google_token'] = (resp['access_token'], '')
    # fetch protected user data resource
    resp = google.get('userinfo')

    # search for user in db
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


@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('logout.html')
