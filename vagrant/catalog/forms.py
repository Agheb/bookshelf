from flask.ext.wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import InputRequired


class BookForm(FlaskForm):
    title = StringField('Title', validators=[InputRequired()])
    author = StringField('Author', validators=[InputRequired()])
    isbn = StringField('ISBN-10', validators=[InputRequired()])
    genre = StringField('Genre', validators=[InputRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Add')
