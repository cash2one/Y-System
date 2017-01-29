# -*- coding: utf-8 -*-

from flask import Blueprint


main = Blueprint('main', __name__)


from . import views, errors
from ..models import Version, Analytics


@main.app_context_processor
def inject_versions():
    return dict(Version=Version)


@main.app_context_processor
def inject_analytics():
    return dict(Analytics=Analytics)