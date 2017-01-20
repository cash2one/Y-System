# -*- coding: utf-8 -*-

from flask import Blueprint, current_app

main = Blueprint('main', __name__)

from . import views, errors


@main.app_context_processor
def inject_version():
    return dict(Version=current_app.config['VERSION'])