# -*- coding: utf-8 -*-

from flask import render_template, redirect, url_for, flash, current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import book
from .. import db
from ..email import send_email
from ..models import Permission, Schedule, Period, CourseType, Booking, BookingState
from ..decorators import admin_required, permission_required


@book.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['YSYS_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning('Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n' % (query.statement, query.parameters, query.duration, query.context))
    return response


@book.route('/vb')
@login_required
@permission_required(Permission.BOOK_VB)
def vb():
    schedules = Schedule.query\
        .join(Period, Period.id == Schedule.period_id)\
        .join(CourseType, CourseType.id == Period.type_id)\
        .filter(CourseType.name == u'VB')\
        .filter(Schedule.available == True)\
        .order_by(Schedule.date.asc())\
        .order_by(Period.name.asc())
    return render_template('book/vb.html', schedules=schedules)


@book.route('/book-vb/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_VB)
def book_vb(schedule_id):
    schedule = Schedule.query.filter_by(id=schedule_id).first()
    if schedule is None:
        flash(u'无效的预约时段')
        return redirect(url_for('book.vb'))
    if not schedule.available:
        flash(u'所选时段尚未开放')
        return redirect(url_for('book.vb'))
    if schedule.out_of_date or schedule.today:
        flash(u'所选时段已不能预约')
        return redirect(url_for('book.vb'))
    if current_user.booked(schedule):
        flash(u'您已经预约过该时段，请不要重复预约')
        return redirect(url_for('book.vb'))
    current_user.book(schedule, u'预约')
    flash(u'预约成功！')
    return redirect(url_for('book.vb'))


@book.route('/wait-vb/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_VB)
def wait_vb(schedule_id):
    schedule = Schedule.query.filter_by(id=schedule_id).first()
    if schedule is None:
        flash(u'无效的预约时段')
        return redirect(url_for('book.vb'))
    if not schedule.available:
        flash(u'所选时段尚未开放')
        return redirect(url_for('book.vb'))
    if schedule.out_of_date or schedule.today:
        flash(u'所选时段已不能预约')
        return redirect(url_for('book.vb'))
    if current_user.booked(schedule):
        flash(u'您已经预约过该时段，请不要重复预约')
        return redirect(url_for('book.vb'))
    current_user.book(schedule, u'排队')
    flash(u'已将您加入候选名单')
    return redirect(url_for('book.vb'))


@book.route('/unbook-vb/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_VB)
def unbook_vb(schedule_id):
    schedule = Schedule.query.filter_by(id=schedule_id).first()
    if schedule is None:
        flash(u'无效的预约时段')
        return redirect(url_for('book.vb'))
    if not schedule.available:
        flash(u'所选时段尚未开放')
        return redirect(url_for('book.vb'))
    if schedule.out_of_date or schedule.today:
        flash(u'所选时段已不能预约')
        return redirect(url_for('book.vb'))
    if not current_user.booked(schedule):
        flash(u'您目前尚未预约该时段')
        return redirect(url_for('book.vb'))
    candidate = current_user.unbook(schedule)
    if candidate:
        send_email(candidate.email, u'您已成功预约VB课程', 'book/mail/booking', user=candidate, schedule=schedule)
    flash(u'取消成功！')
    return redirect(url_for('book.vb'))


@book.route('/y-gre')
@login_required
@permission_required(Permission.BOOK_Y_GRE)
def y_gre():
    schedules = Schedule.query\
        .join(Period, Period.id == Schedule.period_id)\
        .join(CourseType, CourseType.id == Period.type_id)\
        .filter(CourseType.name == u'Y-GRE')\
        .filter(Schedule.available == True)\
        .order_by(Schedule.date.asc())\
        .order_by(Period.name.asc())
    return render_template('book/y_gre.html', schedules=schedules)


@book.route('/book-y-gre/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_Y_GRE)
def book_y_gre(schedule_id):
    schedule = Schedule.query.filter_by(id=schedule_id).first()
    if schedule is None:
        flash(u'无效的预约时段')
        return redirect(url_for('book.y_gre'))
    if not schedule.available:
        flash(u'所选时段尚未开放')
        return redirect(url_for('book.y_gre'))
    if schedule.out_of_date or schedule.today:
        flash(u'所选时段已不能预约')
        return redirect(url_for('book.y_gre'))
    if current_user.booked(schedule):
        flash(u'您已经预约过该时段，请不要重复预约')
        return redirect(url_for('book.y_gre'))
    current_user.book(schedule, u'预约')
    flash(u'预约成功！')
    return redirect(url_for('book.y_gre'))


@book.route('/wait-y-gre/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_Y_GRE)
def wait_y_gre(schedule_id):
    schedule = Schedule.query.filter_by(id=schedule_id).first()
    if schedule is None:
        flash(u'无效的预约时段')
        return redirect(url_for('book.y_gre'))
    if not schedule.available:
        flash(u'所选时段尚未开放')
        return redirect(url_for('book.y_gre'))
    if schedule.out_of_date or schedule.today:
        flash(u'所选时段已不能预约')
        return redirect(url_for('book.y_gre'))
    if current_user.booked(schedule):
        flash(u'您已经预约过该时段，请不要重复预约')
        return redirect(url_for('book.y_gre'))
    current_user.book(schedule, u'排队')
    flash(u'已将您加入候选名单')
    return redirect(url_for('book.y_gre'))


@book.route('/unbook-y-gre/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_Y_GRE)
def unbook_y_gre(schedule_id):
    schedule = Schedule.query.filter_by(id=schedule_id).first()
    if schedule is None:
        flash(u'无效的预约时段')
        return redirect(url_for('book.y_gre'))
    if not schedule.available:
        flash(u'所选时段尚未开放')
        return redirect(url_for('book.y_gre'))
    if schedule.out_of_date or schedule.today:
        flash(u'所选时段已不能预约')
        return redirect(url_for('book.y_gre'))
    if not current_user.booked(schedule):
        flash(u'您目前尚未预约该时段')
        return redirect(url_for('book.y_gre'))
    candidate = current_user.unbook(schedule)
    if candidate:
        send_email(candidate.email, u'您已成功预约Y-GRE课程', 'book/mail/booking', user=candidate, schedule=schedule)
    flash(u'取消成功！')
    return redirect(url_for('book.y_gre'))


