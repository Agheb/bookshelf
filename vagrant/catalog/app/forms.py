from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import InputRequired
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask_uploads import UploadSet, IMAGES

images = UploadSet('images', IMAGES)


class BookForm(FlaskForm):
    title = StringField('Title', validators=[InputRequired()])
    author = StringField('Author', validators=[InputRequired()])
    genre = StringField('Genre', validators=[InputRequired()])
    description = TextAreaField('Description')
    image = FileField('Upload Bookcover', validators=[FileRequired(), FileAllowed(images, 'Images only!')])
    submit = SubmitField('Add')
