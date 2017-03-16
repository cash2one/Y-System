# -*- coding: utf-8 -*-

from datetime import date
from flask import render_template, redirect, url_for, abort, flash, current_app, make_response, request, jsonify
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .. import db
from ..models import User
from ..models import CourseType, Lesson, Section, Punch
from ..models import Assignment, Test
from ..models import Schedule, Booking
from ..models import Feed
from ..notify import get_announcements
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


@main.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.can(u'管理'):
            return redirect(request.args.get('next') or url_for('manage.summary'))
        return redirect(request.args.get('next') or url_for('main.profile', id=current_user.id))
    return render_template('index.html')


@main.route('/profile/<int:id>')
@login_required
def profile(id):
    user = User.query.get_or_404(id)
    if not user.created or user.deleted:
        abort(404)
    if (user.id != current_user.id and not current_user.can(u'管理')) or (user.is_developer and not current_user.is_developer):
        abort(403)
    show_profile_overview = True
    show_profile_progress = False
    show_profile_bookings = False
    show_profile_archive = False
    if current_user.is_authenticated:
        show_profile_overview = bool(request.cookies.get('show_profile_overview', '1'))
        show_profile_progress = bool(request.cookies.get('show_profile_progress', ''))
        show_profile_bookings = bool(request.cookies.get('show_profile_bookings', ''))
        show_profile_archive = bool(request.cookies.get('show_profile_archive', ''))
    # overview
    if show_profile_overview:
        page = request.args.get('page', 1, type=int)
        pagination = Feed.query\
            .filter(Feed.user_id == user.id)\
            .filter(Feed.category != u'access')\
            .order_by(Feed.timestamp.desc())\
            .paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
        feeds = pagination.items
        bookings = []
    # progress
    if show_profile_progress:
        feeds = []
        bookings = []
        pagination = None
    # bookings
    if show_profile_bookings:
        feeds = []
        page = request.args.get('page', 1, type=int)
        pagination = Booking.query\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .filter(Booking.user_id == user.id)\
            .order_by(Schedule.date.desc())\
            .order_by(Schedule.period_id.asc())\
            .paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
        bookings = pagination.items
    # progress
    if show_profile_archive:
        feeds = []
        bookings = []
        pagination = None
    # announcements
    announcements = []
    if user.id == current_user.id:
        announcements = get_announcements(type_name=u'用户主页通知', user=current_user._get_current_object())
    return render_template('profile.html',
        user=user,
        show_profile_overview=show_profile_overview,
        show_profile_progress=show_profile_progress,
        show_profile_bookings=show_profile_bookings,
        show_profile_archive=show_profile_archive,
        feeds=feeds,
        bookings=bookings,
        pagination=pagination,
        announcements=announcements
    )


@main.route('/profile/<int:id>/overview')
@login_required
def profile_overview(id):
    resp = make_response(redirect(url_for('main.profile', id=id)))
    resp.set_cookie('show_profile_overview', '1', max_age=30*24*60*60)
    resp.set_cookie('show_profile_progress', '', max_age=30*24*60*60)
    resp.set_cookie('show_profile_bookings', '', max_age=30*24*60*60)
    resp.set_cookie('show_profile_archive', '', max_age=30*24*60*60)
    return resp


@main.route('/profile/<int:id>/progress')
@login_required
def profile_progress(id):
    resp = make_response(redirect(url_for('main.profile', id=id)))
    resp.set_cookie('show_profile_overview', '', max_age=30*24*60*60)
    resp.set_cookie('show_profile_progress', '1', max_age=30*24*60*60)
    resp.set_cookie('show_profile_bookings', '', max_age=30*24*60*60)
    resp.set_cookie('show_profile_archive', '', max_age=30*24*60*60)
    return resp


@main.route('/profile/<int:id>/bookings')
@login_required
def profile_bookings(id):
    resp = make_response(redirect(url_for('main.profile', id=id)))
    resp.set_cookie('show_profile_overview', '', max_age=30*24*60*60)
    resp.set_cookie('show_profile_progress', '', max_age=30*24*60*60)
    resp.set_cookie('show_profile_bookings', '1', max_age=30*24*60*60)
    resp.set_cookie('show_profile_archive', '', max_age=30*24*60*60)
    return resp


@main.route('/profile/<int:id>/archive')
@login_required
def profile_archive(id):
    resp = make_response(redirect(url_for('main.profile', id=id)))
    resp.set_cookie('show_profile_overview', '', max_age=30*24*60*60)
    resp.set_cookie('show_profile_progress', '', max_age=30*24*60*60)
    resp.set_cookie('show_profile_bookings', '', max_age=30*24*60*60)
    resp.set_cookie('show_profile_archive', '1', max_age=30*24*60*60)
    return resp


@main.route('/profile/<int:id>/overview/data')
@login_required
def profile_overview_data(id):
    user = User.query.get_or_404(id)
    if not user.created or user.deleted:
        abort(404)
    if (user.id != current_user.id and not current_user.can(u'管理')) or (user.is_developer and not current_user.is_developer):
        abort(403)
    return jsonify({
        'progress': {
            'vb': user.vb_progress_json,
            'y_gre': user.y_gre_progress_json,
        },
        'last_punch': {
            'vb': user.last_vb_punch_json,
            'y_gre': user.last_y_gre_punch_json,
        },
        # 'study_plans': [study_plan.to_json() for study_plan in user.study_plans],
    })


@main.route('/profile/<int:id>/progress/vb')
@login_required
def profile_progress_vb(id):
    user = User.query.get_or_404(id)
    if not user.created or user.deleted:
        abort(404)
    if (user.id != current_user.id and not current_user.can(u'管理')) or (user.is_developer and not current_user.is_developer):
        abort(403)
    if user.can_access_advanced_vb:
        lessons = Lesson.query\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(CourseType.name == u'VB')\
            .filter(Lesson.order >= 0)\
            .all()
    else:
        lessons = Lesson.query\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(CourseType.name == u'VB')\
            .filter(Lesson.advanced == False)\
            .filter(Lesson.order >= 0)\
            .all()
    return jsonify({
        'last_punch': user.last_vb_punch_json,
        'progress': user.vb_progress_json,
        'lessons': [lesson.to_json() for lesson in lessons],
        'punches': [punch.to_json() for punch in user.vb_punches],
        'assignment_scores': [score.to_json() for score in user.vb_assignment_scores],
        'test_scores': [score.to_json() for score in user.vb_test_scores_alias],
    })


@main.route('/profile/<int:id>/progress/y-gre')
@login_required
def profile_progress_y_gre(id):
    user = User.query.get_or_404(id)
    if not user.created or user.deleted:
        abort(404)
    if (user.id != current_user.id and not current_user.can(u'管理')) or (user.is_developer and not current_user.is_developer):
        abort(403)
    lessons = Lesson.query\
        .join(CourseType, CourseType.id == Lesson.type_id)\
        .filter(CourseType.name == u'Y-GRE')\
        .filter(Lesson.order >= 0)\
        .all()
    return jsonify({
        'last_punch': user.last_y_gre_punch_json,
        'progress': user.y_gre_progress_json,
        'lessons': [lesson.to_json() for lesson in lessons],
        'punches': [punch.to_json() for punch in user.y_gre_punches],
        'test_scores': [score.to_json() for score in user.y_gre_test_scores_alias],
    })