from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, PasswordField
from wtforms.validators import DataRequired, URL, EqualTo
from flask_ckeditor import CKEditorField
from flask import abort
from functools import wraps
from flask import redirect, url_for, request
from flask_login import current_user


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id!=1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class RegisterForm(FlaskForm):
    username=StringField(label="Your Username",  validators=[DataRequired()])
    email=EmailField(label="Email",  validators=[DataRequired()])
    password=PasswordField(label="Password",  validators=[DataRequired()])
    repeatpassword=PasswordField(label="Repeat Password",  validators=[
        DataRequired(), EqualTo('password', message='Passwords must match')])
    signup=SubmitField(label='Register')

class LoginForm(FlaskForm):
    email=EmailField(label="Email",  validators=[DataRequired()])
    password=PasswordField(label="Password",  validators=[DataRequired()])
    signup=SubmitField(label='Login')

class CommentForm(FlaskForm):
    text=CKEditorField("Comment", validators=[DataRequired()])
    signup=SubmitField(label='Submit Comment')

# TODO: Create a CommentForm so users can leave comments below posts
