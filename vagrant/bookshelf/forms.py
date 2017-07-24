import views
from bookshelf import images, db
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import InputRequired
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from flask_wtf.file import FileField, FileAllowed, FileRequired


def genre_choices():
    return db.session.query(views.Genre)


class BookForm(FlaskForm):
    title = StringField('Title', validators=[InputRequired()])
    author = StringField('Author', validators=[InputRequired()])
    genre = QuerySelectField('Genre', query_factory=genre_choices,
                             allow_blank=False, validators=[InputRequired()])
    description = TextAreaField('Description')
    image = FileField('Upload Bookcover', validators=[
                      FileRequired(), FileAllowed(images, 'Images only!')])
    submit = SubmitField('Add')


class EditForm(BookForm):
    image = FileField('Upload new Bookcover', validators=[
                      FileAllowed(images, 'Images only!')])
    submit = SubmitField('Edit')
