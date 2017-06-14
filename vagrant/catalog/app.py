from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Genre, Item


app = Flask(__name__)

engine = create_engine('sqlite:///bookshelf.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/home')
def show_login():
    return render_template('layout.html')


@app.route('/genre/JSON')
def get_genre_json():
    items = session.query(Genre).all()
    return jsonify(GenreItems=[i.serialize for i in items])


@app.route('/genre/new', methods=['GET', 'POST'])
def new_genre():
    if request.method == 'POST':
        genre_item = Genre(name=request.form['name'])
        session.add(genre_item)
        session.commit()

        return redirect(url_for('get_genre_json'))

if __name__ == '__main__':
    app.debug = True
    app.run(port=5003)
