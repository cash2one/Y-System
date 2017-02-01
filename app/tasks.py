# -*- coding: utf-8 -*-

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