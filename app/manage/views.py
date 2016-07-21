# -*- coding: utf-8 -*-

from flask import render_template, redirect, url_for, flash, current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import manage
from .forms import EditProfileForm, EditProfileAdminForm
from .. import db
from ..models import Permission, Schedule, Period, CourseType
from ..decorators import admin_required, permission_required


@manage.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['YSYS_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning('Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n' % (query.statement, query.parameters, query.duration, query.context))
    return response