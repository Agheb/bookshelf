#!/bin/env python
import datetime
from bookshelf import db
from flask_login import UserMixin

################
#    Model     #
################


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=True)
    avatar = db.Column(db.String(200))
    email = db.Column(db.String(250), nullable=False)
    auth_id = db.Column(db.String(250), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    active = db.Column(db.Boolean, default=False)


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
        """ Return object data in easily serializeable format"""
        return {'name': self.name,
                'id': self.id,
                }


class Item(db.Model):
    __tablename__ = 'book'
    id = db.Column(db.Integer, primary_key=True)
    added_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    title = db.Column(db.String(250), nullable=False)
    author = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(250), default=None, nullable=True)
    img_filename = db.Column(db.String(250), default=None, nullable=True)
    img_url = db.Column(db.String(250), default=None, nullable=True)
    owner = db.Column(db.Integer, default=0, nullable=True)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'))

    @property
    def serialize(self):
        """ Return object data in easily serializeable format """
        return {'item_id': self.id,
                'added_at': self.added_at,
                'title': self.title,
                'author': self.author,
                'description': self.description,
                'genre': self.genre.serialize,
                'img_filename': self.img_filename,
                'owner': self.owner,
                'img_url': self.img_url
                }
