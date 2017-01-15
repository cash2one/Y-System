# -*- coding: utf-8 -*-

from datetime import date
from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .. import db
from ..models import User, Schedule, Punch, Booking, Announcement, AnnouncementType
from ..decorators import permission_required


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
    if current_user.is_authenticated:
        if current_user.can(u'管理'):
            return redirect(request.args.get('next') or url_for('manage.summary'))
        return redirect(request.args.get('next') or url_for('main.profile'))
    return render_template('index.html')


@main.route('/profile')
@login_required
def profile():
    announcements = Announcement.query\
        .join(AnnouncementType, AnnouncementType.id == Announcement.type_id)\
        .filter(AnnouncementType.name == u'用户主页通知')\
        .filter(Announcement.show == True)\
        .filter(Announcement.deleted == False)\
        .order_by(Announcement.modified_at.desc())\
        .all()
    for announcement in announcements:
        if not current_user.notified_by(announcement=announcement):
            flash(u'<div class="content" style="text-align: left;"><div class="header">%s</div>%s</div>' % (announcement.title, announcement.body_html), category='announcement')
            announcement.notify(user=current_user._get_current_object())
    punches = current_user.punches.order_by(Punch.timestamp.desc()).limit(10)
    page = request.args.get('page', 1, type=int)
    pagination = Booking.query\
        .join(Schedule, Schedule.id == Booking.schedule_id)\
        .filter(Booking.user_id == current_user.id)\
        .order_by(Schedule.date.desc())\
        .order_by(Schedule.period_id.asc())\
        .paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    bookings = pagination.items
    return render_template('profile.html', user=current_user, punches=punches, bookings=bookings, pagination=pagination, announcements=announcements)


@main.route('/profile/<int:id>')
@login_required
@permission_required(u'管理')
def profile_user(id):
    user = User.query.get_or_404(id)
    if not user.created or user.deleted:
        abort(404)
    punches = user.punches.order_by(Punch.timestamp.desc()).limit(10)
    page = request.args.get('page', 1, type=int)
    pagination = Booking.query\
        .join(Schedule, Schedule.id == Booking.schedule_id)\
        .filter(Booking.user_id == user.id)\
        .order_by(Schedule.date.asc())\
        .order_by(Schedule.period_id.asc())\
        .paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    bookings = pagination.items
    return render_template('profile_user.html', user=user, punches=punches, bookings=bookings, pagination=pagination)
