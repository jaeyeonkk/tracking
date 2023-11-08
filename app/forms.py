from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    validators,
    TextAreaField,
    FileField,
)
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    useremail = StringField("이메일", validators=[DataRequired()])
    password = PasswordField("비밀번호", validators=[DataRequired()])


class SignupForm(FlaskForm):
    name = StringField("Name", [validators.DataRequired()])
    useremail = StringField("Email", [validators.DataRequired(), validators.Email()])
    password = PasswordField("Password", [validators.DataRequired()])
    submit = SubmitField("Sign Up")


class BoardWriteForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    content = TextAreaField("Content", validators=[DataRequired()])
    file = FileField("File")


class BoardEditForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    content = TextAreaField("Content", validators=[DataRequired()])
    file = FileField("File")
    remove_files = FileField("Remove Files")
    original_files = FileField("Original Files")


class CommentForm(FlaskForm):
    comment = TextAreaField("Comment", validators=[DataRequired()])
    submit = SubmitField("Add Comment")


class DeleteForm(FlaskForm):
    pass
