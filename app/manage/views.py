# -*- coding: utf-8 -*-

from datetime import datetime, date, time, timedelta
from sqlalchemy import or_
import json
from flask import render_template, redirect, url_for, abort, flash, current_app, make_response, request, jsonify
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import manage
from .forms import NewScheduleForm, NewPeriodForm, EditPeriodForm, DeletePeriodForm, NewiPadForm, EditiPadForm, DeleteiPadForm, FilteriPadForm, EditPunchLessonForm, EditPunchSectionForm, BookingCodeForm, RentiPadForm, RentalEmailForm, ConfirmiPadForm, SelectLessonForm, RentiPadByLessonForm, iPadSerialForm, PunchLessonForm, PunchSectionForm, ConfirmPunchForm, NewAnnouncementForm, EditAnnouncementForm, DeleteAnnouncementForm, NewUserForm, NewEducationRecordForm, NewEmploymentRecordForm, NewPreviousAchievementForm, NewTOEFLTestScoreForm, NewAdminForm, EditUserForm, DeleteUserForm, RestoreUserForm, FindUserForm, NewCourseForm, EditCourseForm, DeleteCourseForm
from .. import db
from ..email import send_email
from ..models import Role, User, Gender, PurposeType, ReferrerType, EducationType, PreviousAchievementType, TOEFLTestScoreType, Product, InvitationType, Booking, BookingState, Rental, Punch, Period, Schedule, Lesson, Section, iPad, iPadState, iPadContent, iPadContentJSON, Room, Course, CourseType, CourseRegistration, Announcement, AnnouncementType
from ..decorators import permission_required, administrator_required, developer_required


@manage.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['YSYS_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning('Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n' % (query.statement, query.parameters, query.duration, query.context))
    return response


@manage.route('/summary')
@login_required
@permission_required(u'管理')
def summary():
    announcements = Announcement.query\
        .join(AnnouncementType, AnnouncementType.id == Announcement.type_id)\
        .filter(AnnouncementType.name == u'管理主页通知')\
        .filter(Announcement.show == True)\
        .filter(Announcement.deleted == False)\
        .all()
    for announcement in announcements:
        if not current_user.notified_by(announcement=announcement):
            flash(u'<div class="content" style="text-align: left;"><div class="header">%s</div>%s</div>' % (announcement.title, announcement.body_html), category='announcement')
            announcement.notify(user=current_user._get_current_object())
    show_summary_ipad_1103 = True
    show_summary_ipad_1707 = False
    show_summary_ipad_others = False
    if current_user.is_authenticated:
        show_summary_ipad_1103 = bool(request.cookies.get('show_summary_ipad_1103', '1'))
        show_summary_ipad_1707 = bool(request.cookies.get('show_summary_ipad_1707', ''))
        show_summary_ipad_others = bool(request.cookies.get('show_summary_ipad_others', ''))
    if show_summary_ipad_1103:
        room_id = Room.query.filter_by(name=u'1103').first().id
    if show_summary_ipad_1707:
        room_id = Room.query.filter_by(name=u'1707').first().id
    if show_summary_ipad_others:
        room_id = 0
    return render_template('manage/summary.html', room_id=room_id, show_summary_ipad_1103=show_summary_ipad_1103, show_summary_ipad_1707=show_summary_ipad_1707, show_summary_ipad_others=show_summary_ipad_others, announcements=announcements)


@manage.route('/summary/ipad/1103')
@login_required
@permission_required(u'管理')
def summary_room_1103_ipads():
    resp = make_response(redirect(url_for('manage.summary')))
    resp.set_cookie('show_summary_ipad_1103', '1', max_age=30*24*60*60)
    resp.set_cookie('show_summary_ipad_1707', '', max_age=30*24*60*60)
    resp.set_cookie('show_summary_ipad_others', '', max_age=30*24*60*60)
    return resp


@manage.route('/summary/ipad/1707')
@login_required
@permission_required(u'管理')
def summary_room_1707_ipads():
    resp = make_response(redirect(url_for('manage.summary')))
    resp.set_cookie('show_summary_ipad_1103', '', max_age=30*24*60*60)
    resp.set_cookie('show_summary_ipad_1707', '1', max_age=30*24*60*60)
    resp.set_cookie('show_summary_ipad_others', '', max_age=30*24*60*60)
    return resp


@manage.route('/summary/ipad/others')
@login_required
@permission_required(u'管理')
def summary_other_ipads():
    resp = make_response(redirect(url_for('manage.summary')))
    resp.set_cookie('show_summary_ipad_1103', '', max_age=30*24*60*60)
    resp.set_cookie('show_summary_ipad_1707', '', max_age=30*24*60*60)
    resp.set_cookie('show_summary_ipad_others', '1', max_age=30*24*60*60)
    return resp


@manage.route('/summary/ipad/room/<int:room_id>')
@permission_required(u'管理')
def summary_room(room_id):
    ipads = []
    if room_id == 0:
        ipads = iPad.query\
            .filter_by(room_id=None, deleted=False)\
            .order_by(iPad.alias.asc())
    else:
        room_id = Room.query.get_or_404(room_id).id
        ipads = iPad.query\
            .filter_by(room_id=room_id, deleted=False)\
            .order_by(iPad.alias.asc())
    return jsonify({'ipads': [ipad.to_json() for ipad in ipads]})


@manage.route('/summary/statistics')
@permission_required(u'管理')
def summary_statistics():
    statistics = {
        'booking': {
            'vb': {
                'intro': {
                    'total': Booking.of_current_vb_schedule([u'VB总论']),
                    'show_up': Booking.show_ups([u'VB总论']),
                },
                'l1_3': {
                    'total': Booking.of_current_vb_schedule([u'L1', u'L2', u'L3']),
                    'show_up': Booking.show_ups([u'L1', u'L2', u'L3']),
                },
                'l4_10': {
                    'total': Booking.of_current_vb_schedule([u'L4', u'L5', u'L6', u'L7', u'L8', u'L9', u'L10']),
                    'show_up': Booking.show_ups([u'L4', u'L5', u'L6', u'L7', u'L8', u'L9', u'L10']),
                },
                'l11_14': {
                    'total': Booking.of_current_vb_schedule([u'L11', u'L12', u'L13', u'L14']),
                    'show_up': Booking.show_ups([u'L11', u'L12', u'L13', u'L14']),
                },
            },
            'y_gre': {
                'intro': {
                    'total': Booking.of_current_y_gre_schedule([u'Y-GRE总论']),
                    'show_up': Booking.show_ups([u'Y-GRE总论']),
                },
                'y_gre': {
                    'total': Booking.of_current_y_gre_schedule([u'1st', u'2nd', u'3rd', u'4th', u'5th', u'6th', u'7th', u'8th', u'9th']),
                    'show_up': Booking.show_ups([u'1st', u'2nd', u'3rd', u'4th', u'5th', u'6th', u'7th', u'8th', u'9th']),
                },
                'test': {
                    'total': Booking.of_current_y_gre_schedule([u'Test']),
                    'show_up': Booking.show_ups([u'Test']),
                },
                'aw_intro': {
                    'total': Booking.of_current_y_gre_schedule([u'AW总论']),
                    'show_up': Booking.show_ups([u'AW总论']),
                },
            },
        },
        'room_1103': {
            'ipad': {
                'total': iPad.quantity_in_room(room_name=u'1103'),
                'standby': iPad.quantity_in_room(room_name=u'1103', state_name=u'待机'),
                'candidate': iPad.quantity_in_room(room_name=u'1103', state_name=u'候补'),
                'rent': iPad.quantity_in_room(room_name=u'1103', state_name=u'借出'),
                'maintain': iPad.quantity_in_room(room_name=u'1103', state_name=u'维护'),
                'charge': iPad.quantity_in_room(room_name=u'1103', state_name=u'充电'),
                'obsolete': iPad.quantity_in_room(room_name=u'1103', state_name=u'退役'),
            },
            'rental': {
                'walk_in': Rental.unreturned_walk_ins_in_room(u'1103'),
                'overtime': Rental.current_overtimes_in_room(u'1103'),
            },
        },
        'room_1707': {
            'ipad': {
                'total': iPad.quantity_in_room(room_name=u'1707'),
                'standby': iPad.quantity_in_room(room_name=u'1707', state_name=u'待机'),
                'candidate': iPad.quantity_in_room(room_name=u'1707', state_name=u'候补'),
                'rent': iPad.quantity_in_room(room_name=u'1707', state_name=u'借出'),
                'maintain': iPad.quantity_in_room(room_name=u'1707', state_name=u'维护'),
                'charge': iPad.quantity_in_room(room_name=u'1707', state_name=u'充电'),
                'obsolete': iPad.quantity_in_room(room_name=u'1707', state_name=u'退役'),
            },
            'rental': {
                'walk_in': Rental.unreturned_walk_ins_in_room(u'1707'),
                'overtime': Rental.current_overtimes_in_room(u'1707'),
            },
        },
    }
    return jsonify(statistics)


@manage.route('/booking')
@login_required
@permission_required(u'管理课程预约')
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
@permission_required(u'管理课程预约')
def today_booking():
    resp = make_response(redirect(url_for('manage.booking')))
    resp.set_cookie('show_today_booking', '1', max_age=30*24*60*60)
    resp.set_cookie('show_future_booking', '', max_age=30*24*60*60)
    resp.set_cookie('show_history_booking', '', max_age=30*24*60*60)
    return resp


@manage.route('/booking/future')
@login_required
@permission_required(u'管理课程预约')
def future_booking():
    resp = make_response(redirect(url_for('manage.booking')))
    resp.set_cookie('show_today_booking', '', max_age=30*24*60*60)
    resp.set_cookie('show_future_booking', '1', max_age=30*24*60*60)
    resp.set_cookie('show_history_booking', '', max_age=30*24*60*60)
    return resp


@manage.route('/booking/history')
@login_required
@permission_required(u'管理课程预约')
def history_booking():
    resp = make_response(redirect(url_for('manage.booking')))
    resp.set_cookie('show_today_booking', '', max_age=30*24*60*60)
    resp.set_cookie('show_future_booking', '', max_age=30*24*60*60)
    resp.set_cookie('show_history_booking', '1', max_age=30*24*60*60)
    return resp


@manage.route('/booking/set-state/valid/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(u'管理课程预约')
def set_booking_state_valid(user_id, schedule_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    schedule = Schedule.query.get_or_404(schedule_id)
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    if booking.schedule.full:
        flash(u'该时段名额已经约满', category='error')
        return redirect(request.args.get('next') or url_for('manage.booking'))
    booking.set_state(u'预约')
    db.session.commit()
    send_email(user.email, u'您已成功预约%s的%s课程' % (booking.schedule.date, booking.schedule.period.alias), 'book/mail/booking', user=user, schedule=schedule, booking=booking)
    booked_ipads_quantity = schedule.booked_ipads_quantity(lesson=user.last_punch.section.lesson)
    available_ipads_quantity = user.last_punch.section.lesson.available_ipads.count()
    if booked_ipads_quantity >= available_ipads_quantity:
        for manager in User.query.all():
            if manager.can(u'管理iPad设备'):
                send_email(manager.email, u'含有课程“%s”的iPad资源紧张' % user.last_punch.section.lesson.name, 'book/mail/short_of_ipad', schedule=schedule, lesson=user.last_punch.section.lesson, booked_ipads_quantity=booked_ipads_quantity, available_ipads_quantity=available_ipads_quantity)
    return redirect(request.args.get('next') or url_for('manage.booking'))


@manage.route('/booking/set-state/wait/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(u'管理课程预约')
def set_booking_state_wait(user_id, schedule_id):
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    booking.set_state(u'排队')
    return redirect(request.args.get('next') or url_for('manage.booking'))


@manage.route('/booking/set-state/invalid/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(u'管理课程预约')
def set_booking_state_invalid(user_id, schedule_id):
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    booking.set_state(u'失效')
    return redirect(request.args.get('next') or url_for('manage.booking'))


@manage.route('/booking/set-state/kept/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(u'管理课程预约')
def set_booking_state_kept(user_id, schedule_id):
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    booking.set_state(u'赴约')
    return redirect(request.args.get('next') or url_for('manage.booking'))


@manage.route('/booking/set-state/late/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(u'管理课程预约')
def set_booking_state_late(user_id, schedule_id):
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    booking.set_state(u'迟到')
    return redirect(request.args.get('next') or url_for('manage.booking'))


@manage.route('/booking/set-state/missed/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(u'管理课程预约')
def set_booking_state_missed(user_id, schedule_id):
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    booking.set_state(u'爽约')
    return redirect(request.args.get('next') or url_for('manage.booking'))


@manage.route('/booking/set-state/canceled/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(u'管理课程预约')
def set_booking_state_canceled(user_id, schedule_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    schedule = Schedule.query.get_or_404(schedule_id)
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    candidate = booking.set_state(u'取消')
    db.session.commit()
    if candidate:
        send_email(candidate.email, u'您已成功预约%s的%s课程' % (booking.schedule.date, booking.schedule.period.alias), 'book/mail/booking', user=candidate, schedule=schedule, booking=booking)
        booked_ipads_quantity = schedule.booked_ipads_quantity(lesson=candidate.last_punch.section.lesson)
        available_ipads_quantity = candidate.last_punch.section.lesson.available_ipads.count()
        if booked_ipads_quantity >= available_ipads_quantity:
            for manager in User.query.all():
                if manager.can(u'管理iPad设备'):
                    send_email(manager.email, u'含有课程“%s”的iPad资源紧张' % candidate.last_punch.section.lesson.name, 'book/mail/short_of_ipad', schedule=schedule, lesson=candidate.last_punch.section.lesson, booked_ipads_quantity=booked_ipads_quantity, available_ipads_quantity=available_ipads_quantity)
    return redirect(request.args.get('next') or url_for('manage.booking'))


def time_now(utcOffset=0):
    hour = datetime.utcnow().hour + utcOffset
    if hour >= 24:
        hour -= 24
    minute = datetime.utcnow().minute
    second = datetime.utcnow().second
    microsecond = datetime.utcnow().microsecond
    return time(hour, minute, second, microsecond)


@manage.route('/booking/set-state/missed/all')
@login_required
@permission_required(u'管理课程预约')
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
    flash(u'标记“爽约”：%s条；标记“失效”：%s条' % (len(history_unmarked_missed_bookings + today_unmarked_missed_bookings), len(history_unmarked_waited_bookings + today_unmarked_waited_bookings)), category='info')
    return redirect(request.args.get('next') or url_for('manage.booking'))


@manage.route('/rental')
@login_required
@permission_required(u'管理iPad借阅')
def rental():
    page = request.args.get('page', 1, type=int)
    show_today_rental = True
    show_today_rental_1103 = False
    show_today_rental_1707 = False
    show_history_rental = False
    if current_user.is_authenticated:
        show_today_rental = bool(request.cookies.get('show_today_rental', '1'))
        show_today_rental_1103 = bool(request.cookies.get('show_today_rental_1103', ''))
        show_today_rental_1707 = bool(request.cookies.get('show_today_rental_1707', ''))
        show_history_rental = bool(request.cookies.get('show_history_rental', ''))
    if show_today_rental:
        query = Rental.query\
            .join(Schedule, Schedule.id == Rental.schedule_id)\
            .filter(Schedule.date == date.today())\
            .order_by(Rental.rent_time.desc())
    if show_today_rental_1103:
        query = Rental.query\
            .join(Schedule, Schedule.id == Rental.schedule_id)\
            .join(iPad, iPad.id == Rental.ipad_id)\
            .join(Room, Room.id == iPad.room_id)\
            .filter(Room.name == u'1103')\
            .filter(Schedule.date == date.today())\
            .order_by(Rental.rent_time.desc())
    if show_today_rental_1707:
        query = Rental.query\
            .join(Schedule, Schedule.id == Rental.schedule_id)\
            .join(iPad, iPad.id == Rental.ipad_id)\
            .join(Room, Room.id == iPad.room_id)\
            .filter(Room.name == u'1707')\
            .filter(Schedule.date == date.today())\
            .order_by(Rental.rent_time.desc())
    if show_history_rental:
        query = Rental.query\
            .join(Schedule, Schedule.id == Rental.schedule_id)\
            .filter(Schedule.date < date.today())\
            .order_by(Schedule.date.desc())\
            .order_by(Rental.return_time.desc())
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    rentals = pagination.items
    return render_template('manage/rental.html', rentals=rentals, show_today_rental=show_today_rental, show_today_rental_1103=show_today_rental_1103, show_today_rental_1707=show_today_rental_1707, show_history_rental=show_history_rental, pagination=pagination)


@manage.route('/rental/today')
@login_required
@permission_required(u'管理iPad借阅')
def rental_today():
    resp = make_response(redirect(url_for('manage.rental')))
    resp.set_cookie('show_today_rental', '1', max_age=30*24*60*60)
    resp.set_cookie('show_today_rental_1103', '', max_age=30*24*60*60)
    resp.set_cookie('show_today_rental_1707', '', max_age=30*24*60*60)
    resp.set_cookie('show_history_rental', '', max_age=30*24*60*60)
    return resp


@manage.route('/rental/today/1103')
@login_required
@permission_required(u'管理iPad借阅')
def rental_today_1103():
    resp = make_response(redirect(url_for('manage.rental')))
    resp.set_cookie('show_today_rental', '', max_age=30*24*60*60)
    resp.set_cookie('show_today_rental_1103', '1', max_age=30*24*60*60)
    resp.set_cookie('show_today_rental_1707', '', max_age=30*24*60*60)
    resp.set_cookie('show_history_rental', '', max_age=30*24*60*60)
    return resp


@manage.route('/rental/today/1707')
@login_required
@permission_required(u'管理iPad借阅')
def rental_today_1707():
    resp = make_response(redirect(url_for('manage.rental')))
    resp.set_cookie('show_today_rental', '', max_age=30*24*60*60)
    resp.set_cookie('show_today_rental_1103', '', max_age=30*24*60*60)
    resp.set_cookie('show_today_rental_1707', '1', max_age=30*24*60*60)
    resp.set_cookie('show_history_rental', '', max_age=30*24*60*60)
    return resp


@manage.route('/rental/history')
@login_required
@permission_required(u'管理iPad借阅')
def rental_history():
    resp = make_response(redirect(url_for('manage.rental')))
    resp.set_cookie('show_today_rental', '', max_age=30*24*60*60)
    resp.set_cookie('show_today_rental_1103', '', max_age=30*24*60*60)
    resp.set_cookie('show_today_rental_1707', '', max_age=30*24*60*60)
    resp.set_cookie('show_history_rental', '1', max_age=30*24*60*60)
    return resp


@manage.route('/rental/rent/step-1', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_1():
    form = BookingCodeForm()
    if form.validate_on_submit():
        booking = Booking.query.filter_by(booking_code=form.booking_code.data).first()
        if not booking:
            flash(u'预约码无效', category='error')
            return redirect(url_for('manage.rental_rent_step_1'))
        if not booking.valid:
            flash(u'该预约处于“%s”状态' % booking.state.name, category='error')
            return redirect(url_for('manage.rental_rent_step_1'))
        if booking.schedule.date != date.today():
            flash(u'预约的日期（%s）不在今天' % booking.schedule.date, category='error')
            return redirect(url_for('manage.rental_rent_step_1'))
        if booking.schedule.ended:
            booking.set_state(u'爽约')
        if booking.schedule.started_n_min(n_min=current_app.config['TOLERATE_MINUTES']):
            booking.set_state(u'迟到')
        if booking.schedule.unstarted_n_min(n_min=current_app.config['TOLERATE_MINUTES']):
            booking.set_state(u'赴约')
        return redirect(url_for('manage.rental_rent_step_2', user_id=booking.user_id, schedule_id=booking.schedule_id))
    return render_template('manage/rental_rent_step_1.html', form=form)


@manage.route('/rental/rent/step-2/<int:user_id>/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_2(user_id, schedule_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    schedule = Schedule.query.get_or_404(schedule_id)
    form = RentiPadForm(user=user)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_rent_step_3', user_id=user_id, ipad_id=form.ipad.data, schedule_id=schedule_id))
    return render_template('manage/rental_rent_step_2.html', user=user, schedule=schedule, form=form)


@manage.route('/rental/rent/step-3/<int:user_id>/<int:ipad_id>/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_3(user_id, ipad_id, schedule_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    ipad = iPad.query.get_or_404(ipad_id)
    if ipad.deleted:
        abort(404)
    schedule = Schedule.query.get_or_404(schedule_id)
    form = ConfirmiPadForm()
    if form.validate_on_submit():
        serial = form.serial.data
        if serial != ipad.serial:
            flash(u'iPad序列号信息有误', category='error')
            return redirect(url_for('manage.rental_rent_step_3', user_id=user_id, ipad_id=ipad_id, schedule_id=schedule_id))
        if ipad.state.name not in [u'待机', u'候补']:
            flash(u'序列号为%s的iPad处于“%s”状态，不能借出' % (ipad.serial, ipad.state.name), category='error')
            return redirect(url_for('manage.rental_rent_step_3', user_id=user_id, ipad_id=ipad_id, schedule_id=schedule_id))
        if user.has_unreturned_ipads:
            flash(u'%s有未归换的iPad' % user.name, category='error')
            return redirect(url_for('manage.rental_rent_step_3', user_id=user_id, ipad_id=ipad_id, schedule_id=schedule_id))
        rental = Rental(user_id=user.id, ipad_id=ipad.id, schedule_id=schedule.id, rent_agent_id=current_user.id)
        db.session.add(rental)
        ipad.set_state(u'借出', battery_life=form.battery_life.data, modified_by=current_user._get_current_object())
        flash(u'iPad借出信息登记成功', category='success')
        return redirect(url_for('manage.rental'))
    return render_template('manage/rental_rent_step_3.html', user=user, ipad=ipad, schedule=schedule, form=form)


@manage.route('/rental/rent/step-2-lesson/<int:user_id>/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_2_lesson(user_id, schedule_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    schedule = Schedule.query.get_or_404(schedule_id)
    form = SelectLessonForm()
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_rent_step_3_lesson', user_id=user_id, lesson_id=form.lesson.data, schedule_id=schedule_id))
    return render_template('manage/rental_rent_step_2_lesson.html', user=user, schedule=schedule, form=form)


@manage.route('rental/rent/step-3-lesson/<int:user_id>/<int:lesson_id>/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_3_lesson(user_id, lesson_id, schedule_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    lesson = Lesson.query.get_or_404(lesson_id)
    schedule = Schedule.query.get_or_404(schedule_id)
    form = RentiPadByLessonForm(lesson=lesson)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_rent_step_4_lesson', user_id=user_id, lesson_id=lesson_id, ipad_id=form.ipad.data, schedule_id=schedule_id))
    return render_template('manage/rental_rent_step_3_lesson.html', user=user, lesson=lesson, schedule=schedule, form=form)


@manage.route('rental/rent/step-4-lesson/<int:user_id>/<int:lesson_id>/<int:ipad_id>/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_4_lesson(user_id, lesson_id, ipad_id, schedule_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    lesson = Lesson.query.get_or_404(lesson_id)
    ipad = iPad.query.get_or_404(ipad_id)
    if ipad.deleted:
        abort(404)
    schedule = Schedule.query.get_or_404(schedule_id)
    form = ConfirmiPadForm()
    if form.validate_on_submit():
        serial = form.serial.data
        if serial != ipad.serial:
            flash(u'iPad序列号信息有误', category='error')
            return redirect(url_for('manage.rental_rent_step_4_lesson', user_id=user_id, lesson_id=lesson_id, ipad_id=ipad_id, schedule_id=schedule_id))
        if ipad.state.name not in [u'待机', u'候补']:
            flash(u'序列号为%s的iPad处于“%s”状态，不能借出' % (ipad.serial, ipad.state.name), category='error')
            return redirect(url_for('manage.rental_rent_step_4_lesson', user_id=user_id, lesson_id=lesson_id, ipad_id=ipad_id, schedule_id=schedule_id))
        if user.has_unreturned_ipads:
            flash(u'%s有未归换的iPad' % user.name, category='error')
            return redirect(url_for('manage.rental_rent_step_4_lesson', user_id=user_id, lesson_id=lesson_id, ipad_id=ipad_id, schedule_id=schedule_id))
        rental = Rental(user_id=user.id, ipad_id=ipad.id, schedule_id=schedule.id, rent_agent_id=current_user.id)
        db.session.add(rental)
        ipad.set_state(u'借出', battery_life=form.battery_life.data, modified_by=current_user._get_current_object())
        flash(u'iPad借出信息登记成功', category='success')
        return redirect(url_for('manage.rental'))
    return render_template('manage/rental_rent_step_4_lesson.html', user=user, lesson=lesson, ipad=ipad, schedule=schedule, form=form)


@manage.route('/rental/rent/step-1-alt', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_1_alt():
    form = RentalEmailForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, deleted=False).first()
        if user is None:
            flash(u'邮箱不存在', category='error')
            return redirect(url_for('manage.rental_rent_step_1_alt'))
        return redirect(url_for('manage.rental_rent_step_2_alt', user_id=user.id))
    return render_template('manage/rental_rent_step_1_alt.html', form=form)


@manage.route('/rental/rent/step-2-alt/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_2_alt(user_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    form = RentiPadForm(user=user)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_rent_step_3_alt', user_id=user_id, ipad_id=form.ipad.data))
    return render_template('manage/rental_rent_step_2_alt.html', user=user, form=form)


@manage.route('/rental/rent/step-3-alt/<int:user_id>/<int:ipad_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_3_alt(user_id, ipad_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    ipad = iPad.query.get_or_404(ipad_id)
    if ipad.deleted:
        abort(404)
    schedule = Schedule.current_schedule(user.last_punch.section.lesson.type.name)
    if schedule is None:
        flash(u'目前没有开放的%s时段，无法借出iPad' % user.last_punch.section.lesson.type.name, category='error')
        return redirect(url_for('manage.rental'))
    form = ConfirmiPadForm()
    if form.validate_on_submit():
        serial = form.serial.data
        if serial != ipad.serial:
            flash(u'iPad序列号信息有误', category='error')
            return redirect(url_for('manage.rental_rent_step_3_alt', user_id=user_id, ipad_id=ipad_id))
        if ipad.state.name not in [u'待机', u'候补']:
            flash(u'序列号为%s的iPad处于“%s”状态，不能借出' % (ipad.serial, ipad.state.name), category='error')
            return redirect(url_for('manage.rental_rent_step_3_alt', user_id=user_id, ipad_id=ipad_id))
        if user.has_unreturned_ipads:
            flash(u'%s有未归换的iPad' % user.name, category='error')
            return redirect(url_for('manage.rental_rent_step_3_alt', user_id=user_id, ipad_id=ipad_id))
        rental = Rental(user_id=user.id, ipad_id=ipad.id, schedule_id=schedule.id, rent_agent_id=current_user.id, walk_in=True)
        db.session.add(rental)
        ipad.set_state(u'借出', battery_life=form.battery_life.data, modified_by=current_user._get_current_object())
        flash(u'iPad借出信息登记成功', category='success')
        return redirect(url_for('manage.rental'))
    return render_template('manage/rental_rent_step_3_alt.html', user=user, ipad=ipad, form=form)


@manage.route('/rental/rent/step-2-lesson-alt/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_2_lesson_alt(user_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    form = SelectLessonForm()
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_rent_step_3_lesson_alt', user_id=user_id, lesson_id=form.lesson.data))
    return render_template('manage/rental_rent_step_2_lesson_alt.html', user=user, form=form)


@manage.route('rental/rent/step-3-lesson-alt/<int:user_id>/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_3_lesson_alt(user_id, lesson_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    lesson = Lesson.query.get_or_404(lesson_id)
    form = RentiPadByLessonForm(lesson=lesson)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_rent_step_4_lesson_alt', user_id=user_id, lesson_id=lesson_id, ipad_id=form.ipad.data))
    return render_template('manage/rental_rent_step_3_lesson_alt.html', user=user, lesson=lesson, form=form)


@manage.route('rental/rent/step-4-lesson-alt/<int:user_id>/<int:lesson_id>/<int:ipad_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_4_lesson_alt(user_id, lesson_id, ipad_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    lesson = Lesson.query.get_or_404(lesson_id)
    ipad = iPad.query.get_or_404(ipad_id)
    if ipad.deleted:
        abort(404)
    schedule = Schedule.current_schedule(lesson.type.name)
    if schedule is None:
        flash(u'目前没有开放的%s时段，无法借出iPad' % lesson.type.name, category='error')
        return redirect(url_for('manage.rental'))
    form = ConfirmiPadForm()
    if form.validate_on_submit():
        serial = form.serial.data
        if serial != ipad.serial:
            flash(u'iPad序列号信息有误', category='error')
            return redirect(url_for('manage.rental_rent_step_4_lesson_alt', user_id=user_id, lesson_id=lesson_id, ipad_id=ipad_id))
        if ipad.state.name not in [u'待机', u'候补']:
            flash(u'序列号为%s的iPad处于“%s”状态，不能借出' % (ipad.serial, ipad.state.name), category='error')
            return redirect(url_for('manage.rental_rent_step_4_lesson_alt', user_id=user_id, lesson_id=lesson_id, ipad_id=ipad_id))
        if user.has_unreturned_ipads:
            flash(u'%s有未归换的iPad' % user.name, category='error')
            return redirect(url_for('manage.rental_rent_step_4_lesson_alt', user_id=user_id, lesson_id=lesson_id, ipad_id=ipad_id))
        rental = Rental(user_id=user.id, ipad_id=ipad.id, schedule_id=schedule.id, rent_agent_id=current_user.id, walk_in=True)
        db.session.add(rental)
        ipad.set_state(u'借出', battery_life=form.battery_life.data, modified_by=current_user._get_current_object())
        flash(u'iPad借出信息登记成功', category='success')
        return redirect(url_for('manage.rental'))
    return render_template('manage/rental_rent_step_4_lesson_alt.html', user=user, lesson=lesson, ipad=ipad, form=form)


@manage.route('/rental/return/step-1', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_return_step_1():
    form = iPadSerialForm()
    if form.validate_on_submit():
        serial = form.serial.data
        ipad = iPad.query.filter_by(serial=serial).first()
        if ipad is None:
            flash(u'不存在序列号为%s的iPad' % serial, category='error')
            return redirect(url_for('manage.rental_return_step_1'))
        if ipad.state.name != u'借出':
            flash(u'序列号为%s的iPad处于%s状态，尚未借出' % (serial, ipad.state.name), category='error')
            return redirect(url_for('manage.rental_return_step_1'))
        rental = Rental.query.filter_by(ipad_id=ipad.id, returned=False).first()
        if rental is None:
            flash(u'没有序列号为%s的iPad的借阅记录' % serial, category='error')
            return redirect(url_for('manage.rental_return_step_1'))
        if not form.root.data:
            rental.set_returned(return_agent_id=current_user.id, ipad_state=u'维护')
            db.session.commit()
            for user in User.query.all():
                if user.can(u'管理iPad设备'):
                    send_email(user.email, u'序列号为%s的iPad处于维护状态' % serial, 'manage/mail/maintain_ipad', ipad=ipad, time=datetime.utcnow(), manager=current_user)
            flash(u'已回收序列号为%s的iPad，并设为维护状态' % serial, category='warning')
            return redirect(url_for('manage.rental_return_step_2', user_id=rental.user_id))
        if not form.battery.data:
            rental.set_returned(return_agent_id=current_user.id, ipad_state=u'充电')
            flash(u'已回收序列号为%s的iPad，并设为充电状态' % serial, category='warning')
            return redirect(url_for('manage.rental_return_step_2', user_id=rental.user_id))
        rental.set_returned(return_agent_id=current_user.id)
        flash(u'已回收序列号为%s的iPad' % serial, category='success')
        return redirect(url_for('manage.rental_return_step_2', user_id=rental.user_id))
    return render_template('manage/rental_return_step_1.html', form=form)


@manage.route('/rental/return/step-2/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_return_step_2(user_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    form = PunchLessonForm(user=user)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_return_step_3', user_id=user_id, lesson_id=form.lesson.data))
    return render_template('manage/rental_return_step_2.html', user=user, form=form)


@manage.route('/rental/return/step-3/<int:user_id>/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_return_step_3(user_id, lesson_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    lesson = Lesson.query.get_or_404(lesson_id)
    form = PunchSectionForm(user=user, lesson=lesson)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_return_step_4', user_id=user_id, section_id=form.section.data))
    return render_template('manage/rental_return_step_3.html', user=user, lesson=lesson, form=form)


@manage.route('/rental/return/step-4/<int:user_id>/<int:section_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_return_step_4(user_id, section_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    section = Section.query.get_or_404(section_id)
    form = ConfirmPunchForm()
    if form.validate_on_submit():
        user.punch(section=section)
        flash(u'已保存%s的进度信息为：%s - %s - %s' % (user.name, section.lesson.type.name, section.lesson.name, section.name), category='success')
        return redirect(url_for('manage.rental'))
    return render_template('manage/rental_return_step_4.html', user=user, section=section, form=form)


@manage.route('/rental/return/step-1-alt', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_return_step_1_alt():
    form = RentalEmailForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, deleted=False).first()
        if user is None:
            flash(u'邮箱不存在', category='error')
            return redirect(url_for('manage.rental_return_step_1_alt'))
        return redirect(url_for('manage.rental_return_step_2_alt', user_id=user.id))
    return render_template('manage/rental_return_step_1_alt.html', form=form)


@manage.route('/rental/return/step-2-alt/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_return_step_2_alt(user_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    form = PunchLessonForm(user=user)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_return_step_3_alt', user_id=user_id, lesson_id=form.lesson.data))
    return render_template('manage/rental_return_step_2_alt.html', user=user, form=form)


@manage.route('/rental/return/step-3-alt/<int:user_id>/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_return_step_3_alt(user_id, lesson_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    lesson = Lesson.query.get_or_404(lesson_id)
    form = PunchSectionForm(user=user, lesson=lesson)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_return_step_4_alt', user_id=user_id, section_id=form.section.data))
    return render_template('manage/rental_return_step_3_alt.html', user=user, lesson=lesson, form=form)


@manage.route('/rental/return/step-4-alt/<int:user_id>/<int:section_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_return_step_4_alt(user_id, section_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    section = Section.query.get_or_404(section_id)
    form = ConfirmPunchForm()
    if form.validate_on_submit():
        user.punch(section=section)
        flash(u'已保存%s的进度信息为：%s - %s - %s' % (user.name, section.lesson.type.name, section.lesson.name, section.name), category='success')
        return redirect(url_for('manage.rental'))
    return render_template('manage/rental_return_step_4_alt.html', user=user, section=section, form=form)


@manage.route('/rental/exchange/step-1/<int:rental_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_exchange_step_1(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    if rental.returned:
        flash(u'iPad已处于归还状态', category='error')
        return redirect(url_for('manage.rental'))
    form = iPadSerialForm()
    if form.validate_on_submit():
        serial = form.serial.data
        ipad = iPad.query.filter_by(serial=serial).first()
        if ipad is None:
            flash(u'不存在序列号为%s的iPad' % serial, category='error')
            return redirect(url_for('manage.rental_exchange_step_1', rental_id=rental_id, next=request.args.get('next')))
        if ipad.state.name != u'借出':
            flash(u'序列号为%s的iPad处于%s状态，尚未借出' % (serial, ipad.state.name), category='error')
            return redirect(url_for('manage.rental_exchange_step_1', rental_id=rental_id, next=request.args.get('next')))
        if not form.root.data:
            rental.set_returned(return_agent_id=current_user.id, ipad_state=u'维护')
            db.session.commit()
            for user in User.query.all():
                if user.can(u'管理iPad设备'):
                    send_email(user.email, u'序列号为%s的iPad处于维护状态' % serial, 'manage/mail/maintain_ipad', ipad=ipad, time=datetime.utcnow(), manager=current_user)
            flash(u'已回收序列号为%s的iPad，并设为维护状态' % serial, category='warning')
            return redirect(url_for('manage.rental_exchange_step_2', rental_id=rental_id, next=request.args.get('next')))
        if not form.battery.data:
            rental.set_returned(return_agent_id=current_user.id, ipad_state=u'充电')
            flash(u'已回收序列号为%s的iPad，并设为充电状态' % serial, category='warning')
            return redirect(url_for('manage.rental_exchange_step_2', rental_id=rental_id, next=request.args.get('next')))
        rental.set_returned(return_agent_id=current_user.id)
        flash(u'已回收序列号为%s的iPad' % serial, category='success')
        return redirect(url_for('manage.rental_exchange_step_2', rental_id=rental_id, next=request.args.get('next')))
    return render_template('manage/rental_exchange_step_1.html', rental=rental, form=form)


@manage.route('/rental/exchange/step-2/<int:rental_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_exchange_step_2(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    if not rental.returned:
        flash(u'iPad尚未归还', category='error')
        return redirect(url_for('manage.rental_exchange_step_1', rental_id=rental_id, next=request.args.get('next')))
    user = User.query.get_or_404(rental.user_id)
    if user.deleted:
        abort(404)
    form = PunchLessonForm(user=user)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_exchange_step_3', rental_id=rental_id, lesson_id=form.lesson.data, next=request.args.get('next')))
    return render_template('manage/rental_exchange_step_2.html', rental=rental, form=form)


@manage.route('/rental/exchange/step-3/<int:rental_id>/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_exchange_step_3(rental_id, lesson_id):
    rental = Rental.query.get_or_404(rental_id)
    if not rental.returned:
        flash(u'iPad尚未归还', category='error')
        return redirect(url_for('manage.rental_exchange_step_1', rental_id=rental_id, next=request.args.get('next')))
    user = User.query.get_or_404(rental.user_id)
    if user.deleted:
        abort(404)
    lesson = Lesson.query.get_or_404(lesson_id)
    form = PunchSectionForm(user=user, lesson=lesson)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_exchange_step_4', rental_id=rental_id, section_id=form.section.data, next=request.args.get('next')))
    return render_template('manage/rental_exchange_step_3.html', rental=rental, lesson=lesson, form=form)


@manage.route('/rental/exchange/step-4/<int:rental_id>/<int:section_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_exchange_step_4(rental_id, section_id):
    rental = Rental.query.get_or_404(rental_id)
    if not rental.returned:
        flash(u'iPad尚未归还', category='error')
        return redirect(url_for('manage.rental_exchange_step_1', rental_id=rental_id, next=request.args.get('next')))
    user = User.query.get_or_404(rental.user_id)
    if user.deleted:
        abort(404)
    section = Section.query.get_or_404(section_id)
    form = ConfirmPunchForm()
    if form.validate_on_submit():
        user.punch(section=section)
        flash(u'已保存%s的进度信息为：%s - %s - %s' % (user.name, section.lesson.type.name, section.lesson.name, section.name), category='success')
        return redirect(url_for('manage.rental_exchange_step_5', rental_id=rental_id, next=request.args.get('next')))
    return render_template('manage/rental_exchange_step_4.html', rental=rental, section=section, form=form)


@manage.route('/rental/exchange/step-5/<int:rental_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_exchange_step_5(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    if not rental.returned:
        flash(u'iPad尚未归还', category='error')
        return redirect(url_for('manage.rental_exchange_step_1', rental_id=rental_id, next=request.args.get('next')))
    user = User.query.get_or_404(rental.user_id)
    if user.deleted:
        abort(404)
    form = RentiPadForm(user=user)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_exchange_step_6', rental_id=rental_id, ipad_id=form.ipad.data, next=request.args.get('next')))
    return render_template('manage/rental_exchange_step_5.html', rental=rental, form=form)


@manage.route('/rental/exchange/step-6/<int:rental_id>/<int:ipad_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_exchange_step_6(rental_id, ipad_id):
    rental = Rental.query.get_or_404(rental_id)
    if not rental.returned:
        flash(u'iPad尚未归还', category='error')
        return redirect(url_for('manage.rental_exchange_step_1', rental_id=rental_id, next=request.args.get('next')))
    user = User.query.get_or_404(rental.user_id)
    if user.deleted:
        abort(404)
    ipad = iPad.query.get_or_404(ipad_id)
    if ipad.deleted:
        abort(404)
    schedule = Schedule.query.get_or_404(rental.schedule_id)
    form = ConfirmiPadForm()
    if form.validate_on_submit():
        serial = form.serial.data
        if serial != ipad.serial:
            flash(u'iPad序列号信息有误', category='error')
            return redirect(url_for('manage.rental_exchange_step_6', rental_id=rental_id, ipad_id=ipad_id, next=request.args.get('next')))
        if ipad.state.name not in [u'待机', u'候补']:
            flash(u'序列号为%s的iPad处于“%s”状态，不能借出' % (ipad.serial, ipad.state.name), category='error')
            return redirect(url_for('manage.rental_exchange_step_6', rental_id=rental_id, ipad_id=ipad_id, next=request.args.get('next')))
        if user.has_unreturned_ipads:
            flash(u'%s有未归换的iPad' % user.name, category='error')
            return redirect(url_for('manage.rental_exchange_step_6', rental_id=rental_id, ipad_id=ipad_id, next=request.args.get('next')))
        new_rental = Rental(user_id=user.id, ipad_id=ipad.id, schedule_id=schedule.id, rent_agent_id=current_user.id)
        db.session.add(new_rental)
        ipad.set_state(u'借出', battery_life=form.battery_life.data, modified_by=current_user._get_current_object())
        flash(u'iPad借出信息登记成功', category='success')
        return redirect(request.args.get('next') or url_for('manage.rental'))
    return render_template('manage/rental_exchange_step_6.html', rental=rental, ipad=ipad, form=form)


@manage.route('/rental/exchange/step-5-lesson/<int:rental_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_exchange_step_5_lesson(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    if not rental.returned:
        flash(u'iPad尚未归还', category='error')
        return redirect(url_for('manage.rental_exchange_step_1', rental_id=rental_id, next=request.args.get('next')))
    user = User.query.get_or_404(rental.user_id)
    if user.deleted:
        abort(404)
    form = SelectLessonForm()
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_exchange_step_6_lesson', rental_id=rental_id, lesson_id=form.lesson.data, next=request.args.get('next')))
    return render_template('manage/rental_exchange_step_5_lesson.html', rental=rental, form=form)


@manage.route('rental/exchange/step-6-lesson/<int:rental_id>/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_exchange_step_6_lesson(rental_id, lesson_id):
    rental = Rental.query.get_or_404(rental_id)
    if not rental.returned:
        flash(u'iPad尚未归还', category='error')
        return redirect(url_for('manage.rental_exchange_step_1', rental_id=rental_id, next=request.args.get('next')))
    user = User.query.get_or_404(rental.user_id)
    if user.deleted:
        abort(404)
    lesson = Lesson.query.get_or_404(lesson_id)
    form = RentiPadByLessonForm(lesson=lesson)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_exchange_step_7_lesson', rental_id=rental_id, lesson_id=lesson_id, ipad_id=form.ipad.data, next=request.args.get('next')))
    return render_template('manage/rental_exchange_step_6_lesson.html', rental=rental, lesson=lesson, form=form)


@manage.route('rental/exchange/step-7-lesson/<int:rental_id>/<int:lesson_id>/<int:ipad_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_exchange_step_7_lesson(rental_id, lesson_id, ipad_id):
    rental = Rental.query.get_or_404(rental_id)
    if not rental.returned:
        flash(u'iPad尚未归还', category='error')
        return redirect(url_for('manage.rental_exchange_step_1', rental_id=rental_id, next=request.args.get('next')))
    user = User.query.get_or_404(rental.user_id)
    if user.deleted:
        abort(404)
    lesson = Lesson.query.get_or_404(lesson_id)
    ipad = iPad.query.get_or_404(ipad_id)
    if ipad.deleted:
        abort(404)
    schedule = Schedule.query.get_or_404(rental.schedule_id)
    form = ConfirmiPadForm()
    if form.validate_on_submit():
        serial = form.serial.data
        if serial != ipad.serial:
            flash(u'iPad序列号信息有误', category='error')
            return redirect(url_for('manage.rental_exchange_step_7_lesson', rental_id=rental_id, lesson_id=lesson_id, ipad_id=ipad_id, next=request.args.get('next')))
        if ipad.state.name not in [u'待机', u'候补']:
            flash(u'序列号为%s的iPad处于“%s”状态，不能借出' % (ipad.serial, ipad.state.name), category='error')
            return redirect(url_for('manage.rental_exchange_step_7_lesson', rental_id=rental_id, lesson_id=lesson_id, ipad_id=ipad_id, next=request.args.get('next')))
        if user.has_unreturned_ipads:
            flash(u'%s有未归换的iPad' % user.name, category='error')
            return redirect(url_for('manage.rental_exchange_step_7_lesson', rental_id=rental_id, lesson_id=lesson_id, ipad_id=ipad_id, next=request.args.get('next')))
        new_rental = Rental(user_id=user.id, ipad_id=ipad.id, schedule_id=schedule.id, rent_agent_id=current_user.id)
        db.session.add(new_rental)
        ipad.set_state(u'借出', battery_life=form.battery_life.data, modified_by=current_user._get_current_object())
        flash(u'iPad借出信息登记成功', category='success')
        return redirect(request.args.get('next') or url_for('manage.rental'))
    return render_template('manage/rental_exchange_step_7_lesson.html', rental=rental, lesson=lesson, ipad=ipad, form=form)


@manage.route('/punch/edit/step-1/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理学习进度')
def edit_punch_step_1(user_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    form = EditPunchLessonForm()
    if form.validate_on_submit():
        return redirect(url_for('manage.edit_punch_step_2', user_id=user_id, lesson_id=form.lesson.data, next=request.args.get('next')))
    form.lesson.data = user.last_punch.section.lesson_id
    return render_template('manage/edit_punch_step_1.html', user=user, form=form)


@manage.route('/punch/edit/step-2/<int:user_id>/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理学习进度')
def edit_punch_step_2(user_id, lesson_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    lesson = Lesson.query.get_or_404(lesson_id)
    form = EditPunchSectionForm(lesson=lesson)
    if form.validate_on_submit():
        return redirect(url_for('manage.edit_punch_step_3', user_id=user_id, section_id=form.section.data, next=request.args.get('next')))
    return render_template('manage/edit_punch_step_2.html', user=user, lesson=lesson, form=form)


@manage.route('/punch/edit/step-3/<int:user_id>/<int:section_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理学习进度')
def edit_punch_step_3(user_id, section_id):
    user = User.query.get_or_404(user_id)
    if user.deleted:
        abort(404)
    section = Section.query.get_or_404(section_id)
    form = ConfirmPunchForm()
    if form.validate_on_submit():
        user.punch(section=section)
        flash(u'已保存%s的进度信息为：%s - %s - %s' % (user.name, section.lesson.type.name, section.lesson.name, section.name), category='success')
        return redirect(request.args.get('next') or url_for('manage.find_user'))
    return render_template('manage/edit_punch_step_3.html', user=user, section=section, form=form)


@manage.route('/period', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理预约时段')
def period():
    form = NewPeriodForm()
    if form.validate_on_submit():
        start_time = time(*[int(x) for x in form.start_time.data.split(':')])
        end_time = time(*[int(x) for x in form.end_time.data.split(':')])
        if start_time >= end_time:
            flash(u'无法添加时段模板：%s，时间设置有误' % form.name.data, category='error')
            return redirect(url_for('manage.period'))
        period = Period(name=form.name.data, start_time=start_time, end_time=end_time, type_id=int(form.period_type.data), show=form.show.data, modified_by_id=current_user.id)
        db.session.add(period)
        flash(u'已添加时段模板：%s' % form.name.data, category='success')
        return redirect(url_for('manage.period'))
    page = request.args.get('page', 1, type=int)
    query = Period.query.filter_by(deleted=False)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    periods = pagination.items
    return render_template('manage/period.html', form=form, periods=periods, pagination=pagination)


@manage.route('/period/flip-show/<int:id>')
@login_required
@permission_required(u'管理预约时段')
def flip_period_show(id):
    period = Period.query.get_or_404(id)
    if period.deleted:
        abort(404)
    period.flip_show(modified_by=current_user._get_current_object())
    if period.show:
        flash(u'%s的可选状态改为：可选' % period.alias, category='success')
    else:
        flash(u'%s的可选状态改为：不可选' % period.alias, category='success')
    return redirect(request.args.get('next') or url_for('manage.period'))


@manage.route('/period/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理预约时段')
def edit_period(id):
    period = Period.query.get_or_404(id)
    if period.deleted:
        abort(404)
    form = EditPeriodForm()
    if form.validate_on_submit():
        start_time = time(*[int(x) for x in form.start_time.data.split(':')])
        end_time = time(*[int(x) for x in form.end_time.data.split(':')])
        if start_time >= end_time:
            flash(u'无法更新时段模板：%s，时间设置有误' % form.name.data, category='error')
            return redirect(url_for('manage.edit_period', id=period.id, next=request.args.get('next')))
        period.name = form.name.data
        period.start_time = start_time
        period.end_time = end_time
        period.type_id = int(form.period_type.data)
        period.show = form.show.data
        period.modified_at = datetime.utcnow()
        period.modified_by_id = current_user.id
        db.session.add(period)
        flash(u'已更新时段模板：%s' % form.name.data, category='success')
        return redirect(request.args.get('next') or url_for('manage.period'))
    form.name.data = period.name
    form.start_time.data = period.start_time.strftime(u'%H:%M')
    form.end_time.data = period.end_time.strftime(u'%H:%M')
    form.period_type.data = unicode(period.type_id)
    form.show.data = period.show
    return render_template('manage/edit_period.html', form=form, period=period)


@manage.route('/period/delete/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理预约时段')
def delete_period(id):
    period = Period.query.get_or_404(id)
    if period.deleted:
        abort(404)
    form = DeletePeriodForm()
    if form.validate_on_submit():
        period.safe_delete(modified_by=current_user._get_current_object())
        flash(u'已删除时段模板：%s' % period.name, category='success')
        return redirect(request.args.get('next') or url_for('manage.period'))
    return render_template('manage/delete_period.html', form=form, period=period)


@manage.route('/schedule', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理预约时段')
def schedule():
    form = NewScheduleForm()
    if form.validate_on_submit():
        day = date(*[int(x) for x in form.date.data.split('-')])
        for period_id in form.period.data:
            schedule = Schedule.query.filter_by(date=day, period_id=int(period_id)).first()
            if schedule:
                flash(u'该时段已存在：%s，%s时段：%s - %s' % (schedule.date, schedule.period.type.name, schedule.period.start_time, schedule.period.end_time), category='warning')
            else:
                period = Period.query.get_or_404(int(period_id))
                if period.deleted:
                    abort(404)
                if datetime(day.year, day.month, day.day, period.start_time.hour, period.start_time.minute) < datetime.now():
                    flash(u'该时段已过期：%s，%s时段：%s - %s' % (day, period.type.name, period.start_time, period.end_time), category='error')
                else:
                    schedule = Schedule(date=day, period_id=int(period_id), quota=form.quota.data, available=form.publish_now.data, modified_by_id=current_user.id)
                    db.session.add(schedule)
                    db.session.commit()
                    flash(u'添加时段：%s，%s时段：%s - %s' % (schedule.date, schedule.period.type.name, schedule.period.start_time, schedule.period.end_time), category='success')
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
            .filter(Schedule.date == date.today())\
            .order_by(Schedule.period_id.asc())
    if show_future_schedule:
        query = Schedule.query\
            .filter(Schedule.date > date.today())\
            .order_by(Schedule.date.asc())\
            .order_by(Schedule.period_id.asc())
    if show_history_schedule:
        query = Schedule.query\
            .filter(Schedule.date < date.today())\
            .order_by(Schedule.date.desc())\
            .order_by(Schedule.period_id.asc())
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    schedules = pagination.items
    return render_template('manage/schedule.html', form=form, schedules=schedules, show_today_schedule=show_today_schedule, show_future_schedule=show_future_schedule, show_history_schedule=show_history_schedule, pagination=pagination)


@manage.route('/schedule/today')
@login_required
@permission_required(u'管理预约时段')
def today_schedule():
    resp = make_response(redirect(url_for('manage.schedule')))
    resp.set_cookie('show_today_schedule', '1', max_age=30*24*60*60)
    resp.set_cookie('show_future_schedule', '', max_age=30*24*60*60)
    resp.set_cookie('show_history_schedule', '', max_age=30*24*60*60)
    return resp


@manage.route('/schedule/future')
@login_required
@permission_required(u'管理预约时段')
def future_schedule():
    resp = make_response(redirect(url_for('manage.schedule')))
    resp.set_cookie('show_today_schedule', '', max_age=30*24*60*60)
    resp.set_cookie('show_future_schedule', '1', max_age=30*24*60*60)
    resp.set_cookie('show_history_schedule', '', max_age=30*24*60*60)
    return resp


@manage.route('/schedule/history')
@login_required
@permission_required(u'管理预约时段')
def history_schedule():
    resp = make_response(redirect(url_for('manage.schedule')))
    resp.set_cookie('show_today_schedule', '', max_age=30*24*60*60)
    resp.set_cookie('show_future_schedule', '', max_age=30*24*60*60)
    resp.set_cookie('show_history_schedule', '1', max_age=30*24*60*60)
    return resp


@manage.route('/schedule/publish/<int:id>')
@login_required
@permission_required(u'管理预约时段')
def publish_schedule(id):
    schedule = Schedule.query.get_or_404(id)
    if schedule.out_of_date:
        flash(u'所选时段已经过期', category='error')
        return redirect(request.args.get('next') or url_for('manage.schedule'))
    if schedule.available:
        flash(u'所选时段已经发布', category='warning')
        return redirect(request.args.get('next') or url_for('manage.schedule'))
    schedule.publish(modified_by=current_user._get_current_object())
    flash(u'发布成功！', category='success')
    return redirect(request.args.get('next') or url_for('manage.schedule'))


@manage.route('/schedule/retract/<int:id>')
@login_required
@permission_required(u'管理预约时段')
def retract_schedule(id):
    schedule = Schedule.query.get_or_404(id)
    if schedule.out_of_date:
        flash(u'所选时段已经过期', category='error')
        return redirect(request.args.get('next') or url_for('manage.schedule'))
    if not schedule.available:
        flash(u'所选时段尚未发布', category='warning')
        return redirect(request.args.get('next') or url_for('manage.schedule'))
    schedule.retract(modified_by=current_user._get_current_object())
    flash(u'撤销成功！', category='success')
    return redirect(request.args.get('next') or url_for('manage.schedule'))


@manage.route('/schedule/increase-quota/<int:id>')
@login_required
@permission_required(u'管理预约时段')
def increase_schedule_quota(id):
    schedule = Schedule.query.get_or_404(id)
    if schedule.out_of_date:
        flash(u'所选时段已经过期', category='error')
        return redirect(request.args.get('next') or url_for('manage.schedule'))
    candidate = schedule.increase_quota(modified_by=current_user._get_current_object())
    if candidate:
        booking = Booking.query.filter_by(user_id=candidate.id, schedule_id=schedule_id).first()
        send_email(candidate.email, u'您已成功预约%s的%s课程' % (schedule.date, schedule.period.alias), 'book/mail/booking', user=candidate, schedule=schedule, booking=booking)
        booked_ipads_quantity = schedule.booked_ipads_quantity(lesson=candidate.last_punch.section.lesson)
        available_ipads_quantity = candidate.last_punch.section.lesson.available_ipads.count()
        if booked_ipads_quantity >= available_ipads_quantity:
            for manager in User.query.all():
                if manager.can(u'管理iPad设备'):
                    send_email(manager.email, u'含有课程“%s”的iPad资源紧张' % candidate.last_punch.section.lesson.name, 'book/mail/short_of_ipad', schedule=schedule, lesson=candidate.last_punch.section.lesson, booked_ipads_quantity=booked_ipads_quantity, available_ipads_quantity=available_ipads_quantity)
    flash(u'所选时段名额+1', category='success')
    return redirect(request.args.get('next') or url_for('manage.schedule'))


@manage.route('/schedule/decrease-quota/<int:id>')
@login_required
@permission_required(u'管理预约时段')
def decrease_schedule_quota(id):
    schedule = Schedule.query.get_or_404(id)
    if schedule.out_of_date:
        flash(u'所选时段已经过期', category='error')
        return redirect(request.args.get('next') or url_for('manage.schedule'))
    if schedule.quota == 0:
        flash(u'所选时段名额已经为0', category='error')
        return redirect(request.args.get('next') or url_for('manage.schedule'))
    if schedule.quota <= schedule.occupied_quota:
        flash(u'所选时段名额不可少于预约人数', category='error')
        return redirect(request.args.get('next') or url_for('manage.schedule'))
    schedule.decrease_quota(modified_by=current_user._get_current_object())
    flash(u'所选时段名额-1', category='success')
    return redirect(request.args.get('next') or url_for('manage.schedule'))


@manage.route('/ipad', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理')
def ipad():
    form = NewiPadForm()
    if form.validate_on_submit() and current_user.can(u'管理iPad设备'):
        serial = form.serial.data.upper()
        room_id = int(form.room.data)
        if room_id == 0:
            room_id = None
        ipad = iPad.query.filter_by(serial=serial).first()
        if ipad:
            flash(u'序列号为%s的iPad已存在' % serial, category='error')
            return redirect(url_for('manage.ipad'))
        ipad = iPad(serial=serial, alias=form.alias.data, capacity_id=int(form.capacity.data), room_id=room_id, state_id=int(form.state.data), video_playback=timedelta(hours=form.video_playback.data), modified_by_id=current_user.id)
        db.session.add(ipad)
        db.session.commit()
        for lesson_id in form.vb_lessons.data + form.y_gre_lessons.data:
            lesson = Lesson.query.get(int(lesson_id))
            ipad.add_lesson(lesson)
        iPadContentJSON.mark_out_of_date()
        flash(u'成功添加序列号为%s的iPad' % serial, category='success')
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
    show_ipad_all = True
    show_ipad_maintain = False
    show_ipad_charge = False
    show_ipad_1103 = False
    show_ipad_1707 = False
    show_ipad_others = False
    if current_user.is_authenticated:
        show_ipad_all = bool(request.cookies.get('show_ipad_all', '1'))
        show_ipad_maintain = bool(request.cookies.get('show_ipad_maintain', ''))
        show_ipad_charge = bool(request.cookies.get('show_ipad_charge', ''))
        show_ipad_1103 = bool(request.cookies.get('show_ipad_1103', ''))
        show_ipad_1707 = bool(request.cookies.get('show_ipad_1707', ''))
        show_ipad_others = bool(request.cookies.get('show_ipad_others', ''))
    if show_ipad_all:
        query = iPad.query\
            .filter_by(deleted=False)
    if show_ipad_maintain:
        query = iPad.query\
            .join(iPadState, iPadState.id == iPad.state_id)\
            .filter(iPadState.name == u'维护')\
            .filter(iPad.deleted == False)
    if show_ipad_charge:
        query = iPad.query\
            .join(iPadState, iPadState.id == iPad.state_id)\
            .filter(iPadState.name == u'充电')\
            .filter(iPad.deleted == False)
    if show_ipad_1103:
        query = iPad.query\
            .join(Room, Room.id == iPad.room_id)\
            .filter(Room.name == u'1103')\
            .filter(iPad.deleted == False)
    if show_ipad_1707:
        query = iPad.query\
            .join(Room, Room.id == iPad.room_id)\
            .filter(Room.name == u'1707')\
            .filter(iPad.deleted == False)
    if show_ipad_others:
        query = iPad.query\
            .filter_by(room_id=None, deleted=False)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    ipads = pagination.items
    return render_template('manage/ipad.html', form=form, ipads=ipads, maintain_num=maintain_num, charge_num=charge_num, show_ipad_all=show_ipad_all, show_ipad_maintain=show_ipad_maintain, show_ipad_charge=show_ipad_charge, show_ipad_1103=show_ipad_1103, show_ipad_1707=show_ipad_1707, show_ipad_others=show_ipad_others, pagination=pagination)


@manage.route('/ipad/all')
@login_required
@permission_required(u'管理')
def all_ipads():
    resp = make_response(redirect(url_for('manage.ipad')))
    resp.set_cookie('show_ipad_all', '1', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_maintain', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_charge', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_1103', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_1707', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_others', '', max_age=30*24*60*60)
    return resp


@manage.route('/ipad/maintain')
@login_required
@permission_required(u'管理')
def maintain_ipads():
    resp = make_response(redirect(url_for('manage.ipad')))
    resp.set_cookie('show_ipad_all', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_maintain', '1', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_charge', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_1103', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_1707', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_others', '', max_age=30*24*60*60)
    return resp


@manage.route('/ipad/charge')
@login_required
@permission_required(u'管理')
def charge_ipads():
    resp = make_response(redirect(url_for('manage.ipad')))
    resp.set_cookie('show_ipad_all', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_maintain', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_charge', '1', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_1103', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_1707', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_others', '', max_age=30*24*60*60)
    return resp


@manage.route('/ipad/1103')
@login_required
@permission_required(u'管理')
def room_1103_ipads():
    resp = make_response(redirect(url_for('manage.ipad')))
    resp.set_cookie('show_ipad_all', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_maintain', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_charge', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_1103', '1', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_1707', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_others', '', max_age=30*24*60*60)
    return resp


@manage.route('/ipad/1707')
@login_required
@permission_required(u'管理')
def room_1707_ipads():
    resp = make_response(redirect(url_for('manage.ipad')))
    resp.set_cookie('show_ipad_all', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_maintain', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_charge', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_1103', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_1707', '1', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_others', '', max_age=30*24*60*60)
    return resp


@manage.route('/ipad/others')
@login_required
@permission_required(u'管理')
def other_ipads():
    resp = make_response(redirect(url_for('manage.ipad')))
    resp.set_cookie('show_ipad_all', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_maintain', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_charge', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_1103', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_1707', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_others', '1', max_age=30*24*60*60)
    return resp


@manage.route('/ipad/set-state/standby/<int:id>')
@login_required
@permission_required(u'管理')
def set_ipad_state_standby(id):
    ipad = iPad.query.get_or_404(id)
    if ipad.state.name == u'借出':
        flash(u'iPad“%s”为借出状态，请先回收该iPad', category='error')
        return redirect(request.args.get('next') or url_for('manage.ipad'))
    ipad.set_state(u'待机', modified_by=current_user._get_current_object())
    flash(u'修改iPad“%s”的状态为：待机' % ipad.alias, category='success')
    return redirect(request.args.get('next') or url_for('manage.ipad'))


@manage.route('/ipad/set-state/candidate/<int:id>')
@login_required
@permission_required(u'管理iPad设备')
def set_ipad_state_candidate(id):
    ipad = iPad.query.get_or_404(id)
    if ipad.state.name == u'借出':
        flash(u'iPad“%s”为借出状态，请先回收该iPad', category='error')
        return redirect(request.args.get('next') or url_for('manage.ipad'))
    ipad.set_state(u'候补', modified_by=current_user._get_current_object())
    flash(u'修改iPad“%s”的状态为：候补' % ipad.alias, category='success')
    return redirect(request.args.get('next') or url_for('manage.ipad'))


@manage.route('/ipad/set-state/maintain/<int:id>')
@login_required
@permission_required(u'管理')
def set_ipad_state_maintain(id):
    ipad = iPad.query.get_or_404(id)
    if ipad.state.name == u'借出':
        flash(u'iPad“%s”为借出状态，请先回收该iPad', category='error')
        return redirect(request.args.get('next') or url_for('manage.ipad'))
    ipad.set_state(u'维护', modified_by=current_user._get_current_object())
    db.session.commit()
    for user in User.query.all():
        if user.can(u'管理iPad设备'):
            send_email(user.email, u'序列号为%s的iPad处于维护状态' % ipad.serial, 'manage/mail/maintain_ipad', ipad=ipad, time=datetime.utcnow(), manager=current_user)
    flash(u'修改iPad“%s”的状态为：维护' % ipad.alias, category='success')
    return redirect(request.args.get('next') or url_for('manage.ipad'))


@manage.route('/ipad/set-state/charge/<int:id>')
@login_required
@permission_required(u'管理')
def set_ipad_state_charge(id):
    ipad = iPad.query.get_or_404(id)
    if ipad.state.name == u'借出':
        flash(u'iPad“%s”为借出状态，请先回收该iPad', category='error')
        return redirect(request.args.get('next') or url_for('manage.ipad'))
    ipad.set_state(u'充电', modified_by=current_user._get_current_object())
    flash(u'修改iPad“%s”的状态为：充电' % ipad.alias, category='success')
    return redirect(request.args.get('next') or url_for('manage.ipad'))


@manage.route('/ipad/set-state/obsolete/<int:id>')
@login_required
@permission_required(u'管理iPad设备')
def set_ipad_state_obsolete(id):
    ipad = iPad.query.get_or_404(id)
    if ipad.state.name == u'借出':
        flash(u'iPad“%s”为借出状态，请先回收该iPad', category='error')
        return redirect(request.args.get('next') or url_for('manage.ipad'))
    ipad.set_state(u'退役', modified_by=current_user._get_current_object())
    flash(u'修改iPad“%s”的状态为：退役' % ipad.alias, category='success')
    return redirect(request.args.get('next') or url_for('manage.ipad'))


@manage.route('/ipad/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad设备')
def edit_ipad(id):
    ipad = iPad.query.get_or_404(id)
    if ipad.deleted:
        abort(404)
    form = EditiPadForm(ipad=ipad)
    if form.validate_on_submit():
        ipad.alias = form.alias.data
        ipad.serial = form.serial.data.upper()
        ipad.capacity_id = form.capacity.data
        if int(form.room.data) == 0:
            ipad.room_id = None
        else:
            ipad.room_id = int(form.room.data)
        ipad.state_id = int(form.state.data)
        ipad.video_playback = timedelta(hours=form.video_playback.data)
        ipad.modified_at = datetime.utcnow()
        ipad.modified_by_id = current_user.id
        db.session.add(ipad)
        db.session.commit()
        for ipad_content in ipad.contents:
            ipad.remove_lesson(ipad_content.lesson)
        for lesson_id in form.vb_lessons.data + form.y_gre_lessons.data:
            lesson = Lesson.query.get(int(lesson_id))
            ipad.add_lesson(lesson)
        iPadContentJSON.mark_out_of_date()
        flash(u'iPad信息已更新', category='success')
        return redirect(request.args.get('next') or url_for('manage.ipad'))
    form.alias.data = ipad.alias
    form.serial.data = ipad.serial
    form.capacity.data = unicode(ipad.capacity_id)
    form.room.data = unicode(ipad.room_id)
    form.state.data = unicode(ipad.state_id)
    form.video_playback.data = ipad.video_playback.total_seconds() / 3600
    form.vb_lessons.data = ipad.vb_lesson_ids_included_unicode
    form.y_gre_lessons.data = ipad.y_gre_lesson_ids_included_unicode
    return render_template('manage/edit_ipad.html', form=form, ipad=ipad)


@manage.route('/ipad/delete/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad设备')
def delete_ipad(id):
    ipad = iPad.query.get_or_404(id)
    if ipad.deleted:
        abort(404)
    form = DeleteiPadForm(ipad=ipad)
    if form.validate_on_submit():
        ipad.safe_delete(modified_by=current_user._get_current_object())
        iPadContentJSON.mark_out_of_date()
        flash(u'已删除序列号为%s的iPad' % ipad.serial, category='success')
        return redirect(request.args.get('next') or url_for('manage.ipad'))
    return render_template('manage/delete_ipad.html', form=form, ipad=ipad)


@manage.route('/ipad/filter', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理')
def filter_ipad():
    ipads = []
    form = FilteriPadForm()
    if form.validate_on_submit():
        lesson_ids = form.vb_lessons.data + form.y_gre_lessons.data
        if len(lesson_ids):
            ipad_ids = reduce(lambda x, y: x & y, [set([query.ipad_id for query in iPadContent.query.filter_by(lesson_id=int(lesson_id)).all()]) for lesson_id in lesson_ids])
            ipads = [ipad for ipad in [iPad.query.get(ipad_id) for ipad_id in ipad_ids] if not ipad.deleted]
    return render_template('manage/filter_ipad.html', form=form, ipads=ipads)


@manage.route('/ipad/contents')
@login_required
@permission_required(u'管理')
def ipad_contents():
    ipad_contents = iPadContentJSON.query.get_or_404(1)
    if ipad_contents.out_of_date:
        iPadContentJSON.update()
    return render_template('manage/ipad_contents.html', ipad_contents=json.loads(ipad_contents.json_string))


@manage.route('/announcement', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理通知')
def announcement():
    form = NewAnnouncementForm()
    if form.validate_on_submit():
        announcement = Announcement(title=form.title.data, body_html=form.body.data, type_id=int(form.announcement_type.data), modified_by_id=current_user.id)
        db.session.add(announcement)
        db.session.commit()
        if form.show.data:
            announcement.publish(modified_by=current_user._get_current_object())
        else:
            announcement.clean_up()
        flash(u'已添加通知：“%s”' % form.title.data, category='success')
        return redirect(url_for('manage.announcement'))
    page = request.args.get('page', 1, type=int)
    query = Announcement.query.filter_by(deleted=False)
    pagination = query\
        .order_by(Announcement.modified_at.desc())\
        .paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    announcements = pagination.items
    return render_template('manage/announcement.html', form=form, announcements=announcements, pagination=pagination)


@manage.route('/announcement/publish/<int:id>')
@login_required
@permission_required(u'管理通知')
def publish_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    if announcement.show:
        flash(u'所选通知已经发布', category='warning')
        return redirect(request.args.get('next') or url_for('manage.announcement'))
    announcement.publish(modified_by=current_user._get_current_object())
    flash(u'“%s”发布成功！' % announcement.title, category='success')
    return redirect(request.args.get('next') or url_for('manage.announcement'))


@manage.route('/announcement/retract/<int:id>')
@login_required
@permission_required(u'管理通知')
def retract_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    if not announcement.show:
        flash(u'所选通知尚未发布', category='warning')
        return redirect(request.args.get('next') or url_for('manage.announcement'))
    announcement.retract(modified_by=current_user._get_current_object())
    flash(u'“%s”撤销成功！' % announcement.title, category='success')
    return redirect(request.args.get('next') or url_for('manage.announcement'))


@manage.route('/announcement/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理通知')
def edit_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    if announcement.deleted:
        abort(404)
    form = EditAnnouncementForm()
    if form.validate_on_submit():
        announcement.title = form.title.data
        announcement.body_html = form.body.data
        announcement.type_id = int(form.announcement_type.data)
        announcement.modified_at = datetime.utcnow()
        announcement.modified_by_id = current_user.id
        db.session.add(announcement)
        db.session.commit()
        if form.show.data:
            announcement.publish(modified_by=current_user._get_current_object())
        else:
            announcement.clean_up()
        flash(u'已更新通知：“%s”' % form.title.data, category='success')
        return redirect(request.args.get('next') or url_for('manage.announcement'))
    form.title.data = announcement.title
    form.body.data = announcement.body_html
    form.announcement_type.data = unicode(announcement.type_id)
    form.show.data = announcement.show
    return render_template('manage/edit_announcement.html', form=form, announcement=announcement)


@manage.route('/announcement/delete/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理通知')
def delete_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    if announcement.deleted:
        abort(404)
    form = DeleteAnnouncementForm()
    if form.validate_on_submit():
        announcement.safe_delete(modified_by=current_user._get_current_object())
        flash(u'已删除通知：“%s”' % announcement.title, category='success')
        return redirect(request.args.get('next') or url_for('manage.announcement'))
    return render_template('manage/delete_announcement.html', form=form, announcement=announcement)


@manage.route('/user', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理用户')
def user():
    page = request.args.get('page', 1, type=int)
    show_activated_users = True
    show_unactivated_users = False
    show_suspended_users = False
    show_volunteers = False
    show_moderators = False
    show_administrators = False
    show_developers = False
    show_deleted_users = False
    if current_user.is_authenticated:
        show_activated_users = bool(request.cookies.get('show_activated_users', '1'))
        show_unactivated_users = bool(request.cookies.get('show_unactivated_users', ''))
        show_suspended_users = bool(request.cookies.get('show_suspended_users', ''))
        show_volunteers = bool(request.cookies.get('show_volunteers', ''))
        show_moderators = bool(request.cookies.get('show_moderators', ''))
        show_administrators = bool(request.cookies.get('show_administrators', ''))
        show_developers = bool(request.cookies.get('show_developers', ''))
        show_deleted_users = bool(request.cookies.get('show_deleted_users', ''))
    if show_activated_users:
        query = User.query\
            .join(Role, Role.id == User.role_id)\
            .filter(User.activated == True)\
            .filter(User.deleted == False)\
            .filter(or_(
                Role.name == u'单VB',
                Role.name == u'Y-GRE 普通',
                Role.name == u'Y-GRE VBx2',
                Role.name == u'Y-GRE A权限'
            ))\
            .order_by(User.last_seen_at.desc())
    if show_unactivated_users:
        query = User.query\
            .join(Role, Role.id == User.role_id)\
            .filter(User.activated == False)\
            .filter(User.deleted == False)\
            .filter(or_(
                Role.name == u'单VB',
                Role.name == u'Y-GRE 普通',
                Role.name == u'Y-GRE VBx2',
                Role.name == u'Y-GRE A权限'
            ))\
            .order_by(User.last_seen_at.desc())
    if show_suspended_users:
        query = User.query\
            .join(Role, Role.id == User.role_id)\
            .filter(User.deleted == False)\
            .filter(Role.name == u'挂起')\
            .order_by(User.last_seen_at.desc())
    if show_volunteers:
        query = User.query\
            .join(Role, Role.id == User.role_id)\
            .filter(User.deleted == False)\
            .filter(Role.name == u'志愿者')\
            .order_by(User.last_seen_at.desc())
    if show_moderators:
        query = User.query\
            .join(Role, Role.id == User.role_id)\
            .filter(User.deleted == False)\
            .filter(Role.name == u'协管员')\
            .order_by(User.last_seen_at.desc())
    if show_administrators:
        query = User.query\
            .join(Role, Role.id == User.role_id)\
            .filter(User.deleted == False)\
            .filter(Role.name == u'管理员')\
            .order_by(User.last_seen_at.desc())
    if show_developers:
        query = User.query\
            .join(Role, Role.id == User.role_id)\
            .filter(User.deleted == False)\
            .filter(Role.name == u'开发人员')\
            .order_by(User.last_seen_at.desc())
    if show_deleted_users:
        query = User.query\
            .join(Role, Role.id == User.role_id)\
            .filter(User.deleted == True)\
            .order_by(User.last_seen_at.desc())
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    users = pagination.items
    return render_template('manage/user.html', users=users, show_activated_users=show_activated_users, show_unactivated_users=show_unactivated_users, show_suspended_users=show_suspended_users, show_volunteers=show_volunteers, show_moderators=show_moderators, show_administrators=show_administrators, show_developers=show_developers, show_deleted_users=show_deleted_users, pagination=pagination)


@manage.route('/user/activated')
@login_required
@permission_required(u'管理用户')
def activated_users():
    resp = make_response(redirect(url_for('manage.user')))
    resp.set_cookie('show_activated_users', '1', max_age=30*24*60*60)
    resp.set_cookie('show_unactivated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_suspended_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_volunteers', '', max_age=30*24*60*60)
    resp.set_cookie('show_moderators', '', max_age=30*24*60*60)
    resp.set_cookie('show_administrators', '', max_age=30*24*60*60)
    resp.set_cookie('show_developers', '', max_age=30*24*60*60)
    resp.set_cookie('show_deleted_users', '', max_age=30*24*60*60)
    return resp


@manage.route('/user/unactivated')
@login_required
@permission_required(u'管理用户')
def unactivated_users():
    resp = make_response(redirect(url_for('manage.user')))
    resp.set_cookie('show_activated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_unactivated_users', '1', max_age=30*24*60*60)
    resp.set_cookie('show_suspended_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_volunteers', '', max_age=30*24*60*60)
    resp.set_cookie('show_moderators', '', max_age=30*24*60*60)
    resp.set_cookie('show_administrators', '', max_age=30*24*60*60)
    resp.set_cookie('show_developers', '', max_age=30*24*60*60)
    resp.set_cookie('show_deleted_users', '', max_age=30*24*60*60)
    return resp


@manage.route('/user/suspended')
@login_required
@permission_required(u'管理用户')
def suspended_users():
    resp = make_response(redirect(url_for('manage.user')))
    resp.set_cookie('show_activated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_unactivated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_suspended_users', '1', max_age=30*24*60*60)
    resp.set_cookie('show_volunteers', '', max_age=30*24*60*60)
    resp.set_cookie('show_moderators', '', max_age=30*24*60*60)
    resp.set_cookie('show_administrators', '', max_age=30*24*60*60)
    resp.set_cookie('show_developers', '', max_age=30*24*60*60)
    resp.set_cookie('show_deleted_users', '', max_age=30*24*60*60)
    return resp


@manage.route('/user/volunteers')
@login_required
@permission_required(u'管理用户')
def volunteers():
    resp = make_response(redirect(url_for('manage.user')))
    resp.set_cookie('show_activated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_unactivated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_suspended_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_volunteers', '1', max_age=30*24*60*60)
    resp.set_cookie('show_moderators', '', max_age=30*24*60*60)
    resp.set_cookie('show_administrators', '', max_age=30*24*60*60)
    resp.set_cookie('show_developers', '', max_age=30*24*60*60)
    resp.set_cookie('show_deleted_users', '', max_age=30*24*60*60)
    return resp


@manage.route('/user/moderators')
@login_required
@permission_required(u'管理用户')
def moderators():
    resp = make_response(redirect(url_for('manage.user')))
    resp.set_cookie('show_activated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_unactivated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_suspended_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_volunteers', '', max_age=30*24*60*60)
    resp.set_cookie('show_moderators', '1', max_age=30*24*60*60)
    resp.set_cookie('show_administrators', '', max_age=30*24*60*60)
    resp.set_cookie('show_developers', '', max_age=30*24*60*60)
    resp.set_cookie('show_deleted_users', '', max_age=30*24*60*60)
    return resp


@manage.route('/user/administrators')
@login_required
@administrator_required
def administrators():
    resp = make_response(redirect(url_for('manage.user')))
    resp.set_cookie('show_activated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_unactivated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_suspended_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_volunteers', '', max_age=30*24*60*60)
    resp.set_cookie('show_moderators', '', max_age=30*24*60*60)
    resp.set_cookie('show_administrators', '1', max_age=30*24*60*60)
    resp.set_cookie('show_developers', '', max_age=30*24*60*60)
    resp.set_cookie('show_deleted_users', '', max_age=30*24*60*60)
    return resp


@manage.route('/user/developers')
@login_required
@developer_required
def developers():
    resp = make_response(redirect(url_for('manage.user')))
    resp.set_cookie('show_activated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_unactivated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_suspended_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_volunteers', '', max_age=30*24*60*60)
    resp.set_cookie('show_moderators', '', max_age=30*24*60*60)
    resp.set_cookie('show_administrators', '', max_age=30*24*60*60)
    resp.set_cookie('show_developers', '1', max_age=30*24*60*60)
    resp.set_cookie('show_deleted_users', '', max_age=30*24*60*60)
    return resp


@manage.route('/user/deleted')
@login_required
@administrator_required
def deleted_users():
    resp = make_response(redirect(url_for('manage.user')))
    resp.set_cookie('show_activated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_unactivated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_suspended_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_volunteers', '', max_age=30*24*60*60)
    resp.set_cookie('show_moderators', '', max_age=30*24*60*60)
    resp.set_cookie('show_administrators', '', max_age=30*24*60*60)
    resp.set_cookie('show_developers', '', max_age=30*24*60*60)
    resp.set_cookie('show_deleted_users', '1', max_age=30*24*60*60)
    return resp


# @manage.route('/user/create', methods=['GET', 'POST'])
# @login_required
# @permission_required(u'管理用户')
# def create_user():
#     form = NewUserForm()
#     if form.validate_on_submit():
#         if int(form.id_number.data[16]) % 2 == 1:
#             gender = Gender.query.filter_by(name=u'男').first()
#         else:
#             gender = Gender.query.filter_by(name=u'女').first()
#         user = User(
#             email=form.email.data,
#             role_id=int(form.role.data),
#             password=form.id_number.data[-6:],
#             name=form.name.data,
#             gender_id=gender.id,
#             id_number=form.id_number.data.upper(),
#             birthdate=date(year=int(form.id_number.data[6:10]), month=int(form.id_number.data[10:12]), day=int(form.id_number.data[12:14])),
#             mobile=form.mobile.data,
#             wechat=form.wechat.data,
#             qq=form.qq.data,
#             address=form.address.data,
#             emergency_contact_name=form.emergency_contact_name.data,
#             emergency_contact_relationship_id=int(form.emergency_contact_relationship.data),
#             emergency_contact_mobile=form.emergency_contact_mobile.data,
#             worked_in_same_field=form.worked_in_same_field.data,
#             deformity=form.deformity.data,
#             application_major=form.application_major.data
#         )
#         db.session.add(user)
#         db.session.commit()
#         # education
#         if form.high_school.data:
#             user.add_education_record(
#                 education_type=EducationType.query.filter_by(name=u'高中').first(),
#                 school=form.high_school.data,
#                 year=form.high_school_year.data
#             )
#         if form.bachelor_school.data:
#             user.add_education_record(
#                 education_type=EducationType.query.filter_by(name=u'本科').first(),
#                 school=form.bachelor_school.data,
#                 major=form.bachelor_major.data,
#                 gpa=form.bachelor_gpa.data,
#                 full_gpa=form.bachelor_full_gpa.data,
#                 year=form.bachelor_year.data
#             )
#         if form.master_school.data:
#             user.add_education_record(
#                 education_type=EducationType.query.filter_by(name=u'本科').first(),
#                 school=form.master_school.data,
#                 major=form.master_major.data,
#                 gpa=form.master_gpa.data,
#                 full_gpa=form.master_full_gpa.data,
#                 year=form.master_year.data
#             )
#         if form.doctor_school.data:
#             user.add_education_record(
#                 education_type=EducationType.query.filter_by(name=u'本科').first(),
#                 school=form.doctor_school.data,
#                 major=form.doctor_major.data,
#                 gpa=form.doctor_gpa.data,
#                 full_gpa=form.doctor_full_gpa.data,
#                 year=form.doctor_year.data
#             )
#         # employment
#         if form.employer_1.data:
#             user.add_employment_record(
#                 employer=form.employer_1.data,
#                 position=form.position_1.data,
#                 year=form.job_year_1.data
#             )
#         if form.employer_2.data:
#             user.add_employment_record(
#                 employer=form.employer_2.data,
#                 position=form.position_2.data,
#                 year=form.job_year_2.data
#             )
#         # scores
#         if form.cee_total.data:
#             user.add_previous_achievement(
#                 previous_achievement_type=PreviousAchievementType.query.filter_by(name=u'高考总分').first(),
#                 score=form.cee_total.data
#             )
#         if form.cee_math.data:
#             user.add_previous_achievement(
#                 previous_achievement_type=PreviousAchievementType.query.filter_by(name=u'高考数学').first(),
#                 score=form.cee_math.data
#             )
#         if form.cee_english.data:
#             user.add_previous_achievement(
#                 previous_achievement_type=PreviousAchievementType.query.filter_by(name=u'高考英语').first(),
#                 score=form.cee_english.data
#             )
#         if form.cet_4.data:
#             user.add_previous_achievement(
#                 previous_achievement_type=PreviousAchievementType.query.filter_by(name=u'大学英语四级').first(),
#                 score=form.cet_4.data
#             )
#         if form.cet_6.data:
#             user.add_previous_achievement(
#                 previous_achievement_type=PreviousAchievementType.query.filter_by(name=u'大学英语六级').first(),
#                 score=form.cet_6.data
#             )
#         if form.tem_4.data:
#             user.add_previous_achievement(
#                 previous_achievement_type=PreviousAchievementType.query.filter_by(name=u'专业英语四级').first(),
#                 score=form.tem_4.data
#             )
#         if form.tem_8.data:
#             user.add_previous_achievement(
#                 previous_achievement_type=PreviousAchievementType.query.filter_by(name=u'专业英语八级').first(),
#                 score=form.tem_8.data
#             )
#         if form.competition.data:
#             user.add_previous_achievement(
#                 previous_achievement_type=PreviousAchievementType.query.filter_by(name=u'竞赛').first(),
#                 remark=form.competition.data
#             )
#         if form.other_score.data:
#             user.add_previous_achievement(
#                 previous_achievement_type=PreviousAchievementType.query.filter_by(name=u'其它').first(),
#                 remark=form.other_score.data
#             )
#         if form.toefl_total.data:
#             user.add_toefl_test_score(
#                 toefl_test_score_type=TOEFLTestScoreType.query.filter_by(name=u'初始').first(),
#                 total_score_id=form.toefl_total.data,
#                 reading_score_id=form.toefl_reading.data,
#                 listening_score_id=form.toefl_listening.data,
#                 speaking_score_id=form.toefl_speaking.data,
#                 writing_score_id=form.toefl_writing.data,
#                 modified_by=current_user._get_current_object()
#             )
#         # registration
#         for purpose_type_id in form.purposes.data:
#             user.add_purpose(purpose_type=PurposeType.query.get(int(purpose_type_id)))
#         if form.other_purpose.data:
#             user.add_purpose(purpose_type=PurposeType.query.filter_by(name=u'其它').first(), remark=form.other_purpose.data)
#         for referrer_type_id in form.referrers.data:
#             user.add_referrer(referrer_type=ReferrerType.query.get(int(referrer_type_id)))
#         if form.other_referrer.data:
#             user.add_referrer(referrer_type=ReferrerType.query.filter_by(name=u'其它').first(), remark=form.other_referrer.data)
#         if form.inviter_email.data:
#             inviter = User.query.filter_by(email=form.inviter_email.data).first()
#             if inviter is not None:
#                 inviter.invite_user(user=user, invitation_type=InvitationType.query.filter_by(name=u'积分').first())
#         if int(form.vb_course.data):
#             user.register_course(course=Course.query.get(int(form.vb_course.data)))
#         if int(form.y_gre_course.data):
#             user.register_course(course=Course.query.get(int(form.y_gre_course.data)))
#         for product_id in form.products.data:
#             user.purchase_product(product=Product.query.get(int(product_id)))
#         receptionist = User.query.filter_by(email=form.receptionist_email.data).first()
#         if receptionist is not None:
#             receptionist.receive_user(user=user)
#         current_user.create_user(user=user)
#         flash(u'成功添加“%s”用户：%s' % (user.role.name, user.name), category='success')
#         return redirect(request.args.get('next') or url_for('manage.user'))
#     return render_template('manage/create_user.html', form=form)


@manage.route('/user/create', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理用户')
def create_user():
    form = NewUserForm()
    if form.validate_on_submit():
        if int(form.id_number.data[16]) % 2 == 1:
            gender = Gender.query.filter_by(name=u'男').first()
        else:
            gender = Gender.query.filter_by(name=u'女').first()
        user = User(
            email=form.email.data,
            role_id=Role.query.filter_by(name=u'挂起').first().id,
            password=form.id_number.data[-6:],
            name=form.name.data,
            gender_id=gender.id,
            id_number=form.id_number.data.upper(),
            birthdate=date(year=int(form.id_number.data[6:10]), month=int(form.id_number.data[10:12]), day=int(form.id_number.data[12:14])),
            mobile=form.mobile.data,
            wechat=form.wechat.data,
            qq=form.qq.data,
            address=form.address.data,
            emergency_contact_name=form.emergency_contact_name.data,
            emergency_contact_relationship_id=int(form.emergency_contact_relationship.data),
            emergency_contact_mobile=form.emergency_contact_mobile.data
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    return render_template('manage/create_user.html', form=form)


@manage.route('/user/create/confirm/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理用户')
def create_user_confirm(id):
    user = User.query.get_or_404(id)
    if user.deleted:
        abort(404)
    if user.is_superior_than(user=current_user._get_current_object()):
        abort(403)
    if user.activated:
        flash(u'%s（%s）已经被激活' % (user.name, user.email), category='error')
        return redirect(request.args.get('next') or url_for('manage.user'))
    new_education_record_form = NewEducationRecordForm()
    new_employment_record_form = NewEmploymentRecordForm()
    new_previous_achievement_form = NewPreviousAchievementForm()
    new_toefl_test_score_form = NewTOEFLTestScoreForm()
    return render_template('manage/create_user_confirm.html', new_education_record_form=new_education_record_form, new_employment_record_form=new_employment_record_form, new_previous_achievement_form=new_previous_achievement_form, new_toefl_test_score_form=new_toefl_test_score_form, user=user)


@manage.route('/user/create-admin', methods=['GET', 'POST'])
@login_required
@administrator_required
def create_admin():
    form = NewAdminForm(creator=current_user._get_current_object())
    if form.validate_on_submit():
        if int(form.id_number.data[16]) % 2 == 1:
            gender = Gender.query.filter_by(name=u'男').first()
        else:
            gender = Gender.query.filter_by(name=u'女').first()
        admin = User(
            email=form.email.data,
            role_id=int(form.role.data),
            password=form.id_number.data[-6:],
            name=form.name.data,
            gender_id=gender.id,
            id_number=form.id_number.data.upper(),
            birthdate=date(year=int(form.id_number.data[6:10]), month=int(form.id_number.data[10:12]), day=int(form.id_number.data[12:14]))
        )
        db.session.add(admin)
        db.session.commit()
        current_user.create_user(user=admin)
        flash(u'成功添加%s：%s' % (admin.role.name, admin.name), category='success')
        return redirect(request.args.get('next') or url_for('manage.user'))
    return render_template('manage/create_admin.html', form=form)


@manage.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理用户')
def edit_user(id):
    user = User.query.get_or_404(id)
    if user.deleted:
        abort(404)
    if user.is_superior_than(user=current_user._get_current_object()):
        abort(403)
    form = EditUserForm(editor=current_user._get_current_object())
    if form.validate_on_submit():
        user.name = form.name.data
        user.role_id = int(form.role.data)
        db.session.add(user)
        # if user.vb_course:
        #     user.unregister_course(user.vb_course)
        # if form.vb_course.data:
        #     user.register_course(Course.query.get(form.vb_course.data))
        # if user.y_gre_course:
        #     user.unregister_course(user.y_gre_course)
        # if form.y_gre_course.data:
        #     user.register_course(Course.query.get(form.y_gre_course.data))
        flash(u'%s的用户信息已更新' % form.name.data, category='success')
        return redirect(request.args.get('next') or url_for('manage.user'))
    form.name.data = user.name
    form.role.data = unicode(user.role_id)
    # if user.vb_course:
    #     form.vb_course.data = user.vb_course.id
    # if user.y_gre_course:
    #     form.y_gre_course.data = user.y_gre_course.id
    return render_template('manage/edit_user.html', form=form, user=user)


@manage.route('/user/delete/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理用户')
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.deleted:
        abort(404)
    if user.is_superior_than(user=current_user._get_current_object()):
        abort(403)
    form = DeleteUserForm()
    if form.validate_on_submit():
        user.safe_delete()
        flash(u'已注销用户：%s [%s]（%s）' % (user.name, user.role.name, user.email), category='success')
        return redirect(request.args.get('next') or url_for('manage.user'))
    return render_template('manage/delete_user.html', form=form, user=user)


@manage.route('/user/restore/<int:id>', methods=['GET', 'POST'])
@login_required
@administrator_required
def restore_user(id):
    user = User.query.get_or_404(id)
    if not user.deleted:
        abort(404)
    if user.is_superior_than(user=current_user._get_current_object()):
        abort(403)
    form = RestoreUserForm(restorer=current_user._get_current_object())
    if form.validate_on_submit():
        role = Role.query.get(int(form.role.data))
        user.restore(email=form.email.data, role=role)
        flash(u'已恢复用户：%s [%s]（%s）' % (user.name, role.name, user.email), category='success')
        return redirect(request.args.get('next') or url_for('manage.user'))
    form.email.data = user.email[:-len(u'_%s_deleted' % user.id)]
    form.role.data = unicode(user.role_id)
    return render_template('manage/restore_user.html', form=form, user=user)


@manage.route('/user/find', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理')
def find_user():
    users = []
    name_or_email = request.args.get('keyword')
    if name_or_email:
        users = User.query\
            .filter(User.deleted == False)\
            .filter(or_(
                User.name.like('%' + name_or_email + '%'),
                User.email.like('%' + name_or_email + '%')
            ))\
            .order_by(User.last_seen_at.desc())\
            .limit(current_app.config['RECORD_PER_QUERY'])
    form = FindUserForm()
    if form.validate_on_submit():
        name_or_email = form.name_or_email.data
        if name_or_email:
            users = User.query\
                .filter(User.deleted == False)\
                .filter(or_(
                    User.name.like('%' + name_or_email + '%'),
                    User.email.like('%' + name_or_email + '%')
                ))\
                .order_by(User.last_seen_at.desc())\
                .limit(current_app.config['RECORD_PER_QUERY'])
    form.name_or_email.data = name_or_email
    users = [user for user in users if not user.is_superior_than(user=current_user._get_current_object())]
    return render_template('manage/find_user.html', form=form, users=users, keyword=name_or_email)


@manage.route('/course', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理班级')
def course():
    form = NewCourseForm()
    if form.validate_on_submit():
        course = Course(name=form.name.data, type_id=int(form.course_type.data), show=form.show.data, modified_by_id=current_user.id)
        db.session.add(course)
        flash(u'新建班级：%s' % form.name.data, category='success')
        return redirect(url_for('manage.course'))
    page = request.args.get('page', 1, type=int)
    show_vb_courses = True
    show_y_gre_courses = False
    if current_user.is_authenticated:
        show_vb_courses = bool(request.cookies.get('show_vb_courses', '1'))
        show_y_gre_courses = bool(request.cookies.get('show_y_gre_courses', ''))
    if show_vb_courses:
        query = Course.query\
            .join(CourseType, CourseType.id == Course.type_id)\
            .filter(CourseType.name == u'VB')\
            .filter(Course.deleted == False)\
            .order_by(Course.id.desc())
    if show_y_gre_courses:
        query = Course.query\
            .join(CourseType, CourseType.id == Course.type_id)\
            .filter(CourseType.name == u'Y-GRE')\
            .filter(Course.deleted == False)\
            .order_by(Course.id.desc())
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    courses = pagination.items
    return render_template('manage/course.html', form=form, courses=courses, show_vb_courses=show_vb_courses, show_y_gre_courses=show_y_gre_courses, pagination=pagination)


@manage.route('/course/vb')
@login_required
@permission_required(u'管理班级')
def vb_courses():
    resp = make_response(redirect(url_for('manage.course')))
    resp.set_cookie('show_vb_courses', '1', max_age=30*24*60*60)
    resp.set_cookie('show_y_gre_courses', '', max_age=30*24*60*60)
    return resp


@manage.route('/course/y-gre')
@login_required
@permission_required(u'管理班级')
def y_gre_courses():
    resp = make_response(redirect(url_for('manage.course')))
    resp.set_cookie('show_vb_courses', '', max_age=30*24*60*60)
    resp.set_cookie('show_y_gre_courses', '1', max_age=30*24*60*60)
    return resp


@manage.route('/course/<int:id>')
@login_required
@permission_required(u'管理')
def course_users(id):
    course = Course.query.get_or_404(id)
    if course.deleted:
        abort(404)
    page = request.args.get('page', 1, type=int)
    query = User.query\
        .join(CourseRegistration, CourseRegistration.user_id == User.id)\
        .join(Course, Course.id == CourseRegistration.course_id)\
        .filter(User.deleted == False)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    users = pagination.items
    return render_template('manage/course_users.html', course=course, users=users, pagination=pagination)


@manage.route('/course/flip-show/<int:id>')
@login_required
@permission_required(u'管理班级')
def flip_course_show(id):
    course = Course.query.get_or_404(id)
    if course.deleted:
        abort(404)
    course.flip_show(modified_by=current_user._get_current_object())
    if course.show:
        flash(u'班级：%s的可选状态改为：可选' % course.name, category='success')
    else:
        flash(u'班级：%s的可选状态改为：不可选' % course.name, category='success')
    return redirect(request.args.get('next') or url_for('manage.course'))


@manage.route('/course/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理班级')
def edit_course(id):
    course = Course.query.get_or_404(id)
    if course.deleted:
        abort(404)
    form = EditCourseForm()
    if form.validate_on_submit():
        course.name = form.name.data
        course.type_id = int(form.course_type.data)
        course.show = form.show.data
        course.modified_at = datetime.utcnow()
        course.modified_by_id = current_user.id
        db.session.add(course)
        flash(u'已更新班级：%s' % form.name.data, category='success')
        return redirect(request.args.get('next') or url_for('manage.course'))
    form.name.data = course.name
    form.course_type.data = unicode(course.type_id)
    form.show.data = course.show
    return render_template('manage/edit_course.html', form=form, course=course)


@manage.route('/course/delete/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理班级')
def delete_course(id):
    course = Course.query.get_or_404(id)
    if course.deleted:
        abort(404)
    form = DeleteCourseForm()
    if form.validate_on_submit():
        course.safe_delete(modified_by=current_user._get_current_object())
        flash(u'已删除班级：%s' % course.name, category='success')
        return redirect(request.args.get('next') or url_for('manage.course'))
    return render_template('manage/delete_course.html', form=form, course=course)


@manage.route('/analytics')
@login_required
@permission_required(u'管理')
def analytics():
    analytics_token = current_app.config['ANALYTICS_TOKEN']
    return render_template('manage/analytics.html', analytics_token=analytics_token)


@manage.route('/suggest/user/')
@permission_required(u'管理')
def suggest_user():
    users = []
    name_or_email = request.args.get('keyword')
    if name_or_email:
        users = User.query\
            .filter(User.deleted == False)\
            .filter(or_(
                User.name.like('%' + name_or_email + '%'),
                User.email.like('%' + name_or_email + '%')
            ))\
            .order_by(User.last_seen_at.desc())\
            .limit(current_app.config['RECORD_PER_QUERY'])
    return jsonify({'results': [user.to_json_suggestion() for user in users if not user.is_superior_than(user=current_user._get_current_object())]})


@manage.route('/suggest/email/')
@permission_required(u'管理')
def suggest_email():
    users = []
    name_or_email = request.args.get('keyword')
    if name_or_email:
        users = User.query\
            .filter(User.deleted == False)\
            .filter(or_(
                User.name.like('%' + name_or_email + '%'),
                User.email.like('%' + name_or_email + '%')
            ))\
            .order_by(User.last_seen_at.desc())\
            .limit(current_app.config['RECORD_PER_QUERY'])
    return jsonify({'results': [user.to_json_suggestion(suggest_email=True) for user in users if not user.is_superior_than(user=current_user._get_current_object())]})


@manage.route('/search/user/')
@permission_required(u'管理')
def search_user():
    users = []
    name_or_email = request.args.get('keyword')
    if name_or_email:
        users = User.query\
            .filter(User.deleted == False)\
            .filter(or_(
                User.name.like('%' + name_or_email + '%'),
                User.email.like('%' + name_or_email + '%')
            ))\
            .order_by(User.last_seen_at.desc())\
            .limit(current_app.config['RECORD_PER_QUERY'])
    return jsonify({'results': [user.to_json_suggestion(include_url=True) for user in users if not user.is_superior_than(user=current_user._get_current_object())]})