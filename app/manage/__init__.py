# -*- coding: utf-8 -*-

from flask import Blueprint

manage = Blueprint('manage', __name__)

from . import views
from ..models import Permission


@manage.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
