# -*- coding: utf-8 -*-

from datetime import datetime, date, time
from sqlalchemy import or_
import json
from flask import render_template, redirect, url_for, flash, current_app, make_response, request
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import manage
from .forms import NewScheduleForm, NewPeriodForm, EditPeriodForm, DeletePeriodForm, NewiPadForm, EditiPadForm, DeleteiPadForm, FilteriPadForm, NewActivationForm, EditActivationForm, DeleteActivationForm, EditUserForm, FindUserForm, EditPunchLessonForm, EditPunchSectionForm, EditAuthForm, EditAuthFormAdmin, BookingCodeForm, RentiPadForm, RentalEmailForm, ConfirmiPadForm, iPadSerialForm, PunchLessonForm, PunchSectionForm, ConfirmPunchForm
from .. import db
from ..email import send_email
from ..models import Permission, Role, User, Activation, Booking, BookingState, Schedule, Period, iPad, iPadState, iPadContent, iPadContentJSON, Room, Course, Rental, Lesson, Section, Punch
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
    show_today_booking = True
    show_future_booking = False
    show_history_booking = False
    if current_user.is_authenticated:
        show_today_booking = bool(request.cookies.get('show_today_booking', '1'))
        show_future_booking = bool(request.cookies.get('show_future_booking', ''))
        show_history_booking = bool(request.cookies.get('show_history_booking', ''))
    if show_today_booking:
        query = Booking.query\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .filter(Schedule.date == date.today())\
            .order_by(Schedule.period_id.asc())\
            .order_by(Booking.timestamp.desc())
    if show_history_booking:
        query = Booking.query\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .filter(Schedule.date < date.today())\
            .order_by(Schedule.date.desc())\
            .order_by(Schedule.period_id.asc())\
            .order_by(Booking.timestamp.desc())
    if show_future_booking:
        query = Booking.query\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .filter(Schedule.date > date.today())\
            .order_by(Schedule.date.asc())\
            .order_by(Schedule.period_id.asc())\
            .order_by(Booking.timestamp.desc())
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    bookings = pagination.items
    return render_template('manage/booking.html', bookings=bookings, show_today_booking=show_today_booking, show_future_booking=show_future_booking, show_history_booking=show_history_booking, pagination=pagination)


@manage.route('/booking/today')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def today_booking():
    resp = make_response(redirect(url_for('manage.booking')))
    resp.set_cookie('show_today_booking', '1', max_age=30*24*60*60)
    resp.set_cookie('show_future_booking', '', max_age=30*24*60*60)
    resp.set_cookie('show_history_booking', '', max_age=30*24*60*60)
    return resp


@manage.route('/booking/future')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def future_booking():
    resp = make_response(redirect(url_for('manage.booking')))
    resp.set_cookie('show_today_booking', '', max_age=30*24*60*60)
    resp.set_cookie('show_future_booking', '1', max_age=30*24*60*60)
    resp.set_cookie('show_history_booking', '', max_age=30*24*60*60)
    return resp


@manage.route('/booking/history')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def history_booking():
    resp = make_response(redirect(url_for('manage.booking')))
    resp.set_cookie('show_today_booking', '', max_age=30*24*60*60)
    resp.set_cookie('show_future_booking', '', max_age=30*24*60*60)
    resp.set_cookie('show_history_booking', '1', max_age=30*24*60*60)
    return resp


@manage.route('/booking/set-state-valid/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def set_booking_state_valid(user_id, schedule_id):
    user = User.query.get_or_404(user_id)
    schedule = Schedule.query.get_or_404(schedule_id)
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    if booking.schedule.full:
        flash(u'该时段名额已经约满')
        return redirect(url_for('manage.booking', page=request.args.get('page')))
    booking.set_state(u'预约')
    db.session.commit()
    send_email(user.email, u'您已成功预约%s的%s课程' % (booking.schedule.date, booking.schedule.period.alias), 'book/mail/booking', user=user, schedule=schedule, booking=booking)
    booked_ipads = Booking.query\
        .join(Punch, Punch.user_id == Booking.user_id)\
        .join(BookingState, BookingState.id == Booking.state_id)\
        .filter(Booking.schedule_id == schedule_id)\
        .filter(BookingState.name == u'预约')\
        .filter(Punch.lesson_id == user.last_punch.lesson_id)
    available_ipads = iPad.query\
        .join(iPadContent, iPadContent.ipad_id == iPad.id)\
        .join(iPadState, iPadState.id == iPad.state_id)\
        .filter(iPadContent.lesson_id == user.last_punch.lesson_id)\
        .filter(iPadState.name != u'退役')
    if booked_ipads.count() >= available_ipads.count():
        for manager in User.query.all():
            if manager.can(Permission.MANAGE_IPAD):
                send_email(manager.email, u'含有课程“%s”的iPad资源紧张' % user.last_punch.lesson.name, 'book/mail/short_of_ipad', schedule=schedule, lesson=user.last_punch.lesson, booked_ipads=booked_ipads, available_ipads=available_ipads)
    return redirect(url_for('manage.booking', page=request.args.get('page')))


@manage.route('/booking/set-state-wait/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def set_booking_state_wait(user_id, schedule_id):
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    booking.set_state(u'排队')
    # db.session.commit()
    return redirect(url_for('manage.booking', page=request.args.get('page')))


@manage.route('/booking/set-state-invalid/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def set_booking_state_invalid(user_id, schedule_id):
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    booking.set_state(u'失效')
    # db.session.commit()
    return redirect(url_for('manage.booking', page=request.args.get('page')))


@manage.route('/booking/set-state-kept/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def set_booking_state_kept(user_id, schedule_id):
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    booking.set_state(u'赴约')
    # db.session.commit()
    return redirect(url_for('manage.booking', page=request.args.get('page')))


@manage.route('/booking/set-state-late/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def set_booking_state_late(user_id, schedule_id):
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    booking.set_state(u'迟到')
    # db.session.commit()
    return redirect(url_for('manage.booking', page=request.args.get('page')))


@manage.route('/booking/set-state-missed/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def set_booking_state_missed(user_id, schedule_id):
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    booking.set_state(u'爽约')
    # db.session.commit()
    return redirect(url_for('manage.booking', page=request.args.get('page')))


@manage.route('/booking/set-state-canceled/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def set_booking_state_canceled(user_id, schedule_id):
    user = User.query.get_or_404(user_id)
    schedule = Schedule.query.get_or_404(schedule_id)
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    candidate = booking.set_state(u'取消')
    db.session.commit()
    if candidate:
        send_email(candidate.email, u'您已成功预约%s的%s课程' % (booking.schedule.date, booking.schedule.period.alias), 'book/mail/booking', user=candidate, schedule=schedule, booking=booking)
        booked_ipads = Booking.query\
            .join(Punch, Punch.user_id == Booking.user_id)\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .filter(Booking.schedule_id == schedule_id)\
            .filter(BookingState.name == u'预约')\
            .filter(Punch.lesson_id == candidate.last_punch.lesson_id)
        available_ipads = iPad.query\
            .join(iPadContent, iPadContent.ipad_id == iPad.id)\
            .join(iPadState, iPadState.id == iPad.state_id)\
            .filter(iPadContent.lesson_id == candidate.last_punch.lesson_id)\
            .filter(iPadState.name != u'退役')
        if booked_ipads.count() >= available_ipads.count():
            for manager in User.query.all():
                if manager.can(Permission.MANAGE_IPAD):
                    send_email(manager.email, u'含有课程“%s”的iPad资源紧张' % candidate.last_punch.lesson.name, 'book/mail/short_of_ipad', schedule=schedule, lesson=candidate.last_punch.lesson, booked_ipads=booked_ipads, available_ipads=available_ipads)
    return redirect(url_for('manage.booking', page=request.args.get('page')))


def time_now(utcOffset=0):
    hour = datetime.utcnow().hour + utcOffset
    if hour >= 24:
        hour -= 24
    minute = datetime.utcnow().minute
    second = datetime.utcnow().second
    microsecond = datetime.utcnow().microsecond
    return time(hour, minute, second, microsecond)


@manage.route('/booking/set-state-missed-all')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def set_booking_state_missed_all():
    history_unmarked_missed_bookings = Booking.query\
        .join(BookingState, BookingState.id == Booking.state_id)\
        .join(Schedule, Schedule.id == Booking.schedule_id)\
        .filter(BookingState.name == u'预约')\
        .filter(Schedule.date < date.today())\
        .all()
    today_unmarked_missed_bookings = Booking.query\
        .join(BookingState, BookingState.id == Booking.state_id)\
        .join(Schedule, Schedule.id == Booking.schedule_id)\
        .join(Period, Period.id == Schedule.period_id)\
        .filter(BookingState.name == u'预约')\
        .filter(Schedule.date == date.today())\
        .filter(Period.end_time < time_now(utcOffset=current_app.config['UTC_OFFSET']))\
        .all()
    for booking in history_unmarked_missed_bookings + today_unmarked_missed_bookings:
        booking.set_state(u'爽约')
    history_unmarked_waited_bookings = Booking.query\
        .join(BookingState, BookingState.id == Booking.state_id)\
        .join(Schedule, Schedule.id == Booking.schedule_id)\
        .filter(BookingState.name == u'排队')\
        .filter(Schedule.date < date.today())\
        .all()
    today_unmarked_waited_bookings = Booking.query\
        .join(BookingState, BookingState.id == Booking.state_id)\
        .join(Schedule, Schedule.id == Booking.schedule_id)\
        .join(Period, Period.id == Schedule.period_id)\
        .filter(BookingState.name == u'排队')\
        .filter(Schedule.date == date.today())\
        .filter(Period.end_time < time_now(utcOffset=current_app.config['UTC_OFFSET']))\
        .all()
    for booking in history_unmarked_waited_bookings + today_unmarked_waited_bookings:
        booking.set_state(u'失效')
    db.session.commit()
    flash(u'标记“爽约”：%s条；标记“失效”：%s条' % (len(history_unmarked_missed_bookings + today_unmarked_missed_bookings), len(history_unmarked_waited_bookings + today_unmarked_waited_bookings)))
    return redirect(url_for('manage.booking', page=request.args.get('page')))


@manage.route('/schedule', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_SCHEDULE)
def schedule():
    form = NewScheduleForm()
    if form.validate_on_submit():
        day = date(*[int(x) for x in form.date.data.split('-')])
        for period_id in form.period.data:
            schedule = Schedule.query.filter_by(date=day, period_id=period_id).first()
            if schedule:
                flash(u'该时段已存在：%s，%s时段：%s - %s' % (schedule.date, schedule.period.type.name, schedule.period.start_time, schedule.period.end_time))
            else:
                period = Period.query.filter_by(id=period_id).first()
                if datetime(day.year, day.month, day.day, period.start_time.hour, period.start_time.minute) < datetime.now():
                    flash(u'该时段已过期：%s，%s时段：%s - %s' % (day, period.type.name, period.start_time, period.end_time))
                else:
                    schedule = Schedule(date=day, period_id=period_id, quota=form.quota.data, available=form.publish_now.data)
                    db.session.add(schedule)
                    db.session.commit()
                    flash(u'添加时段：%s，%s时段：%s - %s' % (schedule.date, schedule.period.type.name, schedule.period.start_time, schedule.period.end_time))
        return redirect(url_for('manage.schedule'))
    page = request.args.get('page', 1, type=int)
    show_today_schedule = True
    show_future_schedule = False
    show_history_schedule = False
    if current_user.is_authenticated:
        show_today_schedule = bool(request.cookies.get('show_today_schedule', '1'))
        show_future_schedule = bool(request.cookies.get('show_future_schedule', ''))
        show_history_schedule = bool(request.cookies.get('show_history_schedule', ''))
    if show_today_schedule:
        query = Schedule.query\
            .filter(Schedule.date == date.today())
    if show_future_schedule:
        query = Schedule.query\
            .filter(Schedule.date > date.today())
    if show_history_schedule:
        query = Schedule.query\
            .filter(Schedule.date < date.today())
    pagination = query\
        .order_by(Schedule.date.desc())\
        .order_by(Schedule.period_id.asc())\
        .paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    schedules = pagination.items
    return render_template('manage/schedule.html', form=form, schedules=schedules, show_today_schedule=show_today_schedule, show_future_schedule=show_future_schedule, show_history_schedule=show_history_schedule, pagination=pagination)


@manage.route('/schedule/today')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def today_schedule():
    resp = make_response(redirect(url_for('manage.schedule')))
    resp.set_cookie('show_today_schedule', '1', max_age=30*24*60*60)
    resp.set_cookie('show_future_schedule', '', max_age=30*24*60*60)
    resp.set_cookie('show_history_schedule', '', max_age=30*24*60*60)
    return resp


@manage.route('/schedule/future')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def future_schedule():
    resp = make_response(redirect(url_for('manage.schedule')))
    resp.set_cookie('show_today_schedule', '', max_age=30*24*60*60)
    resp.set_cookie('show_future_schedule', '1', max_age=30*24*60*60)
    resp.set_cookie('show_history_schedule', '', max_age=30*24*60*60)
    return resp


@manage.route('/schedule/history')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def history_schedule():
    resp = make_response(redirect(url_for('manage.schedule')))
    resp.set_cookie('show_today_schedule', '', max_age=30*24*60*60)
    resp.set_cookie('show_future_schedule', '', max_age=30*24*60*60)
    resp.set_cookie('show_history_schedule', '1', max_age=30*24*60*60)
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
    schedule = Schedule.query.get_or_404(id)
    if schedule is None:
        flash(u'该预约时段不存在')
        return redirect(url_for('manage.schedule', page=request.args.get('page')))
    if schedule.out_of_date:
        flash(u'所选时段已经过期')
        return redirect(url_for('manage.schedule', page=request.args.get('page')))
    candidate = schedule.increase_quota()
    if candidate:
        booking = Booking.query.filter_by(user_id=candidate.id, schedule_id=schedule_id).first()
        send_email(candidate.email, u'您已成功预约%s的%s课程' % (schedule.date, schedule.period.alias), 'book/mail/booking', user=candidate, schedule=schedule, booking=booking)
        booked_ipads = Booking.query\
            .join(Punch, Punch.user_id == Booking.user_id)\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .filter(Booking.schedule_id == schedule_id)\
            .filter(BookingState.name == u'预约')\
            .filter(Punch.lesson_id == candidate.last_punch.lesson_id)
        available_ipads = iPad.query\
            .join(iPadContent, iPadContent.ipad_id == iPad.id)\
            .join(iPadState, iPadState.id == iPad.state_id)\
            .filter(iPadContent.lesson_id == candidate.last_punch.lesson_id)\
            .filter(iPadState.name != u'退役')
        if booked_ipads.count() >= available_ipads.count():
            for manager in User.query.all():
                if manager.can(Permission.MANAGE_IPAD):
                    send_email(manager.email, u'含有课程“%s”的iPad资源紧张' % candidate.last_punch.lesson.name, 'book/mail/short_of_ipad', schedule=schedule, lesson=candidate.last_punch.lesson, booked_ipads=booked_ipads, available_ipads=available_ipads)
    flash(u'所选时段名额+1')
    return redirect(url_for('manage.schedule', page=request.args.get('page')))


@manage.route('/schedule/decrease-quota/<int:id>')
@login_required
@permission_required(Permission.MANAGE_SCHEDULE)
def decrease_schedule_quota(id):
    schedule = Schedule.query.get_or_404(id)
    if schedule is None:
        flash(u'该预约时段不存在')
        return redirect(url_for('manage.schedule', page=request.args.get('page')))
    if schedule.out_of_date:
        flash(u'所选时段已经过期')
        return redirect(url_for('manage.schedule', page=request.args.get('page')))
    if schedule.quota == 0:
        flash(u'所选时段名额已经为0')
        return redirect(url_for('manage.schedule', page=request.args.get('page')))
    if schedule.quota <= schedule.occupied_quota:
        flash(u'所选时段名额不可少于预约人数')
        return redirect(url_for('manage.schedule', page=request.args.get('page')))
    schedule.decrease_quota()
    flash(u'所选时段名额-1')
    return redirect(url_for('manage.schedule', page=request.args.get('page')))


@manage.route('/period', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_SCHEDULE)
def period():
    form = NewPeriodForm()
    if form.validate_on_submit():
        name = form.name.data
        start_time = time(*[int(x) for x in form.start_time.data.split(':')])
        end_time = time(*[int(x) for x in form.end_time.data.split(':')])
        type_id = form.period_type.data
        show = form.show.data
        if start_time >= end_time:
            flash(u'无法添加时段模板：%s，时间设置有误' % name)
            return redirect(url_for('manage.period'))
        period = Period(name=name, start_time=start_time, end_time=end_time, type_id=type_id, show=show)
        db.session.add(period)
        db.session.commit()
        flash(u'已添加时段模板：%s' % name)
        return redirect(url_for('manage.period'))
    page = request.args.get('page', 1, type=int)
    query = Period.query
    pagination = query\
        .order_by(Period.id.asc())\
        .paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    periods = pagination.items
    return render_template('manage/period.html', form=form, periods=periods, pagination=pagination)


@manage.route('/edit-period/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_SCHEDULE)
def edit_period(id):
    period = Period.query.get_or_404(id)
    form = EditPeriodForm()
    if form.validate_on_submit():
        name = form.name.data
        start_time = time(*[int(x) for x in form.start_time.data.split(':')])
        end_time = time(*[int(x) for x in form.end_time.data.split(':')])
        type_id = form.period_type.data
        show = form.show.data
        if start_time >= end_time:
            flash(u'无法更新时段模板：%s，时间设置有误' % name)
            return redirect(url_for('manage.edit_period', id=period.id))
        period.name = name
        period.start_time = start_time
        period.end_time = end_time
        period.type_id = type_id
        period.show = show
        db.session.add(period)
        db.session.commit()
        flash(u'已更新时段模板：%s' % name)
        return redirect(url_for('manage.period'))
    form.name.data = period.name
    form.start_time.data = period.start_time.strftime(u'%H:%M')
    form.end_time.data = period.end_time.strftime(u'%H:%M')
    form.period_type.data = period.type_id
    form.show.data = period.show
    return render_template('manage/edit_period.html', form=form, period=period)


@manage.route('/delete-period/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_SCHEDULE)
def delete_period(id):
    period = Period.query.get_or_404(id)
    name = period.name
    form = DeletePeriodForm()
    if form.validate_on_submit():
        if period.used:
            flash(u'时段模板“%s”已被使用中，无法删除' % name)
            return redirect(url_for('manage.period'))
        db.session.delete(period)
        db.session.commit()
        flash(u'已删除时段模板：%s' % name)
        return redirect(url_for('manage.period'))
    return render_template('manage/delete_period.html', form=form, period=period)


@manage.route('/ipad', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_IPAD)
def ipad():
    form = NewiPadForm()
    if form.validate_on_submit():
        alias = form.alias.data
        serial = form.serial.data.upper()
        capacity_id = form.capacity.data
        room_id = form.room.data
        if room_id == 0:
            room_id = None
        state_id = form.state.data
        ipad = iPad.query.filter_by(serial=serial).first()
        if ipad:
            flash(u'序列号为%s的iPad已存在' % serial)
            return redirect(url_for('manage.ipad'))
        ipad = iPad(serial=serial, alias=alias, capacity_id=capacity_id, room_id=room_id, state_id=state_id)
        db.session.add(ipad)
        db.session.commit()
        for lesson_id in form.vb_lessons.data + form.y_gre_lessons.data:
            ipad.add_lesson(lesson_id)
        db.session.commit()
        iPadContentJSON.mark_out_of_date()
        flash(u'成功添加序列号为%s的iPad' % serial)
        return redirect(url_for('manage.ipad'))
    maintain_num = iPad.query\
        .join(iPadState, iPadState.id == iPad.state_id)\
        .filter(iPadState.name == u'维护')\
        .count()
    charge_num = iPad.query\
        .join(iPadState, iPadState.id == iPad.state_id)\
        .filter(iPadState.name == u'充电')\
        .count()
    page = request.args.get('page', 1, type=int)
    show_all = True
    show_maintain = False
    show_charge = False
    show_1103 = False
    show_1707 = False
    show_others = False
    if current_user.is_authenticated:
        show_all = bool(request.cookies.get('show_all', '1'))
        show_maintain = bool(request.cookies.get('show_maintain', ''))
        show_charge = bool(request.cookies.get('show_charge', ''))
        show_1103 = bool(request.cookies.get('show_1103', ''))
        show_1707 = bool(request.cookies.get('show_1707', ''))
        show_others = bool(request.cookies.get('show_others', ''))
    if show_all:
        query = iPad.query
    if show_maintain:
        query = iPad.query\
            .join(iPadState, iPadState.id == iPad.state_id)\
            .filter(iPadState.name == u'维护')
    if show_charge:
        query = iPad.query\
            .join(iPadState, iPadState.id == iPad.state_id)\
            .filter(iPadState.name == u'充电')
    if show_1103:
        query = iPad.query\
            .join(Room, Room.id == iPad.room_id)\
            .filter(Room.name == u'1103')
    if show_1707:
        query = iPad.query\
            .join(Room, Room.id == iPad.room_id)\
            .filter(Room.name == u'1707')
    if show_others:
        query = iPad.query.filter_by(room_id=None)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    ipads = pagination.items
    return render_template('manage/ipad.html', form=form, ipads=ipads, maintain_num=maintain_num, charge_num=charge_num, show_all=show_all, show_maintain=show_maintain, show_charge=show_charge, show_1103=show_1103, show_1707=show_1707, show_others=show_others, pagination=pagination)


@manage.route('/ipad/all')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def all_ipads():
    resp = make_response(redirect(url_for('manage.ipad')))
    resp.set_cookie('show_all', '1', max_age=30*24*60*60)
    resp.set_cookie('show_maintain', '', max_age=30*24*60*60)
    resp.set_cookie('show_charge', '', max_age=30*24*60*60)
    resp.set_cookie('show_1103', '', max_age=30*24*60*60)
    resp.set_cookie('show_1707', '', max_age=30*24*60*60)
    resp.set_cookie('show_others', '', max_age=30*24*60*60)
    return resp


@manage.route('/ipad/maintain')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def maintain_ipads():
    resp = make_response(redirect(url_for('manage.ipad')))
    resp.set_cookie('show_all', '', max_age=30*24*60*60)
    resp.set_cookie('show_maintain', '1', max_age=30*24*60*60)
    resp.set_cookie('show_charge', '', max_age=30*24*60*60)
    resp.set_cookie('show_1103', '', max_age=30*24*60*60)
    resp.set_cookie('show_1707', '', max_age=30*24*60*60)
    resp.set_cookie('show_others', '', max_age=30*24*60*60)
    return resp


@manage.route('/ipad/charge')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def charge_ipads():
    resp = make_response(redirect(url_for('manage.ipad')))
    resp.set_cookie('show_all', '', max_age=30*24*60*60)
    resp.set_cookie('show_maintain', '', max_age=30*24*60*60)
    resp.set_cookie('show_charge', '1', max_age=30*24*60*60)
    resp.set_cookie('show_1103', '', max_age=30*24*60*60)
    resp.set_cookie('show_1707', '', max_age=30*24*60*60)
    resp.set_cookie('show_others', '', max_age=30*24*60*60)
    return resp


@manage.route('/ipad/1103')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def room_1103_ipads():
    resp = make_response(redirect(url_for('manage.ipad')))
    resp.set_cookie('show_all', '', max_age=30*24*60*60)
    resp.set_cookie('show_maintain', '', max_age=30*24*60*60)
    resp.set_cookie('show_charge', '', max_age=30*24*60*60)
    resp.set_cookie('show_1103', '1', max_age=30*24*60*60)
    resp.set_cookie('show_1707', '', max_age=30*24*60*60)
    resp.set_cookie('show_others', '', max_age=30*24*60*60)
    return resp


@manage.route('/ipad/1707')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def room_1707_ipads():
    resp = make_response(redirect(url_for('manage.ipad')))
    resp.set_cookie('show_all', '', max_age=30*24*60*60)
    resp.set_cookie('show_maintain', '', max_age=30*24*60*60)
    resp.set_cookie('show_charge', '', max_age=30*24*60*60)
    resp.set_cookie('show_1103', '', max_age=30*24*60*60)
    resp.set_cookie('show_1707', '1', max_age=30*24*60*60)
    resp.set_cookie('show_others', '', max_age=30*24*60*60)
    return resp


@manage.route('/ipad/others')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def other_ipads():
    resp = make_response(redirect(url_for('manage.ipad')))
    resp.set_cookie('show_all', '', max_age=30*24*60*60)
    resp.set_cookie('show_maintain', '', max_age=30*24*60*60)
    resp.set_cookie('show_charge', '', max_age=30*24*60*60)
    resp.set_cookie('show_1103', '', max_age=30*24*60*60)
    resp.set_cookie('show_1707', '', max_age=30*24*60*60)
    resp.set_cookie('show_others', '1', max_age=30*24*60*60)
    return resp


@manage.route('/edit-ipad/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_IPAD)
def edit_ipad(id):
    ipad = iPad.query.get_or_404(id)
    form = EditiPadForm(ipad=ipad)
    if form.validate_on_submit():
        ipad.alias = form.alias.data
        ipad.serial = form.serial.data.upper()
        ipad.capacity_id = form.capacity.data
        if form.room.data == 0:
            ipad.room_id = None
        else:
            ipad.room_id = form.room.data
        ipad.state_id = form.state.data
        db.session.add(ipad)
        db.session.commit()
        for pc in ipad.lessons_included:
            ipad.remove_lesson(pc.lesson_id)
        for lesson_id in form.vb_lessons.data + form.y_gre_lessons.data:
            ipad.add_lesson(lesson_id)
        db.session.commit()
        iPadContentJSON.mark_out_of_date()
        flash(u'iPad信息已更新')
        return redirect(url_for('manage.ipad'))
    form.alias.data = ipad.alias
    form.serial.data = ipad.serial
    form.capacity.data = ipad.capacity_id
    form.room.data = ipad.room_id
    form.state.data = ipad.state_id
    form.vb_lessons.data = ipad.vb_lesson_ids_included
    form.y_gre_lessons.data = ipad.y_gre_lesson_ids_included
    return render_template('manage/edit_ipad.html', form=form, ipad=ipad)


@manage.route('/delete-ipad/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_IPAD)
def delete_ipad(id):
    ipad = iPad.query.get_or_404(id)
    form = DeleteiPadForm(ipad=ipad)
    if form.validate_on_submit():
        ipad_serial = ipad.serial
        for pc in ipad.lessons_included:
            ipad.remove_lesson(pc.lesson_id)
        db.session.delete(ipad)
        db.session.commit()
        iPadContentJSON.mark_out_of_date()
        flash(u'已删除序列号为%s的iPad' % ipad_serial)
        return redirect(url_for('manage.ipad'))
    return render_template('manage/delete_ipad.html', form=form, ipad=ipad)


@manage.route('/filter-ipad', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE)
def filter_ipad():
    ipads = []
    form = FilteriPadForm()
    if form.validate_on_submit():
        lesson_ids = form.vb_lessons.data + form.y_gre_lessons.data
        if len(lesson_ids):
            ipad_ids = reduce(lambda x, y: x & y, [set([query.ipad_id for query in iPadContent.query.filter_by(lesson_id=lesson_id).all()]) for lesson_id in lesson_ids])
            ipads = [iPad.query.filter_by(id=ipad_id).first() for ipad_id in ipad_ids]
    return render_template('manage/filter_ipad.html', form=form, ipads=ipads)


@manage.route('/ipad/contents')
@login_required
@permission_required(Permission.MANAGE)
def ipad_contents():
    ipad_contents = iPadContentJSON.query.get_or_404(1)
    if ipad_contents.out_of_date:
        iPadContentJSON.update()
    return render_template('manage/ipad_contents.html', ipad_contents=json.loads(ipad_contents.json_string))


@manage.route('/user', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_USER)
def user():
    form = NewActivationForm()
    if form.validate_on_submit():
        name = form.name.data
        activation_code = form.activation_code.data
        role_id = form.role.data
        vb_course_id = form.vb_course.data
        if vb_course_id == 0:
            vb_course_id = None
        y_gre_course_id = form.y_gre_course.data
        if y_gre_course_id == 0:
            y_gre_course_id = None
        activation = Activation(name=name, activation_code=activation_code, role_id=role_id, vb_course_id=vb_course_id, y_gre_course_id=y_gre_course_id, inviter_id=current_user.id)
        db.session.add(activation)
        db.session.commit()
        flash(u'%s用户：%s添加成功' % (activation.role.name, activation.name))
        return redirect(url_for('manage.user'))
    page = request.args.get('page', 1, type=int)
    show_users = True
    show_activations = False
    if current_user.is_authenticated:
        show_users = bool(request.cookies.get('show_users', '1'))
        show_activations = bool(request.cookies.get('show_activations', ''))
    pagination_users = User.query\
        .join(Role, Role.id == User.role_id)\
        .filter(or_(
            Role.name == u'禁止预约',
            Role.name == u'单VB',
            Role.name == u'Y-GRE 普通',
            Role.name == u'Y-GRE VBx2',
            Role.name == u'Y-GRE A权限'
        ))\
        .order_by(User.last_seen.desc())\
        .paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    users = pagination_users.items
    pagination_activations = Activation.query\
        .join(Role, Role.id == Activation.role_id)\
        .filter(or_(
            Role.name == u'禁止预约',
            Role.name == u'单VB',
            Role.name == u'Y-GRE 普通',
            Role.name == u'Y-GRE VBx2',
            Role.name == u'Y-GRE A权限'
        ))\
        .order_by(Activation.timestamp.desc())\
        .paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    activations = pagination_activations.items
    return render_template('manage/user.html', users=users, activations=activations, form=form, show_users=show_users, show_activations=show_activations, pagination_users=pagination_users, pagination_activations=pagination_activations)


@manage.route('/user/users')
@login_required
@permission_required(Permission.MANAGE_USER)
def users():
    resp = make_response(redirect(url_for('manage.user')))
    resp.set_cookie('show_users', '1', max_age=30*24*60*60)
    resp.set_cookie('show_activations', '', max_age=30*24*60*60)
    return resp


@manage.route('/user/activations')
@login_required
@permission_required(Permission.MANAGE_USER)
def activations():
    resp = make_response(redirect(url_for('manage.user')))
    resp.set_cookie('show_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_activations', '1', max_age=30*24*60*60)
    return resp


@manage.route('/edit-activation/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_USER)
def edit_activation(id):
    activation = Activation.query.get_or_404(id)
    form = EditActivationForm()
    if form.validate_on_submit():
        activation.name = form.name.data
        activation.activation_code = form.activation_code.data
        activation.role_id = form.role.data
        activation.vb_course_id = form.vb_course.data
        activation.y_gre_course_id = form.y_gre_course.data
        db.session.add(activation)
        db.session.commit()
        flash(u'%s的激活信息已更新' % activation.name)
        return redirect(url_for('manage.user'))
    form.name.data = activation.name
    form.activation_code.data = None
    form.role.data = activation.role_id
    form.vb_course.data = activation.vb_course_id
    form.y_gre_course.data = activation.y_gre_course_id
    return render_template('manage/edit_activation.html', form=form, activation=activation)


@manage.route('/delete-activation/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_USER)
def delete_activation(id):
    activation = Activation.query.get_or_404(id)
    name = activation.name
    form = DeleteActivationForm(activation=activation)
    if form.validate_on_submit():
        db.session.delete(activation)
        db.session.commit()
        flash(u'已删除%s的激活邀请' % name)
        return redirect(url_for('manage.user'))
    return render_template('manage/delete_activation.html', form=form, activation=activation)


@manage.route('/edit-user/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_USER)
def edit_user(id):
    user = User.query.get_or_404(id)
    form = EditUserForm(user=user)
    if form.validate_on_submit():
        user.name = form.name.data
        # user.email = form.email.data
        user.role_id = form.role.data
        if user.vb_course:
            user.unregister(user.vb_course)
        if form.vb_course.data:
            user.register(Course.query.filter_by(id=form.vb_course.data).first())
        if user.y_gre_course:
            user.unregister(user.y_gre_course)
        if form.y_gre_course.data:
            user.register(Course.query.filter_by(id=form.y_gre_course.data).first())
        db.session.add(user)
        db.session.commit()
        flash(u'%s的账户信息已更新' % user.name)
        return redirect(request.args.get('next') or url_for('manage.user'))
    form.name.data = user.name
    form.email.data = user.email
    form.role.data = user.role_id
    if user.vb_course:
        form.vb_course.data = user.vb_course.id
    if user.y_gre_course:
        form.y_gre_course.data = user.y_gre_course.id
    return render_template('manage/edit_user.html', form=form, user=user)


@manage.route('/edit-punch/step-1/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def edit_punch_step_1(user_id):
    user = User.query.get_or_404(user_id)
    form = EditPunchLessonForm()
    if form.validate_on_submit():
        lesson_id = form.lesson.data
        return redirect(url_for('manage.edit_punch_step_2', user_id=user_id, lesson_id=lesson_id, next=request.args.get('next')))
    form.lesson.data = user.last_punch.lesson_id
    return render_template('manage/edit_punch_step_1.html', user=user, form=form, next=request.args.get('next'))


@manage.route('/edit-punch/step-2/<int:user_id>/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def edit_punch_step_2(user_id, lesson_id):
    user = User.query.get_or_404(user_id)
    lesson = Lesson.query.get_or_404(lesson_id)
    form = EditPunchSectionForm(lesson=lesson)
    if form.validate_on_submit():
        section_id = form.section.data
        return redirect(url_for('manage.edit_punch_step_3', user_id=user_id, lesson_id=lesson_id, section_id=section_id, next=request.args.get('next')))
    return render_template('manage/edit_punch_step_2.html', user=user, lesson=lesson, form=form, next=request.args.get('next'))


@manage.route('/edit-punch/step-3/<int:user_id>/<int:lesson_id>/<int:section_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def edit_punch_step_3(user_id, lesson_id, section_id):
    user = User.query.get_or_404(user_id)
    lesson = Lesson.query.get_or_404(lesson_id)
    section = Section.query.get_or_404(section_id)
    form = ConfirmPunchForm()
    if form.validate_on_submit():
        punch = Punch.query\
            .filter_by(user_id=user_id, lesson_id=lesson_id, section_id=section_id)\
            .first()
        if punch is not None:
            # punches = Punch.query\
            #     .filter(Punch.timestamp > punch.timestamp)\
            #     .all()
            # for pun in punches:
            #     db.session.delete(pun)
            punch.timestamp = datetime.utcnow()
        else:
            punch = Punch(user_id=user_id, lesson_id=lesson_id, section_id=section_id)
        db.session.add(punch)
        db.session.commit()
        flash(u'已保存%s的进度信息为：%s - %s - %s' % (user.name, lesson.type.name, lesson.name, section.name))
        return redirect(request.args.get('next') or url_for('manage.find_user'))
    return render_template('manage/edit_punch_step_3.html', user=user, lesson=lesson, section=section, form=form, next=request.args.get('next'))


@manage.route('/find-user', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE)
def find_user():
    name_or_email = request.args.get('keyword')
    if name_or_email:
        users = User.query\
            .join(Role, Role.id == User.role_id)\
            .filter(or_(
                User.name == name_or_email,
                User.email == name_or_email
            ))\
            .filter(or_(
                Role.name == u'禁止预约',
                Role.name == u'单VB',
                Role.name == u'Y-GRE 普通',
                Role.name == u'Y-GRE VBx2',
                Role.name == u'Y-GRE A权限'
            ))\
            .order_by(User.last_seen.desc())
    else:
        users = []
    form = FindUserForm()
    if form.validate_on_submit():
        name_or_email = form.name_or_email.data
        if name_or_email:
            users = User.query\
                .join(Role, Role.id == User.role_id)\
                .filter(or_(
                    User.name == name_or_email,
                    User.email == name_or_email
                ))\
                .filter(or_(
                    Role.name == u'禁止预约',
                    Role.name == u'单VB',
                    Role.name == u'Y-GRE 普通',
                    Role.name == u'Y-GRE VBx2',
                    Role.name == u'Y-GRE A权限'
                ))\
                .order_by(User.last_seen.desc())
    form.name_or_email.data = name_or_email
    return render_template('manage/find_user.html', form=form, users=users, keyword=name_or_email)


@manage.route('/analytics')
@login_required
@permission_required(Permission.MANAGE)
def analytics():
    analytics_token = current_app.config['ANALYTICS_TOKEN']
    return render_template('manage/analytics.html', analytics_token=analytics_token)


@manage.route('/auth')
@login_required
@permission_required(Permission.MANAGE_AUTH)
def auth():
    page = request.args.get('page', 1, type=int)
    show_auth_managers = True
    show_auth_users = False
    if current_user.is_authenticated:
        show_auth_managers = bool(request.cookies.get('show_auth_managers', '1'))
        show_auth_users = bool(request.cookies.get('show_auth_users', ''))
    if show_auth_managers:
        query = User.query\
            .join(Role, Role.id == User.role_id)\
            .filter(or_(
                Role.name == u'预约协管员',
                Role.name == u'iPad借阅协管员',
                Role.name == u'时段协管员',
                Role.name == u'iPad内容协管员',
                Role.name == u'用户协管员',
                Role.name == u'志愿者',
                Role.name == u'管理员'
            ))\
            .order_by(User.last_seen.desc())
    if show_auth_users:
        query = User.query\
            .join(Role, Role.id == User.role_id)\
            .filter(or_(
                Role.name == u'禁止预约',
                Role.name == u'单VB',
                Role.name == u'Y-GRE 普通',
                Role.name == u'Y-GRE VBx2',
                Role.name == u'Y-GRE A权限'
            ))\
            .order_by(User.last_seen.desc())
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    users = pagination.items
    return render_template('manage/auth.html', users=users, show_auth_managers=show_auth_managers, show_auth_users=show_auth_users, pagination=pagination)


@manage.route('/auth/managers')
@login_required
@permission_required(Permission.MANAGE_AUTH)
def auth_managers():
    resp = make_response(redirect(url_for('manage.auth')))
    resp.set_cookie('show_auth_managers', '1', max_age=30*24*60*60)
    resp.set_cookie('show_auth_users', '', max_age=30*24*60*60)
    return resp


@manage.route('/auth/users')
@login_required
@permission_required(Permission.MANAGE_AUTH)
def auth_users():
    resp = make_response(redirect(url_for('manage.auth')))
    resp.set_cookie('show_auth_managers', '', max_age=30*24*60*60)
    resp.set_cookie('show_auth_users', '1', max_age=30*24*60*60)
    return resp


@manage.route('/edit-auth/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_AUTH)
def edit_auth(id):
    user = User.query.get_or_404(id)
    form = EditAuthForm(user=user)
    if form.validate_on_submit():
        user.name = form.name.data
        # user.email = form.email.data
        user.role_id = form.role.data
        if user.vb_course:
            user.unregister(user.vb_course)
        if form.vb_course.data:
            user.register(Course.query.filter_by(id=form.vb_course.data).first())
        if user.y_gre_course:
            user.unregister(user.y_gre_course)
        if form.y_gre_course.data:
            user.register(Course.query.filter_by(id=form.y_gre_course.data).first())
        db.session.add(user)
        db.session.commit()
        flash(u'%s的账户信息已更新' % user.name)
        return redirect(url_for('manage.auth'))
    form.name.data = user.name
    form.email.data = user.email
    form.role.data = user.role_id
    if user.vb_course:
        form.vb_course.data = user.vb_course.id
    if user.y_gre_course:
        form.y_gre_course.data = user.y_gre_course.id
    return render_template('manage/edit_auth.html', form=form, user=user)


@manage.route('/auth-admin')
@login_required
@permission_required(Permission.ADMINISTER)
def auth_admin():
    page = request.args.get('page', 1, type=int)
    show_auth_managers_admin = True
    show_auth_users_admin = False
    if current_user.is_authenticated:
        show_auth_managers_admin = bool(request.cookies.get('show_auth_managers_admin', '1'))
        show_auth_users_admin = bool(request.cookies.get('show_auth_users_admin', ''))
    if show_auth_managers_admin:
        query = User.query\
            .join(Role, Role.id == User.role_id)\
            .filter(or_(
                Role.name == u'预约协管员',
                Role.name == u'iPad借阅协管员',
                Role.name == u'时段协管员',
                Role.name == u'iPad内容协管员',
                Role.name == u'用户协管员',
                Role.name == u'志愿者',
                Role.name == u'管理员',
                Role.name == u'开发人员'
            ))\
            .order_by(Role.id.desc())
    if show_auth_users_admin:
        query = User.query\
            .join(Role, Role.id == User.role_id)\
            .filter(or_(
                Role.name == u'禁止预约',
                Role.name == u'单VB',
                Role.name == u'Y-GRE 普通',
                Role.name == u'Y-GRE VBx2',
                Role.name == u'Y-GRE A权限'
            ))\
            .order_by(User.last_seen.desc())
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    users = pagination.items
    return render_template('manage/auth_admin.html', users=users, show_auth_managers_admin=show_auth_managers_admin, show_auth_users_admin=show_auth_users_admin, pagination=pagination)


@manage.route('/auth/managers-admin')
@login_required
@permission_required(Permission.ADMINISTER)
def auth_managers_admin():
    resp = make_response(redirect(url_for('manage.auth_admin')))
    resp.set_cookie('show_auth_managers_admin', '1', max_age=30*24*60*60)
    resp.set_cookie('show_auth_users_admin', '', max_age=30*24*60*60)
    return resp


@manage.route('/auth/users-admin')
@login_required
@permission_required(Permission.ADMINISTER)
def auth_users_admin():
    resp = make_response(redirect(url_for('manage.auth_admin')))
    resp.set_cookie('show_auth_managers_admin', '', max_age=30*24*60*60)
    resp.set_cookie('show_auth_users_admin', '1', max_age=30*24*60*60)
    return resp


@manage.route('/edit-auth-admin/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.ADMINISTER)
def edit_auth_admin(id):
    user = User.query.get_or_404(id)
    form = EditAuthFormAdmin(user=user)
    if form.validate_on_submit():
        user.name = form.name.data
        # user.email = form.email.data
        user.role_id = form.role.data
        if user.vb_course:
            user.unregister(user.vb_course)
        if form.vb_course.data:
            user.register(Course.query.filter_by(id=form.vb_course.data).first())
        if user.y_gre_course:
            user.unregister(user.y_gre_course)
        if form.y_gre_course.data:
            user.register(Course.query.filter_by(id=form.y_gre_course.data).first())
        db.session.add(user)
        db.session.commit()
        flash(u'%s的账户信息已更新' % user.name)
        return redirect(url_for('manage.auth_admin'))
    form.name.data = user.name
    form.email.data = user.email
    form.role.data = user.role_id
    if user.vb_course:
        form.vb_course.data = user.vb_course.id
    if user.y_gre_course:
        form.y_gre_course.data = user.y_gre_course.id
    return render_template('manage/edit_auth_admin.html', form=form, user=user)


@manage.route('/rental')
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def rental():
    page = request.args.get('page', 1, type=int)
    show_today_rental = True
    show_history_rental = False
    if current_user.is_authenticated:
        show_today_rental = bool(request.cookies.get('show_today_rental', '1'))
        show_history_rental = bool(request.cookies.get('show_history_rental', ''))
    if show_today_rental:
        query = Rental.query\
            .filter(Rental.date == date.today())\
            .order_by(Rental.rent_time.desc())
    if show_history_rental:
        query = Rental.query\
            .filter(Rental.date < date.today())\
            .order_by(Rental.date.desc())\
            .order_by(Rental.return_time.desc())
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    rentals = pagination.items
    return render_template('manage/rental.html', rentals=rentals, show_today_rental=show_today_rental, show_history_rental=show_history_rental, pagination=pagination)


@manage.route('/rental/today')
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def rental_today():
    resp = make_response(redirect(url_for('manage.rental')))
    resp.set_cookie('show_today_rental', '1', max_age=30*24*60*60)
    resp.set_cookie('show_history_rental', '', max_age=30*24*60*60)
    return resp


@manage.route('/rental/history')
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def rental_history():
    resp = make_response(redirect(url_for('manage.rental')))
    resp.set_cookie('show_today_rental', '', max_age=30*24*60*60)
    resp.set_cookie('show_history_rental', '1', max_age=30*24*60*60)
    return resp


@manage.route('/rental/rent/step-1', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def rental_rent_step_1():
    form = BookingCodeForm()
    if form.validate_on_submit():
        booking_code = form.booking_code.data
        booking = Booking.query.filter_by(booking_code=booking_code).first()
        if not booking:
            flash(u'预约码无效')
            return redirect(url_for('manage.rental_rent_step_1'))
        if not booking.valid:
            flash(u'该预约处于“%s”状态' % booking.state.name)
            return redirect(url_for('manage.rental_rent_step_1'))
        if booking.schedule.date != date.today():
            flash(u'预约的日期（%s）不在今天' % booking.schedule.date)
            return redirect(url_for('manage.rental_rent_step_1'))
        if booking.schedule.ended:
            booking.set_state(u'爽约')
            # db.session.commit()
        if booking.schedule.started_n_min(n_min=current_app.config['TOLERATE_MINUTES']):
            booking.set_state(u'迟到')
            # db.session.commit()
        if booking.schedule.unstarted_n_min(n_min=current_app.config['TOLERATE_MINUTES']):
            booking.set_state(u'赴约')
            # db.session.commit()
        return redirect(url_for('manage.rental_rent_step_2', user_id=booking.user_id))
    return render_template('manage/rental_rent_step_1.html', form=form)


@manage.route('/rental/rent/step-2/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def rental_rent_step_2(user_id):
    user = User.query.get_or_404(user_id)
    form = RentiPadForm(user=user)
    if form.validate_on_submit():
        ipad_id = form.ipad.data
        return redirect(url_for('manage.rental_rent_step_3', user_id=user_id, ipad_id=ipad_id))
    return render_template('manage/rental_rent_step_2.html', user=user, form=form)


@manage.route('/rental/rent/step-3/<int:user_id>/<int:ipad_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def rental_rent_step_3(user_id, ipad_id):
    user = User.query.get_or_404(user_id)
    ipad = iPad.query.get_or_404(ipad_id)
    form = ConfirmiPadForm()
    if form.validate_on_submit():
        serial = form.serial.data
        if serial != ipad.serial:
            flash(u'iPad序列号信息有误')
            return redirect(url_for('manage.rental_rent_step_3', user_id=user_id, ipad_id=ipad_id))
        if ipad.state.name not in [u'待机', u'候补']:
            flash(u'序列号为%s的iPad处于“%s”状态，不能借出' % (ipad.serial, ipad.state.name))
            return redirect(url_for('manage.rental_rent_step_3', user_id=user_id, ipad_id=ipad_id))
        if user.has_unreturned_ipads:
            flash(u'%s有未归换的iPad' % user.name)
            return redirect(url_for('manage.rental_rent_step_3', user_id=user_id, ipad_id=ipad_id))
        rental = Rental(user=user, ipad=ipad, rent_agent_id=current_user.id)
        db.session.add(rental)
        ipad.set_state(u'借出')
        # db.session.commit()
        flash(u'iPad借出信息登记成功')
        return redirect(url_for('manage.rental'))
    return render_template('manage/rental_rent_step_3.html', user=user, ipad=ipad, form=form)


@manage.route('/rental/rent/step-1-alt', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def rental_rent_step_1_alt():
    form = RentalEmailForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user is None:
            flash(u'邮箱不存在')
            return redirect(url_for('manage.rental_rent_step_1_alt'))
        return redirect(url_for('manage.rental_rent_step_2_alt', user_id=user.id))
    return render_template('manage/rental_rent_step_1_alt.html', form=form)


@manage.route('/rental/rent/step-2-alt/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def rental_rent_step_2_alt(user_id):
    user = User.query.get_or_404(user_id)
    form = RentiPadForm(user=user)
    if form.validate_on_submit():
        ipad_id = form.ipad.data
        return redirect(url_for('manage.rental_rent_step_3_alt', user_id=user_id, ipad_id=ipad_id))
    return render_template('manage/rental_rent_step_2_alt.html', user=user, form=form)


@manage.route('/rental/rent/step-3-alt/<int:user_id>/<int:ipad_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def rental_rent_step_3_alt(user_id, ipad_id):
    user = User.query.get_or_404(user_id)
    ipad = iPad.query.get_or_404(ipad_id)
    form = ConfirmiPadForm()
    if form.validate_on_submit():
        serial = form.serial.data
        if serial != ipad.serial:
            flash(u'iPad序列号信息有误')
            return redirect(url_for('manage.rental_rent_step_3_alt', user_id=user_id, ipad_id=ipad_id))
        if ipad.state.name not in [u'待机', u'候补']:
            flash(u'序列号为%s的iPad处于“%s”状态，不能借出' % (ipad.serial, ipad.state.name))
            return redirect(url_for('manage.rental_rent_step_3_alt', user_id=user_id, ipad_id=ipad_id))
        if user.has_unreturned_ipads:
            flash(u'%s有未归换的iPad' % user.name)
            return redirect(url_for('manage.rental_rent_step_3_alt', user_id=user_id, ipad_id=ipad_id))
        rental = Rental(user=user, ipad=ipad, rent_agent_id=current_user.id)
        db.session.add(rental)
        ipad.set_state(u'借出')
        # db.session.commit()
        flash(u'iPad借出信息登记成功')
        return redirect(url_for('manage.rental'))
    return render_template('manage/rental_rent_step_3_alt.html', user=user, ipad=ipad, form=form)


@manage.route('/rental/return/step-1', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def rental_return_step_1():
    form = iPadSerialForm()
    if form.validate_on_submit():
        serial = form.serial.data
        ipad = iPad.query.filter_by(serial=serial).first()
        if ipad is None:
            flash(u'不存在序列号为%s的iPad' % serial)
            return redirect(url_for('manage.rental_return_step_1'))
        if ipad.state.name != u'借出':
            flash(u'序列号为%s的iPad处于%s状态，尚未借出' % (serial, ipad.state.name))
            return redirect(url_for('manage.rental_return_step_1'))
        rental = Rental.query.filter_by(ipad_id=ipad.id).first()
        if rental is None:
            flash(u'没有序列号为%s的iPad的借阅记录' % serial)
            return redirect(url_for('manage.rental_return_step_1'))
        if not form.root.data:
            rental.set_returned(return_agent_id=current_user.id, ipad_state=u'维护')
            db.session.commit()
            for user in User.query.all():
                if user.can(Permission.MANAGE_IPAD):
                    send_email(user.email, u'序列号为%s的iPad处于%s状态' % (serial, ipad.state.name), 'manage/mail/maintain_ipad', ipad=ipad, time=datetime.utcnow(), manager=current_user)
            flash(u'已回收序列号为%s的iPad，并设为%s状态' % (serial, ipad.state.name))
            return redirect(url_for('manage.rental_return_step_2', user_id=rental.user_id))
        if not form.battery.data:
            rental.set_returned(return_agent_id=current_user.id, ipad_state=u'充电')
            db.session.commit()
            flash(u'已回收序列号为%s的iPad，并设为%s状态' % (serial, ipad.state.name))
            return redirect(url_for('manage.rental_return_step_2', user_id=rental.user_id))
        rental.set_returned(return_agent_id=current_user.id)
        db.session.commit()
        flash(u'已回收序列号为%s的iPad' % serial)
        return redirect(url_for('manage.rental_return_step_2', user_id=rental.user_id))
    return render_template('manage/rental_return_step_1.html', form=form)


@manage.route('/rental/return/step-2/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def rental_return_step_2(user_id):
    user = User.query.get_or_404(user_id)
    form = PunchLessonForm(user=user)
    if form.validate_on_submit():
        lesson_id = form.lesson.data
        return redirect(url_for('manage.rental_return_step_3', user_id=user_id, lesson_id=lesson_id))
    return render_template('manage/rental_return_step_2.html', user=user, form=form)


@manage.route('/rental/return/step-3/<int:user_id>/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def rental_return_step_3(user_id, lesson_id):
    user = User.query.get_or_404(user_id)
    lesson = Lesson.query.get_or_404(lesson_id)
    form = PunchSectionForm(user=user, lesson=lesson)
    if form.validate_on_submit():
        section_id = form.section.data
        return redirect(url_for('manage.rental_return_step_4', user_id=user_id, lesson_id=lesson_id, section_id=section_id))
    return render_template('manage/rental_return_step_3.html', user=user, lesson=lesson, form=form)


@manage.route('/rental/return/step-4/<int:user_id>/<int:lesson_id>/<int:section_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def rental_return_step_4(user_id, lesson_id, section_id):
    user = User.query.get_or_404(user_id)
    lesson = Lesson.query.get_or_404(lesson_id)
    section = Section.query.get_or_404(section_id)
    form = ConfirmPunchForm()
    if form.validate_on_submit():
        punch = Punch(user_id=user_id, lesson_id=lesson_id, section_id=section_id)
        db.session.add(punch)
        db.session.commit()
        flash(u'已保存%s的进度信息为：%s - %s - %s' % (user.name, lesson.type.name, lesson.name, section.name))
        return redirect(url_for('manage.rental'))
    return render_template('manage/rental_return_step_4.html', user=user, lesson=lesson, section=section, form=form)


@manage.route('/rental/return/step-1-alt', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def rental_return_step_1_alt():
    form = RentalEmailForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user is None:
            flash(u'邮箱不存在')
            return redirect(url_for('manage.rental_return_step_1_alt'))
        return redirect(url_for('manage.rental_return_step_2_alt', user_id=user.id))
    return render_template('manage/rental_return_step_1_alt.html', form=form)


@manage.route('/rental/return/step-2-alt/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def rental_return_step_2_alt(user_id):
    user = User.query.get_or_404(user_id)
    form = PunchLessonForm(user=user)
    if form.validate_on_submit():
        lesson_id = form.lesson.data
        return redirect(url_for('manage.rental_return_step_3_alt', user_id=user_id, lesson_id=lesson_id))
    return render_template('manage/rental_return_step_2_alt.html', user=user, form=form)


@manage.route('/rental/return/step-3-alt/<int:user_id>/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def rental_return_step_3_alt(user_id, lesson_id):
    user = User.query.get_or_404(user_id)
    lesson = Lesson.query.get_or_404(lesson_id)
    form = PunchSectionForm(user=user, lesson=lesson)
    if form.validate_on_submit():
        section_id = form.section.data
        return redirect(url_for('manage.rental_return_step_4_alt', user_id=user_id, lesson_id=lesson_id, section_id=section_id))
    return render_template('manage/rental_return_step_3_alt.html', user=user, lesson=lesson, form=form)


@manage.route('/rental/return/step-4-alt/<int:user_id>/<int:lesson_id>/<int:section_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RENTAL)
def rental_return_step_4_alt(user_id, lesson_id, section_id):
    user = User.query.get_or_404(user_id)
    lesson = Lesson.query.get_or_404(lesson_id)
    section = Section.query.get_or_404(section_id)
    form = ConfirmPunchForm()
    if form.validate_on_submit():
        punch = Punch(user_id=user_id, lesson_id=lesson_id, section_id=section_id)
        db.session.add(punch)
        db.session.commit()
        flash(u'已保存%s的进度信息为：%s - %s - %s' % (user.name, lesson.type.name, lesson.name, section.name))
        return redirect(url_for('manage.rental'))
    return render_template('manage/rental_return_step_4_alt.html', user=user, lesson=lesson, section=section, form=form)



