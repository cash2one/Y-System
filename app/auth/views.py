# -*- coding: utf-8 -*-

from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .forms import LoginForm, ActivationForm, ChangePasswordForm, ResetPasswordRequestForm, ResetPasswordForm, ChangeEmailForm
from .. import db
from ..models import User, Role
from ..email import send_email, send_emails
from ..notify import get_announcements, add_feed


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        add_feed(user=current_user._get_current_object(), event=u'请求访问', category=u'access', ignore_in=30*60)
        if not current_user.activated and request.endpoint[:13] != 'auth.activate' and request.endpoint != 'static':
            logout_user()
            return redirect(url_for('auth.activate'))
        if not current_user.confirmed and request.endpoint[:5] != 'auth.' and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous:
        return redirect(url_for('main.index'))
    if current_user.confirmed:
        return redirect(current_user.index_url)
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash(u'您已经登录', 'info')
        return redirect(request.args.get('next') or current_user.index_url)
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower(), created=True, deleted=False).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            get_announcements(type_name=u'登录通知', flash_first=True)
            add_feed(user=user, event=u'登录系统', category=u'access')
            return redirect(request.args.get('next') or user.index_url)
        flash(u'无效的用户名或密码', category='error')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    add_feed(user=current_user._get_current_object(), event=u'登出系统', category=u'access')
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/activate', methods=['GET', 'POST'])
def activate():
    if current_user.is_authenticated and current_user.confirmed:
        flash(u'您已经登录', category='info')
        return redirect(request.args.get('next') or current_user.index_url)
    form = ActivationForm()
    if form.validate_on_submit():
        new_user = User.query.filter_by(email=form.email.data.lower(), created=True, activated=False, deleted=False).first()
        if new_user is not None and new_user.verify_password(form.activation_code.data):
            new_user.activate(new_password=form.password.data)
            token = new_user.generate_confirmation_token()
            send_email(new_user.email, u'确认您的邮箱账户', 'auth/mail/confirm', user=new_user, token=token)
            login_user(new_user, remember=False)
            flash(u'激活成功！', category='success')
            flash(u'一封确认邮件已经发送至您的邮箱', category='info')
            send_emails([user.email for user in User.users_can(u'管理用户').all()], u'新用户：%s' % (new_user.name_alias), 'auth/mail/new_user', user=new_user)
            add_feed(user=new_user, event=u'激活账户', category=u'auth')
            return redirect(url_for('auth.unconfirmed'))
        flash(u'激活信息有误，或账户已处于激活状态', category='error')
    return render_template('auth/activate.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(current_user.index_url)
    if current_user.confirm(token):
        flash(u'您的邮箱账户确认成功！', category='success')
        add_feed(user=current_user._get_current_object(), event=u'确认邮箱为：%s' % current_user.email, category=u'auth')
        return redirect(current_user.index_url)
    else:
        flash(u'确认链接无效或者已经过期', category='error')
        return redirect(url_for('auth.unconfirmed'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, u'确认您的邮箱账户', 'auth/mail/confirm', user=current_user._get_current_object(), token=token)
    flash(u'一封新的确认邮件已经发送至您的邮箱', category='info')
    add_feed(user=current_user._get_current_object(), event=u'请求重发邮箱确认邮件至：%s' % current_user.email, category=u'auth')
    return redirect(url_for('auth.unconfirmed'))


@auth.route('/password/change', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash(u'修改密码成功', category='success')
            add_feed(user=current_user._get_current_object(), event=u'修改密码', category=u'auth')
            return redirect(current_user.index_url)
        else:
            flash(u'密码有误', category='error')
            return redirect(url_for('auth.change_password'))
    return render_template("auth/change_password.html", form=form)


@auth.route('/password/reset', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        flash(u'您已经登录', category='info')
        return redirect(request.args.get('next') or current_user.index_url)
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None:
            token = user.generate_reset_token()
            send_email(user.email, u'重置您的密码', 'auth/mail/reset_password', user=user, token=token, next=request.args.get('next'))
            flash(u'一封用于重置密码的邮件已经发送至您的邮箱', category='info')
            add_feed(user=user, event=u'请求重置密码', category=u'auth')
            return redirect(url_for('auth.reset_password_request'))
    return render_template('auth/reset_password_request.html', form=form)


@auth.route('/password/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        flash(u'您已经登录', category='info')
        return redirect(current_user.index_url)
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is None:
            flash(u'用户邮箱错误', category='error')
            return redirect(url_for('auth.reset_password_request'))
        if user.reset_password(token, form.password.data):
            flash(u'重置密码成功', category='success')
            add_feed(user=user, event=u'重置密码', category=u'auth')
            return redirect(url_for('auth.login'))
        else:
            flash(u'重置密码失败', category='error')
            return redirect(url_for('auth.reset_password_request'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/email/change', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data.lower()
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, u'确认您的邮箱账户', 'auth/mail/change_email', user=current_user._get_current_object(), token=token)
            flash(u'一封确认邮件已经发送至您的邮箱', category='info')
            add_feed(user=current_user._get_current_object(), event=u'请求修改邮箱为：%s' % new_email, category=u'auth')
            return redirect(url_for('auth.change_email_request'))
        else:
            flash(u'无效的用户名或密码', category='error')
            return redirect(url_for('auth.change_email_request'))
    return render_template("auth/change_email.html", form=form)


@auth.route('/email/change/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash(u'修改邮箱成功', category='success')
        add_feed(user=current_user._get_current_object(), event=u'修改邮箱为：%s' % current_user.email, category=u'auth')
    else:
        flash(u'请求无效', category='error')
    return redirect(current_user.index_url)