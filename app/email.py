# -*- coding: utf-8 -*-

from flask import current_app, render_template
from flask_mail import Message
from . import mail, celery


@celery.task
def send_async_email(mag_dict):
    msg = Message()
    msg.__dict__.update(mag_dict)
    mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(
        subject=app.config['YSYS_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
        sender=app.config['YSYS_MAIL_SENDER'],
        recipients=[to]
    )
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    send_async_email.delay(msg.__dict__)


def send_emails(users, subject, template, **kwargs):
    for user in users:
        send_email(to=user.email, subject=subject, template=template, **kwargs)
