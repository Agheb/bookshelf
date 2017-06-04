import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    first_name = Column(String(250), nullable=False)
    last_name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    # profile_pic = Column(String(250)


class Genre(Base):
    __tablename__ = 'genre'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """return object data in easily serializeable format"""
        return {'name': self.name, 'id': self.id}


class Item_Type(Base):
    __tablename__ = 'itemtype'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


class Book(Base):
    __tablename__ = 'book'
# Add Column for Date added Timestamp
    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    author = Column(String(250), nullable=False)
    description = Column(String(250), nullable=False)
    url = Column(String(250))
    pic_url = Column(String(250))
    release_date = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    genre_id = Column(Integer, ForeignKey('genre.id'))
    genre = relationship(Genre)
    item_type_id = Column(Integer, ForeignKey('itemtype.id'))
    item_type = relationship(Item_Type)

    @property
    def serialize(self):
        """return object data in easily serializeable format"""
        return {'id': self.id,
                'title': self.title,
                'genre': self.genre,
                'item_type': self.item_type}


engine = create_engine('sqlite:///bookshelf.db')

Base.metadata.create_all(engine)
