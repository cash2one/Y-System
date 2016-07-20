# -*- coding: utf-8 -*-

from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import Activation, User


class LoginForm(Form):
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    password = PasswordField(u'密码', validators=[Required(), Length(6, 64)])
    remember_me = BooleanField(u'记住我')
    submit = SubmitField(u'登录')


class ActivationForm(Form):
    name = StringField(u'姓名', validators=[Required(), Length(1, 64)])
    activation_code = StringField(u'激活码', validators=[Required(), Length(6, 64)])
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    password = PasswordField(u'密码', validators=[Required(), EqualTo('password2')])
    password2 = PasswordField(u'确认密码', validators=[Required()])
    eula = BooleanField(u'同意使用条款', validators=[Required()])
    submit = SubmitField(u'激活')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'%s已经被注册' % field.data)


class ChangePasswordForm(Form):
    old_password = PasswordField(u'旧密码', validators=[Required()])
    password = PasswordField(u'新密码', validators=[Required(), EqualTo('password2')])
    password2 = PasswordField(u'确认密码', validators=[Required()])
    submit = SubmitField(u'修改密码')


class ResetPasswordRequestForm(Form):
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    submit = SubmitField(u'请求重置密码')


class ResetPasswordForm(Form):
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    password = PasswordField(u'新密码', validators=[Required(), EqualTo('password2')])
    password2 = PasswordField(u'确认密码', validators=[Required()])
    submit = SubmitField(u'重置密码')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError(u'未知的邮箱地址')


class ChangeEmailForm(Form):
    email = StringField(u'新邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    password = PasswordField(u'密码', validators=[Required()])
    submit = SubmitField(u'修改邮箱')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'%s已经被注册' % field.data)
