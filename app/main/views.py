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
    if user.id != current_user.id and not current_user.can(u'管理'):
        abort(403)
    show_profile_progress = True
    show_profile_bookings = False
    if current_user.is_authenticated:
        show_profile_progress = bool(request.cookies.get('show_profile_progress', '1'))
        show_profile_bookings = bool(request.cookies.get('show_profile_bookings', ''))
    # progress
    if show_profile_progress:
        # if user.can_access_advanced_vb:
        #     vb_lessons = Lesson.query\
        #         .join(CourseType, CourseType.id == Lesson.type_id)\
        #         .filter(CourseType.name == u'VB')\
        #         .filter(Lesson.order >= 0)\
        #         .all()
        # else:
        #     vb_lessons = Lesson.query\
        #         .join(CourseType, CourseType.id == Lesson.type_id)\
        #         .filter(CourseType.name == u'VB')\
        #         .filter(Lesson.advanced == False)\
        #         .filter(Lesson.order >= 0)\
        #         .all()
        # if user.can(u'预约Y-GRE课程'):
        #     y_gre_lessons = Lesson.query\
        #         .join(CourseType, CourseType.id == Lesson.type_id)\
        #         .filter(CourseType.name == u'Y-GRE')\
        #         .filter(Lesson.order >= 0)\
        #         .all()
        # else:
        #     y_gre_lessons = []
        bookings = []
        pagination = None
    # bookings
    if show_profile_bookings:
        # vb_lessons = []
        # y_gre_lessons = []
        page = request.args.get('page', 1, type=int)
        pagination = Booking.query\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .filter(Booking.user_id == user.id)\
            .order_by(Schedule.date.asc())\
            .order_by(Schedule.period_id.asc())\
            .paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
        bookings = pagination.items
    # announcements
    announcements = []
    if user.id == current_user.id:
        announcements = get_announcements(type_name=u'用户主页通知', user=current_user._get_current_object())
    return render_template('profile.html',
        user=user,
        show_profile_progress=show_profile_progress,
        show_profile_bookings=show_profile_bookings,
        # vb_lessons=vb_lessons,
        # y_gre_lessons=y_gre_lessons,
        bookings=bookings,
        pagination=pagination,
        announcements=announcements
    )


@main.route('/profile/<int:id>/progress')
@login_required
def profile_progress(id):
    resp = make_response(redirect(url_for('main.profile', id=id)))
    resp.set_cookie('show_profile_progress', '1', max_age=30*24*60*60)
    resp.set_cookie('show_profile_bookings', '', max_age=30*24*60*60)
    return resp


@main.route('/profile/<int:id>/booking')
@login_required
def profile_bookings(id):
    resp = make_response(redirect(url_for('main.profile', id=id)))
    resp.set_cookie('show_profile_progress', '', max_age=30*24*60*60)
    resp.set_cookie('show_profile_bookings', '1', max_age=30*24*60*60)
    return resp


@main.route('/profile/<int:id>/progress/vb')
@login_required
def profile_progress_vb(id):
    user = User.query.get_or_404(id)
    if not user.created or user.deleted:
        abort(404)
    if user.id != current_user.id and not current_user.can(u'管理'):
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
        'lessons': [lesson.to_json(user=user) for lesson in lessons]
    })


@main.route('/profile/<int:id>/progress/y-gre')
@login_required
def profile_progress_y_gre(id):
    user = User.query.get_or_404(id)
    if not user.created or user.deleted:
        abort(404)
    if user.id != current_user.id and not current_user.can(u'管理'):
        abort(403)
    lessons = Lesson.query\
        .join(CourseType, CourseType.id == Lesson.type_id)\
        .filter(CourseType.name == u'Y-GRE')\
        .filter(Lesson.order >= 0)\
        .all()
    return jsonify({
        'last_punch': user.last_y_gre_punch_json,
        'progress': user.y_gre_progress_json,
        'lessons': [lesson.to_json(user=user) for lesson in lessons]
    })


@main.route('/profile/<int:user_id>/progress/section/<int:section_id>')
@login_required
def profile_progress_section(user_id, section_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    if user.id != current_user.id and not current_user.can(u'管理'):
        abort(403)
    section = Section.query.get_or_404(section_id)
    progress_json = {
        'section': section.to_json(),
        'status': 'undone',
        'element_id': request.args.get('element_id'),
    }
    punch = Punch.query.filter_by(user_id=user.id, section_id=section_id).first()
    if punch is not None:
        progress_json['status'] = 'done'
        if section_id == user.last_punch.section_id:
            progress_json['status'] = 'ongoing'
        progress_json['punch'] = punch.to_json()
    return jsonify(progress_json)


@main.route('/profile/<int:user_id>/progress/assignment/<int:assignment_id>')
@login_required
def profile_progress_assignment(user_id, assignment_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    if user.id != current_user.id and not current_user.can(u'管理'):
        abort(403)
    assignment = Assignment.query.get_or_404(assignment_id)
    progress_json = {
        'assignment': assignment.to_json(),
        'submitted': False,
        'element_id': request.args.get('element_id'),
    }
    assignment_score = user.submitted(assignment=assignment)
    if assignment_score is not None:
        progress_json['submitted'] = True
        progress_json['score'] = assignment_score.to_json()
    return jsonify(progress_json)


@main.route('/profile/<int:user_id>/progress/test/<int:test_id>')
@login_required
def profile_progress_test(user_id, test_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    if user.id != current_user.id and not current_user.can(u'管理'):
        abort(403)
    test = Test.query.get_or_404(test_id)
    progress_json = {
        'test': test.to_json(),
        'taken': False,
        'element_id': request.args.get('element_id'),
    }
    if test.lesson.type.name == u'VB':
        test_score = user.taken_vb(test=test)
    elif test.lesson.type.name == u'Y-GRE':
        test_score = user.taken_y_gre(test=test)
    if test_score is not None:
        progress_json['taken'] = True
        progress_json['score'] = test_score.to_json()
    return jsonify(progress_json)