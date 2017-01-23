# -*- coding: utf-8 -*-

from flask import current_app, render_template
from flask_mail import Message
from . import mail
from .decorators import async


@async
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(
        app.config['YSYS_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
        sender=app.config['YSYS_MAIL_SENDER'],
        recipients=[to]
    )
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    send_async_email(app, msg)


def send_emails(users, subject, template, **kwargs):
    for user in users:
        app = current_app._get_current_object()
        msg = Message(
            app.config['YSYS_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
            sender=app.config['YSYS_MAIL_SENDER'],
            recipients=[user.email]
        )
        msg.body = render_template(template + '.txt', **kwargs)
        msg.html = render_template(template + '.html', **kwargs)
        send_async_email(app, msg)
