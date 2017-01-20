# -*- coding: utf-8 -*-

from flask import Blueprint

main = Blueprint('main', __name__)

from . import views, errors
from ..models import Version


@main.app_context_processor
def inject_versions():
    return dict(Version=Version)