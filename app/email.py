# -*- coding: utf-8 -*-

from flask import current_app, render_template
from flask_mail import Message
from .tasks import send_async_email, send_async_emails


def msg_to_dict(recipient, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(
        subject=app.config['YSYS_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
        sender=app.config['YSYS_MAIL_SENDER'],
        recipients=[recipient]
    )
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    return msg.__dict__


def send_email(recipient, subject, template, **kwargs):
    send_async_email.delay(msg_to_dict(recipient, subject, template, **kwargs))


def send_emails(recipients, subject, template, **kwargs):
    send_async_emails.delay([msg_to_dict(recipient=recipient, subject=subject, template=template, **kwargs) for recipient in recipients])