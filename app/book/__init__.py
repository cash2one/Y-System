# -*- coding: utf-8 -*-

from flask import Blueprint

book = Blueprint('book', __name__)

from . import views
from ..models import Permission


@book.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
