# -*- coding: utf-8 -*-

from datetime import date
from flask import render_template, redirect, url_for, flash, current_app, make_response, request
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
    page = request.args.get('page', 1, type=int)
    query = Schedule.query\
        .join(Period, Period.id == Schedule.period_id)\
        .join(CourseType, CourseType.id == Period.type_id)\
        .filter(CourseType.name == u'VB')\
        .filter(Schedule.available == True)\
        .order_by(Schedule.date.asc())\
        .order_by(Period.name.asc())
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    schedules = pagination.items
    return render_template('book/vb.html', schedules=schedules, pagination=pagination)


@book.route('/vb/book/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_VB)
def book_vb(schedule_id):
    schedule = Schedule.query.filter_by(id=schedule_id).first()
    if schedule is None:
        flash(u'无效的预约时段')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if not schedule.available:
        flash(u'所选时段尚未开放')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if schedule.out_of_date or schedule.today:
        flash(u'所选时段已不能预约')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if current_user.booked(schedule):
        flash(u'您已经预约过该时段，请不要重复预约')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if current_user.booking_y_gre_same_day(schedule):
        flash(u'您当天已经预约过Y-GRE课程，不要太贪心哦~')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    same_day_bookings = current_user.booking_vb_same_day(schedule)
    if same_day_bookings >= 2 and not current_user.can(Permission.BOOK_ANY):
        flash(u'您当天已经预约过%d节VB课程，不要太贪心哦~' % same_day_bookings)
        return redirect(url_for('book.vb', page=request.args.get('page')))
    elif same_day_bookings >= 1 and not current_user.can(Permission.BOOK_VB_2):
        flash(u'您当天已经预约过VB课程，不要太贪心哦~')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    current_user.book(schedule, u'预约')
    flash(u'预约成功！')
    return redirect(url_for('book.vb', page=request.args.get('page')))


@book.route('/vb/wait/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_VB)
def wait_vb(schedule_id):
    schedule = Schedule.query.filter_by(id=schedule_id).first()
    if schedule is None:
        flash(u'无效的预约时段')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if not schedule.available:
        flash(u'所选时段尚未开放')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if schedule.out_of_date or schedule.today:
        flash(u'所选时段已不能预约')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if current_user.booked(schedule):
        flash(u'您已经预约过该时段，请不要重复预约')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if current_user.booking_y_gre_same_day(schedule):
        flash(u'您当天已经预约过Y-GRE课程，不要太贪心哦~')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    same_day_bookings = current_user.booking_vb_same_day(schedule)
    if same_day_bookings >= 2 and not current_user.can(Permission.BOOK_ANY):
        flash(u'您当天已经预约过%d节VB课程，不要太贪心哦~' % same_day_bookings)
        return redirect(url_for('book.vb', page=request.args.get('page')))
    elif same_day_bookings >= 1 and not current_user.can(Permission.BOOK_VB_2):
        flash(u'您当天已经预约过VB课程，不要太贪心哦~')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    current_user.book(schedule, u'排队')
    flash(u'已将您加入候选名单')
    return redirect(url_for('book.vb', page=request.args.get('page')))


@book.route('/vb/unbook/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_VB)
def unbook_vb(schedule_id):
    schedule = Schedule.query.filter_by(id=schedule_id).first()
    if schedule is None:
        flash(u'无效的预约时段')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if not schedule.available:
        flash(u'所选时段尚未开放')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if schedule.out_of_date or schedule.today:
        flash(u'所选时段已不能预约')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if not current_user.booked(schedule):
        flash(u'您目前尚未预约该时段')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    candidate = current_user.unbook(schedule)
    if candidate:
        send_email(candidate.email, u'您已成功预约%s课程' % schedule.period.alias, 'book/mail/booking', user=candidate, schedule=schedule)
    flash(u'取消成功！')
    return redirect(url_for('book.vb', page=request.args.get('page')))


@book.route('/y-gre')
@login_required
@permission_required(Permission.BOOK_Y_GRE)
def y_gre():
    page = request.args.get('page', 1, type=int)
    query = Schedule.query\
        .join(Period, Period.id == Schedule.period_id)\
        .join(CourseType, CourseType.id == Period.type_id)\
        .filter(CourseType.name == u'Y-GRE')\
        .filter(Schedule.available == True)\
        .filter(Schedule.date >= date.today())\
        .order_by(Schedule.date.asc())\
        .order_by(Period.name.asc())
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    schedules = pagination.items
    return render_template('book/y_gre.html', schedules=schedules, pagination=pagination)


@book.route('/y-gre/book/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_Y_GRE)
def book_y_gre(schedule_id):
    schedule = Schedule.query.filter_by(id=schedule_id).first()
    if schedule is None:
        flash(u'无效的预约时段')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if not schedule.available:
        flash(u'所选时段尚未开放')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if schedule.out_of_date or schedule.today:
        flash(u'所选时段已不能预约')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if current_user.booked(schedule):
        flash(u'您已经预约过该时段，请不要重复预约')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if current_user.booking_vb_same_day(schedule):
        flash(u'您当天已经预约过VB课程，不要太贪心哦~')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    same_day_bookings = current_user.booking_y_gre_same_day(schedule)
    if same_day_bookings >= 1 and not current_user.can(Permission.BOOK_ANY):
        flash(u'您当天已经预约过Y-GRE课程，不要太贪心哦~' % same_day_bookings)
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    current_user.book(schedule, u'预约')
    flash(u'预约成功！')
    return redirect(url_for('book.y_gre', page=request.args.get('page')))


@book.route('/y-gre/wait/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_Y_GRE)
def wait_y_gre(schedule_id):
    schedule = Schedule.query.filter_by(id=schedule_id).first()
    if schedule is None:
        flash(u'无效的预约时段')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if not schedule.available:
        flash(u'所选时段尚未开放')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if schedule.out_of_date or schedule.today:
        flash(u'所选时段已不能预约')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if current_user.booked(schedule):
        flash(u'您已经预约过该时段，请不要重复预约')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if current_user.booking_vb_same_day(schedule):
        flash(u'您当天已经预约过VB课程，不要太贪心哦~')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    same_day_bookings = current_user.booking_y_gre_same_day(schedule)
    if same_day_bookings >= 1 and not current_user.can(Permission.BOOK_ANY):
        flash(u'您当天已经预约过Y-GRE课程，不要太贪心哦~' % same_day_bookings)
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    current_user.book(schedule, u'排队')
    flash(u'已将您加入候选名单')
    return redirect(url_for('book.y_gre', page=request.args.get('page')))


@book.route('/y-gre/unbook/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_Y_GRE)
def unbook_y_gre(schedule_id):
    schedule = Schedule.query.filter_by(id=schedule_id).first()
    if schedule is None:
        flash(u'无效的预约时段')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if not schedule.available:
        flash(u'所选时段尚未开放')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if schedule.out_of_date or schedule.today:
        flash(u'所选时段已不能预约')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if not current_user.booked(schedule):
        flash(u'您目前尚未预约该时段')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    candidate = current_user.unbook(schedule)
    if candidate:
        send_email(candidate.email, u'您已成功预约%s课程' % schedule.period.alias, 'book/mail/booking', user=candidate, schedule=schedule)
    flash(u'取消成功！')
    return redirect(url_for('book.y_gre', page=request.args.get('page')))


