# -*- coding: utf-8 -*-

from datetime import datetime, date
from sqlalchemy import or_
from flask import render_template, redirect, url_for, flash, current_app, make_response, request
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import manage
from .forms import NewScheduleForm, NewiPadForm, EditiPadForm, DeleteiPadForm, FilteriPadForm, NewActivationForm, EditActivationForm, DeleteActivationForm, EditUserForm
from .. import db
from ..email import send_email
from ..models import Permission, Role, User, Activation, Booking, Schedule, Period, iPad, iPadContent, Room, Course
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
    if booking.schedule.full:
        flash(u'该时段名额已经约满')
        return redirect(url_for('manage.booking', page=request.args.get('page')))
    booking.set_state(u'预约')
    db.session.commit()
    send_email(booking.user.email, u'您已成功预约%s的%s课程' % (schedule.date, schedule.period.alias), 'book/mail/booking', user=booking.user, schedule=booking.schedule)
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
        send_email(candidate.email, u'您已成功预约%s的%s课程' % (schedule.date, schedule.period.alias), 'book/mail/booking', user=candidate, schedule=booking.schedule)
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
    show_today = True
    show_future = False
    show_history = False
    if current_user.is_authenticated:
        show_today = bool(request.cookies.get('show_today', '1'))
        show_future = bool(request.cookies.get('show_future', ''))
        show_history = bool(request.cookies.get('show_history', ''))
    if show_today:
        query = Schedule.query\
            .filter(Schedule.date == date.today())
    if show_future:
        query = Schedule.query\
            .filter(Schedule.date > date.today())
    if show_history:
        query = Schedule.query\
            .filter(Schedule.date < date.today())
    pagination = query\
        .order_by(Schedule.date.desc())\
        .order_by(Schedule.period_id.asc())\
        .paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    schedules = pagination.items
    return render_template('manage/schedule.html', form=form, schedules=schedules, show_today=show_today, show_future=show_future, show_history=show_history, pagination=pagination)


@manage.route('/schedule/today')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def today_schedule():
    resp = make_response(redirect(url_for('manage.schedule')))
    resp.set_cookie('show_today', '1', max_age=30*24*60*60)
    resp.set_cookie('show_future', '', max_age=30*24*60*60)
    resp.set_cookie('show_history', '', max_age=30*24*60*60)
    return resp


@manage.route('/schedule/future')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def future_schedule():
    resp = make_response(redirect(url_for('manage.schedule')))
    resp.set_cookie('show_today', '', max_age=30*24*60*60)
    resp.set_cookie('show_future', '1', max_age=30*24*60*60)
    resp.set_cookie('show_history', '', max_age=30*24*60*60)
    return resp


@manage.route('/schedule/history')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def history_schedule():
    resp = make_response(redirect(url_for('manage.schedule')))
    resp.set_cookie('show_today', '', max_age=30*24*60*60)
    resp.set_cookie('show_future', '', max_age=30*24*60*60)
    resp.set_cookie('show_history', '1', max_age=30*24*60*60)
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
        send_email(candidate.email, u'您已成功预约%s的%s课程' % (schedule.date, schedule.period.alias), 'book/mail/booking', user=candidate, schedule=schedule)
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
        flash(u'成功添加序列号为%s的iPad' % serial)
        return redirect(url_for('manage.ipad'))
    page = request.args.get('page', 1, type=int)
    show_all = True
    show_1103 = False
    show_1707 = False
    show_others = False
    if current_user.is_authenticated:
        show_all = bool(request.cookies.get('show_all', '1'))
        show_1103 = bool(request.cookies.get('show_1103', ''))
        show_1707 = bool(request.cookies.get('show_1707', ''))
        show_others = bool(request.cookies.get('show_others', ''))
    if show_all:
        query = iPad.query
    if show_1103:
        query = iPad.query\
            .join(Room, Room.id == iPad.room_id)\
            .filter(Room.name == u'1103')
    if show_1707:
        query = iPad.query\
            .join(Room, Room.id == iPad.room_id)\
            .filter(Room.name == u'1707')
    if show_others:
        query = iPad.query\
            .join(Room, Room.id == iPad.room_id)\
            .filter(Room.name == u'无')
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    ipads = pagination.items
    return render_template('manage/ipad.html', form=form, ipads=ipads, show_all=show_all, show_1103=show_1103, show_1707=show_1707, show_others=show_others, pagination=pagination)


@manage.route('/ipad/all')
@login_required
@permission_required(Permission.MANAGE_BOOKING)
def all_ipads():
    resp = make_response(redirect(url_for('manage.ipad')))
    resp.set_cookie('show_all', '1', max_age=30*24*60*60)
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
        ipad.room_id = form.room.data
        ipad.state_id = form.state.data
        db.session.add(ipad)
        db.session.commit()
        for pc in ipad.lessons_included:
            ipad.remove_lesson(pc.lesson_id)
        for lesson_id in form.vb_lessons.data + form.y_gre_lessons.data:
            ipad.add_lesson(lesson_id)
        db.session.commit()
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
        flash(u'已删除序列号为%s的iPad' % ipad_serial)
        return redirect(url_for('manage.ipad'))
    return render_template('manage/delete_ipad.html', form=form, ipad=ipad)


@manage.route('/filter-ipad', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_IPAD)
def filter_ipad():
    ipads = []
    form = FilteriPadForm()
    if form.validate_on_submit():
        lesson_ids = form.vb_lessons.data + form.y_gre_lessons.data
        if len(lesson_ids):
            ipad_ids = reduce(lambda x, y: x & y, [set([query.ipad_id for query in iPadContent.query.filter_by(lesson_id=lesson_id).all()]) for lesson_id in lesson_ids])
            ipads = [iPad.query.filter_by(id=ipad_id).first() for ipad_id in ipad_ids]
    return render_template('manage/filter_ipad.html', form=form, ipads=ipads)


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
        y_gre_course_id = form.y_gre_course.data
        if Role.query.filter_by(id=role_id).first().name == u'单VB':
            activation = Activation(name=name, activation_code=activation_code, role_id=role_id, vb_course_id=vb_course_id)
            db.session.add(activation)
        elif y_gre_course_id == 0:
            flash(u'请选择%s的Y-GRE班级' % name)
            return redirect(url_for('manage.user'))
        else:
            activation = Activation(name=name, activation_code=activation_code, role_id=role_id, vb_course_id=vb_course_id, y_gre_course_id=y_gre_course_id)
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
            Role.name == u'单VB',
            Role.name == u'Y-GRE 普通',
            Role.name == u'Y-GRE VBx2',
            Role.name == u'Y-GRE A权限'
        ))\
        .order_by(Activation.id.desc())\
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
        user.email = form.email.data
        user.role_id = form.role.data
        user.unregister(user.vb_course)
        user.register(Course.query.filter_by(id=form.vb_course.data).first())
        user.unregister(user.y_gre_course)
        user.register(Course.query.filter_by(id=form.y_gre_course.data).first())
        db.session.add(user)
        db.session.commit()
        flash(u'%s的账户信息已更新' % user.name)
        return redirect(url_for('manage.user'))
    form.name.data = user.name
    form.email.data = user.email
    form.role.data = user.role_id
    form.vb_course.data = user.vb_course.id
    form.y_gre_course.data = user.y_gre_course.id
    return render_template('manage/edit_user.html', form=form, user=user)