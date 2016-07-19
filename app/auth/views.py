# -*- coding: utf-8 -*-

from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .. import db
from ..models import User, Activation
from ..email import send_email
from .forms import LoginForm, ActivationForm, ChangePasswordForm, PasswordResetRequestForm, PasswordResetForm, ChangeEmailForm


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed and request.endpoint[:5] != 'auth.' and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous:
        return redirect(url_for('main.index'))
    if current_user.confirmed:
        return redirect(url_for('main.profile'))
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            # flash('欢迎登录云英语教育服务支撑系统！')
            return redirect(request.args.get('next') or url_for('main.profile'))
        flash('无效的用户名或密码')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@auth.route('/activate', methods=['GET', 'POST'])
def activate():
    form = ActivationForm()
    if form.validate_on_submit():
        activations = Activation.query.filter_by(name=form.name.data).all()
        for activation in activations:
            if activation.verify_activation_code(form.activation_code.data):
                if not activation.activated:
                    activation.activated = True
                    db.session.add(activation)
                    user = User(email=form.email.data, name=form.name.data, role_id=activation.role_id, password=form.password.data)
                    db.session.add(user)
                    db.session.commit()
                    token = user.generate_confirmation_token()
                    send_email(user.email, u'确认您的邮箱账户', 'auth/mail/confirm', user=user, token=token)
                    flash(u'激活成功，请登录！')
                    # flash(u'一封确认邮件已经发送到您的邮箱')
                    return redirect(url_for('auth.login'))
                flash(u'%s的云英语账户已处于激活状态' % form.name.data)
                flash(u'请直接登录')
                return redirect(url_for('auth.login'))
        flash(u'激活信息有误或者不存在')
    return render_template('auth/activate.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.profile'))
    if current_user.confirm(token):
        flash(u'您的邮箱账户确认成功！')
    else:
        flash(u'确认链接无效或者已经过期')
        return redirect(url_for('auth.unconfirmed'))
    return redirect(url_for('main.profile'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, u'确认您的邮箱账户', 'auth/mail/confirm', user=current_user, token=token)
    flash(u'一封新的确认邮件已经发送到您的邮箱')
    return redirect(url_for('main.index'))


# @auth.route('/change-password', methods=['GET', 'POST'])
# @login_required
# def change_password():
#     form = ChangePasswordForm()
#     if form.validate_on_submit():
#         if current_user.verify_password(form.old_password.data):
#             current_user.password = form.password.data
#             db.session.add(current_user)
#             flash('Your password has been updated.')
#             return redirect(url_for('main.index'))
#         else:
#             flash('Invalid password.')
#     return render_template("auth/change_password.html", form=form)


# @auth.route('/reset', methods=['GET', 'POST'])
# def password_reset_request():
#     if not current_user.is_anonymous:
#         return redirect(url_for('main.index'))
#     form = PasswordResetRequestForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(email=form.email.data).first()
#         if user:
#             token = user.generate_reset_token()
#             send_email(user.email, 'Reset Your Password', 'auth/email/reset_password', user=user, token=token, next=request.args.get('next'))
#         flash('An email with instructions to reset your password has been sent to you.')
#         return redirect(url_for('auth.login'))
#     return render_template('auth/reset_password.html', form=form)


# @auth.route('/reset/<token>', methods=['GET', 'POST'])
# def password_reset(token):
#     if not current_user.is_anonymous:
#         return redirect(url_for('main.index'))
#     form = PasswordResetForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(email=form.email.data).first()
#         if user is None:
#             return redirect(url_for('main.index'))
#         if user.reset_password(token, form.password.data):
#             flash('Your password has been updated.')
#             return redirect(url_for('auth.login'))
#         else:
#             return redirect(url_for('main.index'))
#     return render_template('auth/reset_password.html', form=form)


# @auth.route('/change-email', methods=['GET', 'POST'])
# @login_required
# def change_email_request():
#     form = ChangeEmailForm()
#     if form.validate_on_submit():
#         if current_user.verify_password(form.password.data):
#             new_email = form.email.data
#             token = current_user.generate_email_change_token(new_email)
#             send_email(new_email, 'Confirm your email address', 'auth/email/change_email', user=current_user, token=token)
#             flash('An email with instructions to confirm your new email address has been sent to you.')
#             return redirect(url_for('main.index'))
#         else:
#             flash('Invalid email or password.')
#     return render_template("auth/change_email.html", form=form)


# @auth.route('/change-email/<token>')
# @login_required
# def change_email(token):
#     if current_user.change_email(token):
#         flash('Your email address has been updated.')
#     else:
#         flash('Invalid request.')
#     return redirect(url_for('main.index'))