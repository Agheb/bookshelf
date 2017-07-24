#!/bin/env python

from bookshelf import db
from bookshelf.views import User, Genre, Item

db.create_all()
genre_ls = ['Science fiction', 'Satire', 'Drama',
            'Action and Adventure', 'Romance',
            'Mystery', 'Horror', 'Self help']

for genre in genre_ls:
    x = Genre()
    x.name = genre
    db.session.add(x)

db.session.commit()

