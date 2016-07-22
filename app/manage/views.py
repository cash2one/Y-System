# -*- coding: utf-8 -*-

from datetime import date
from flask import render_template, redirect, url_for, flash, current_app, make_response, request
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import manage
from .forms import NewScheduleForm
from .. import db
from ..models import Permission, Booking, Schedule
from ..decorators import admin_required, permission_required


@manage.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['YSYS_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning('Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n' % (query.statement, query.parameters, query.duration, query.context))
    return response


@manage.route('/booking')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def booking():
    page = request.args.get('page', 1, type=int)
    pagination = Booking.query\
        .order_by(Booking.timestamp.desc())\
        .paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    bookings = pagination.items
    return render_template('manage/booking.html', bookings=bookings, pagination=pagination)


@manage.route('/schedule', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_SCHEDULE)
def schedule():
    form = NewScheduleForm()
    if form.validate_on_submit():
        day = date(int(form.date.data[:4]), int(form.date.data[5:7]), int(form.date.data[8:]))
        for period_id in form.period.data:
            s = Schedule.query.filter_by(date=day, period_id=period_id).first()
            if s:
                flash(u'该时段已存在：%s，%s时段：%s - %s' % (s.date, s.period.type.name, s.period.start_time, s.period.end_time))
            else:
                s = Schedule(date=day, period_id=period_id, quota=form.quota.data, available=form.publish_now.data)
                db.session.add(s)
                db.session.commit()
                flash(u'添加时段：%s，%s时段：%s - %s' % (s.date, s.period.type.name, s.period.start_time, s.period.end_time))
        return redirect(url_for('manage.schedule'))
    page = request.args.get('page', 1, type=int)
    show_out_of_date = False
    if current_user.is_authenticated:
        show_out_of_date = bool(request.cookies.get('show_out_of_date', ''))
    if show_out_of_date:
        query = Schedule.query\
            .filter(Schedule.date < date.today())
    else:
        query = Schedule.query\
            .filter(Schedule.date >= date.today())
    pagination = query\
        .order_by(Schedule.date.desc())\
        .order_by(Schedule.period_id.asc())\
        .paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    schedules = pagination.items
    return render_template('manage/schedule.html', form=form, schedules=schedules, show_out_of_date=show_out_of_date, pagination=pagination)


@manage.route('/up-to-date-schedule')
@login_required
@permission_required(Permission.MANAGE_SCHEDULE)
def up_to_date_schedule():
    resp = make_response(redirect(url_for('manage.schedule')))
    resp.set_cookie('show_out_of_date', '', max_age=30*24*60*60)
    return resp


@manage.route('/out-of-date-schedule')
@login_required
@permission_required(Permission.MANAGE_SCHEDULE)
def out_of_date_schedule():
    resp = make_response(redirect(url_for('manage.schedule')))
    resp.set_cookie('show_out_of_date', '1', max_age=30*24*60*60)
    return resp


@manage.route('/publish-schedule/<int:id>')
@login_required
@permission_required(Permission.MANAGE_SCHEDULE)
def publish_schedule(id):
    schedule = Schedule.query.filter_by(id=id).first()
    if schedule is None:
        flash(u'该预约时段不存在')
        return redirect(url_for('manage.schedule'))
    if schedule.out_of_date:
        flash(u'所选时段已经过期')
        return redirect(url_for('manage.schedule'))
    if schedule.available:
        flash(u'所选时段已经发布')
        return redirect(url_for('manage.schedule'))
    schedule.publish()
    flash(u'发布成功！')
    return redirect(url_for('manage.schedule'))


@manage.route('/retract-schedule/<int:id>')
@login_required
@permission_required(Permission.MANAGE_SCHEDULE)
def retract_schedule(id):
    schedule = Schedule.query.filter_by(id=id).first()
    if schedule is None:
        flash(u'该预约时段不存在')
        return redirect(url_for('manage.schedule'))
    if schedule.out_of_date:
        flash(u'所选时段已经过期')
        return redirect(url_for('manage.schedule'))
    if not schedule.available:
        flash(u'所选时段尚未发布')
        return redirect(url_for('manage.schedule'))
    schedule.retract()
    flash(u'撤销成功！')
    return redirect(url_for('manage.schedule'))


@manage.route('/increase-schedule-quota/<int:id>')
@login_required
@permission_required(Permission.MANAGE_SCHEDULE)
def increase_schedule_quota(id):
    schedule = Schedule.query.filter_by(id=id).first()
    if schedule is None:
        flash(u'该预约时段不存在')
        return redirect(url_for('manage.schedule'))
    if schedule.out_of_date:
        flash(u'所选时段已经过期')
        return redirect(url_for('manage.schedule'))
    schedule.increase_quota()
    flash(u'所选时段名额+1')
    return redirect(url_for('manage.schedule'))


@manage.route('/decrease-schedule-quota/<int:id>')
@login_required
@permission_required(Permission.MANAGE_SCHEDULE)
def decrease_schedule_quota(id):
    schedule = Schedule.query.filter_by(id=id).first()
    if schedule is None:
        flash(u'该预约时段不存在')
        return redirect(url_for('manage.schedule'))
    if schedule.out_of_date:
        flash(u'所选时段已经过期')
        return redirect(url_for('manage.schedule'))
    if schedule.quota == 0:
        flash(u'所选时段名额已经为0')
        return redirect(url_for('manage.schedule'))
    schedule.decrease_quota()
    flash(u'所选时段名额-1')
    return redirect(url_for('manage.schedule'))