# -*- coding: utf-8 -*-

from flask import current_app, render_template
from flask_mail import Message
from .tasks import send_async_email, send_async_emails


def msg_to_dict(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(
        subject=app.config['YSYS_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
        sender=app.config['YSYS_MAIL_SENDER'],
        recipients=[to]
    )
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    return msg.__dict__


def send_email(to, subject, template, **kwargs):
    send_async_email.delay(msg_to_dict(to, subject, template, **kwargs))


def send_emails(users, subject, template, **kwargs):
    send_async_emails.delay([msg_to_dict(to=user.email, subject=subject, template=template, **kwargs) for user in users])