from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    validators,
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


class AcceptForm(FlaskForm):
    submit = SubmitField("동의")
