# -*- coding: utf-8 -*-

from datetime import date
from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .. import db
from ..models import Permission, Schedule, Period, CourseType, User, Punch, Booking
from ..decorators import admin_required, permission_required


@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['YSYS_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning('Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n' % (query.statement, query.parameters, query.duration, query.context))
    return response


@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@main.route('/profile')
@login_required
def profile():
    page = request.args.get('page', 1, type=int)
    punches = Punch.query\
        .filter_by(user_id=current_user.id)\
        .order_by(Punch.timestamp.desc())\
        .limit(10)
    query = Booking.query\
        .join(Schedule, Schedule.id == Booking.schedule_id)\
        .filter(Schedule.date > date.today())\
        .filter(Booking.user_id == current_user.id)\
        .order_by(Schedule.date.desc())\
        .order_by(Schedule.period_id.asc())
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    bookings = pagination.items
    return render_template('profile.html', user=current_user, punches=punches, bookings=bookings, pagination=pagination)


@main.route('/profile/<int:user_id>')
@login_required
@permission_required(Permission.MANAGE_USER)
def profile_user(user_id):
    user = User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    punches = Punch.query\
        .filter_by(user_id=user.id)\
        .order_by(Punch.timestamp.desc())\
        .limit(10)
    query = Booking.query\
        .join(Schedule, Schedule.id == Booking.schedule_id)\
        .filter(Schedule.date > date.today())\
        .filter(Booking.user_id == user.id)\
        .order_by(Schedule.date.asc())\
        .order_by(Schedule.period_id.asc())
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    bookings = pagination.items
    return render_template('profile.html', user=user, punches=punches, bookings=bookings, pagination=pagination)
