# -*- coding: utf-8 -*-

from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .forms import LoginForm, ActivationForm, ChangePasswordForm, ResetPasswordRequestForm, ResetPasswordForm, ChangeEmailForm
from .. import db
from ..email import send_email
from ..models import User, Role, Announcement, AnnouncementType


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
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
        if current_user.can(u'管理'):
            return redirect(url_for('manage.summary'))
        return redirect(url_for('main.profile'))
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash(u'您已经登录', 'info')
        if current_user.can(u'管理'):
            return redirect(request.args.get('next') or url_for('manage.summary'))
        return redirect(request.args.get('next') or url_for('main.profile'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, deleted=False).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            # flash(u'欢迎登录云英语教育服务支撑系统！', category='info')
            announcement = Announcement.query\
                .join(AnnouncementType, AnnouncementType.id == Announcement.type_id)\
                .filter(AnnouncementType.name == u'登录通知')\
                .filter(Announcement.show == True)\
                .filter(Announcement.deleted == False)\
                .first()
            if announcement is not None:
                flash(u'[%s]%s' % (announcement.title, announcement.body), category='announcement')
            if user.can(u'管理'):
                return redirect(request.args.get('next') or url_for('manage.summary'))
            return redirect(request.args.get('next') or url_for('main.profile'))
        flash(u'无效的用户名或密码', category='error')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/activate', methods=['GET', 'POST'])
def activate():
    if current_user.is_authenticated:
        flash(u'您已经登录', 'info')
        if current_user.can(u'管理'):
            return redirect(request.args.get('next') or url_for('manage.summary'))
        return redirect(request.args.get('next') or url_for('main.profile'))
    form = ActivationForm()
    if form.validate_on_submit():
        new_users = User.query.filter_by(name=form.name.data, activated=False, deleted=False).all()
        for new_user in new_users:
            if new_user.verify_password(form.activation_code.data):
                new_user.activate()
                token = new_user.generate_confirmation_token()
                send_email(new_user.email, u'确认您的邮箱账户', 'auth/mail/confirm', user=new_user, token=token)
                flash(u'激活成功，请登录！', category='success')
                flash(u'一封确认邮件已经发送至您的邮箱', category='info')
                for user in User.query.all():
                    if user.can(u'管理用户'):
                        send_email(user.email, u'新用户：%s（%s）' % (new_user.name, new_user.email), 'auth/mail/new_user', user=new_user)
                return redirect(url_for('auth.login'))
        flash(u'激活信息有误，或账户已处于激活状态', category='error')
    return render_template('auth/activate.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        if current_user.can(u'管理'):
            return redirect(url_for('manage.summary'))
        return redirect(url_for('main.profile'))
    if current_user.confirm(token):
        flash(u'您的邮箱账户确认成功！', category='success')
    else:
        flash(u'确认链接无效或者已经过期', category='error')
        return redirect(url_for('auth.unconfirmed'))
    if current_user.can(u'管理'):
        return redirect(url_for('manage.summary'))
    return redirect(url_for('main.profile'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, u'确认您的邮箱账户', 'auth/mail/confirm', user=current_user, token=token)
    flash(u'一封新的确认邮件已经发送至您的邮箱', category='info')
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
            if current_user.can(u'管理'):
                return redirect(url_for('manage.summary'))
            return redirect(url_for('main.profile'))
        else:
            flash(u'密码有误', category='error')
    return render_template("auth/change_password.html", form=form)


@auth.route('/password/reset', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        flash(u'您已经登录', 'info')
        if current_user.can(u'管理'):
            return redirect(request.args.get('next') or url_for('manage.summary'))
        return redirect(request.args.get('next') or url_for('main.profile'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, u'重置您的密码', 'auth/mail/reset_password', user=user, token=token, next=request.args.get('next'))
        flash(u'一封用于重置密码的邮件已经发送至您的邮箱', category='info')
        return redirect(url_for('auth.reset_password_request'))
    return render_template('auth/reset_password_request.html', form=form)


@auth.route('/password/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        flash(u'您已经登录', 'info')
        if current_user.can(u'管理'):
            return redirect(url_for('manage.summary'))
        return redirect(url_for('main.profile'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash(u'用户邮箱错误', category='error')
            return redirect(url_for('auth.reset_password_request'))
        if user.reset_password(token, form.password.data):
            flash(u'重置密码成功', category='success')
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
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, u'确认您的邮箱账户', 'auth/mail/change_email', user=current_user, token=token)
            flash(u'一封确认邮件已经发送至您的邮箱', category='info')
            return redirect(url_for('auth.change_email_request'))
        else:
            flash(u'无效的用户名或密码', category='error')
    return render_template("auth/change_email.html", form=form)


@auth.route('/email/change/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash(u'修改邮箱成功', category='success')
    else:
        flash(u'请求无效', category='error')
    if current_user.can(u'管理'):
        return redirect(url_for('manage.summary'))
    return redirect(url_for('main.profile'))
