# -*- coding: utf-8 -*-

from datetime import date
from flask import render_template, redirect, url_for, flash, current_app, make_response, request
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import manage
from .forms import NewScheduleForm
from .. import db
from ..email import send_email
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
    show_today = True
    show_future = False
    show_history = False
    if current_user.is_authenticated:
        show_today = bool(request.cookies.get('show_today', '1'))
        show_future = bool(request.cookies.get('show_future', ''))
        show_history = bool(request.cookies.get('show_history', ''))
    if show_today:
        query = Booking.query\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .filter(Schedule.date == date.today())\
            .order_by(Schedule.period_id.asc())\
            .order_by(Booking.timestamp.desc())
    if show_history:
        query = Booking.query\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .filter(Schedule.date < date.today())\
            .order_by(Schedule.date.desc())\
            .order_by(Schedule.period_id.asc())\
            .order_by(Booking.timestamp.desc())
    if show_future:
        query = Booking.query\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .filter(Schedule.date > date.today())\
            .order_by(Schedule.date.asc())\
            .order_by(Schedule.period_id.asc())\
            .order_by(Booking.timestamp.desc())
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    bookings = pagination.items
    return render_template('manage/booking.html', bookings=bookings, show_today=show_today, show_future=show_future, show_history=show_history, pagination=pagination)


@manage.route('/booking/today')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def today_booking():
    resp = make_response(redirect(url_for('manage.booking')))
    resp.set_cookie('show_today', '1', max_age=30*24*60*60)
    resp.set_cookie('show_future', '', max_age=30*24*60*60)
    resp.set_cookie('show_history', '', max_age=30*24*60*60)
    return resp


@manage.route('/booking/future')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def future_booking():
    resp = make_response(redirect(url_for('manage.booking')))
    resp.set_cookie('show_today', '', max_age=30*24*60*60)
    resp.set_cookie('show_future', '1', max_age=30*24*60*60)
    resp.set_cookie('show_history', '', max_age=30*24*60*60)
    return resp


@manage.route('/booking/history')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def history_booking():
    resp = make_response(redirect(url_for('manage.booking')))
    resp.set_cookie('show_today', '', max_age=30*24*60*60)
    resp.set_cookie('show_future', '', max_age=30*24*60*60)
    resp.set_cookie('show_history', '1', max_age=30*24*60*60)
    return resp


@manage.route('/booking/set-state-valid/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def set_booking_state_valid(user_id, schedule_id):
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    booking.set_state(u'预约')
    db.session.commit()
    return redirect(url_for('manage.booking', page=request.args.get('page')))


@manage.route('/booking/set-state-wait/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def set_booking_state_wait(user_id, schedule_id):
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    booking.set_state(u'排队')
    db.session.commit()
    return redirect(url_for('manage.booking', page=request.args.get('page')))


@manage.route('/booking/set-state-invalid/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def set_booking_state_invalid(user_id, schedule_id):
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    booking.set_state(u'失效')
    db.session.commit()
    return redirect(url_for('manage.booking', page=request.args.get('page')))


@manage.route('/booking/set-state-kept/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def set_booking_state_kept(user_id, schedule_id):
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    booking.set_state(u'赴约')
    db.session.commit()
    return redirect(url_for('manage.booking', page=request.args.get('page')))


@manage.route('/booking/set-state-late/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def set_booking_state_late(user_id, schedule_id):
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    booking.set_state(u'迟到')
    db.session.commit()
    return redirect(url_for('manage.booking', page=request.args.get('page')))


@manage.route('/booking/set-state-missed/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def set_booking_state_missed(user_id, schedule_id):
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    booking.set_state(u'爽约')
    db.session.commit()
    return redirect(url_for('manage.booking', page=request.args.get('page')))


@manage.route('/booking/set-state-canceled/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def set_booking_state_canceled(user_id, schedule_id):
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    candidate = booking.set_state(u'取消')
    db.session.commit()
    if candidate:
        send_email(candidate.email, u'您已成功预约%s课程' % booking.schedule.period.alias, 'book/mail/booking', user=candidate, schedule=booking.schedule)
    return redirect(url_for('manage.booking', page=request.args.get('page')))


@manage.route('/schedule', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_SCHEDULE)
def schedule():
    form = NewScheduleForm()
    if form.validate_on_submit():
        day = date(int(form.date.data[:4]), int(form.date.data[5:7]), int(form.date.data[8:]))
        for period_id in form.period.data:
            schedule = Schedule.query.filter_by(date=day, period_id=period_id).first()
            if schedule:
                flash(u'该时段已存在：%s，%s时段：%s - %s' % (schedule.date, schedule.period.type.name, schedule.period.start_time, schedule.period.end_time))
            else:
                schedule = Schedule(date=day, period_id=period_id, quota=form.quota.data, available=form.publish_now.data)
                db.session.add(schedule)
                db.session.commit()
                flash(u'添加时段：%s，%s时段：%s - %s' % (schedule.date, schedule.period.type.name, schedule.period.start_time, schedule.period.end_time))
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


@manage.route('/schedule/up-to-date')
@login_required
@permission_required(Permission.MANAGE_SCHEDULE)
def up_to_date_schedule():
    resp = make_response(redirect(url_for('manage.schedule')))
    resp.set_cookie('show_out_of_date', '', max_age=30*24*60*60)
    return resp


@manage.route('/schedule/out-of-date')
@login_required
@permission_required(Permission.MANAGE_SCHEDULE)
def out_of_date_schedule():
    resp = make_response(redirect(url_for('manage.schedule')))
    resp.set_cookie('show_out_of_date', '1', max_age=30*24*60*60)
    return resp


@manage.route('/schedule/publish/<int:id>')
@login_required
@permission_required(Permission.MANAGE_SCHEDULE)
def publish_schedule(id):
    schedule = Schedule.query.filter_by(id=id).first()
    if schedule is None:
        flash(u'该预约时段不存在')
        return redirect(url_for('manage.schedule', page=request.args.get('page')))
    if schedule.out_of_date:
        flash(u'所选时段已经过期')
        return redirect(url_for('manage.schedule', page=request.args.get('page')))
    if schedule.available:
        flash(u'所选时段已经发布')
        return redirect(url_for('manage.schedule', page=request.args.get('page')))
    schedule.publish()
    flash(u'发布成功！')
    return redirect(url_for('manage.schedule', page=request.args.get('page')))


@manage.route('/schedule/retract/<int:id>')
@login_required
@permission_required(Permission.MANAGE_SCHEDULE)
def retract_schedule(id):
    schedule = Schedule.query.filter_by(id=id).first()
    if schedule is None:
        flash(u'该预约时段不存在')
        return redirect(url_for('manage.schedule', page=request.args.get('page')))
    if schedule.out_of_date:
        flash(u'所选时段已经过期')
        return redirect(url_for('manage.schedule', page=request.args.get('page')))
    if not schedule.available:
        flash(u'所选时段尚未发布')
        return redirect(url_for('manage.schedule', page=request.args.get('page')))
    schedule.retract()
    flash(u'撤销成功！')
    return redirect(url_for('manage.schedule', page=request.args.get('page')))


@manage.route('/schedule/increase-quota/<int:id>')
@login_required
@permission_required(Permission.MANAGE_SCHEDULE)
def increase_schedule_quota(id):
    schedule = Schedule.query.filter_by(id=id).first()
    if schedule is None:
        flash(u'该预约时段不存在')
        return redirect(url_for('manage.schedule', page=request.args.get('page')))
    if schedule.out_of_date:
        flash(u'所选时段已经过期')
        return redirect(url_for('manage.schedule', page=request.args.get('page')))
    candidate = schedule.increase_quota()
    if candidate:
        send_email(candidate.email, u'您已成功预约%s课程' % schedule.period.alias, 'book/mail/booking', user=candidate, schedule=schedule)
    flash(u'所选时段名额+1')
    return redirect(url_for('manage.schedule', page=request.args.get('page')))


@manage.route('/schedule/decrease-quota/<int:id>')
@login_required
@permission_required(Permission.MANAGE_SCHEDULE)
def decrease_schedule_quota(id):
    schedule = Schedule.query.filter_by(id=id).first()
    if schedule is None:
        flash(u'该预约时段不存在')
        return redirect(url_for('manage.schedule', page=request.args.get('page')))
    if schedule.out_of_date:
        flash(u'所选时段已经过期')
        return redirect(url_for('manage.schedule', page=request.args.get('page')))
    if schedule.quota == 0:
        flash(u'所选时段名额已经为0')
        return redirect(url_for('manage.schedule', page=request.args.get('page')))
    schedule.decrease_quota()
    flash(u'所选时段名额-1')
    return redirect(url_for('manage.schedule', page=request.args.get('page')))