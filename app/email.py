# -*- coding: utf-8 -*-

from flask import current_app, render_template
from flask_mail import Message
from . import mail, celery


@celery.task
def send_async_email(msg_dict):
    msg = Message()
    msg.__dict__.update(msg_dict)
    mail.send(msg)


@celery.task
def send_async_emails(msg_dicts):
    with mail.connect() as conn:
        for msg_dict in msg_dicts:
            msg = Message()
            msg.__dict__.update(msg_dict)
            conn.send(msg)


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