# -*- coding: utf-8 -*-

from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import Activation, User


class LoginForm(Form):
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email()])
    password = PasswordField(u'密码', validators=[Required(), Length(6, 64)])
    remember_me = BooleanField(u'记住我')
    submit = SubmitField(u'登录')


class ActivationForm(Form):
    name = StringField(u'姓名', validators=[Required(), Length(1, 64)])
    activation_code = StringField(u'激活码', validators=[Required(), Length(6, 64)])
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email()])
    password = PasswordField(u'密码', validators=[Required(), EqualTo('password2')])
    password2 = PasswordField(u'确认密码', validators=[Required()])
    eula = BooleanField(u'同意云英语条款', validators=[Required()])
    submit = SubmitField(u'激活')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'%s已经做注册' % field.data)


# class RegistrationForm(Form):
#     email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
#     username = StringField('Username', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Usernames must have only letters, numbers, dots or underscores')])
#     password = PasswordField('Password', validators=[Required(), EqualTo('password2', message='Passwords must match.')])
#     password2 = PasswordField('Confirm password', validators=[Required()])
#     submit = SubmitField('Register')

#     def validate_email(self, field):
#         if User.query.filter_by(email=field.data).first():
#             raise ValidationError('Email already registered.')

#     def validate_username(self, field):
#         if User.query.filter_by(username=field.data).first():
#             raise ValidationError('Username already in use.')


class ChangePasswordForm(Form):
    old_password = PasswordField('Old password', validators=[Required()])
    password = PasswordField('New password', validators=[Required(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm new password', validators=[Required()])
    submit = SubmitField('Update Password')


class PasswordResetRequestForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
    submit = SubmitField('Reset Password')


class PasswordResetForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
    password = PasswordField('New Password', validators=[Required(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Reset Password')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')


class ChangeEmailForm(Form):
    email = StringField('New Email', validators=[Required(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[Required()])
    submit = SubmitField('Update Email Address')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')
