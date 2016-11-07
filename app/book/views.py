# -*- coding: utf-8 -*-

from datetime import date
from flask import render_template, redirect, url_for, flash, current_app, make_response, request
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import book
from .. import db
from ..email import send_email
from ..models import Permission, User, Schedule, Period, CourseType, Booking, BookingState, iPadState, iPad, iPadContent, Punch, Announcement, AnnouncementType
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
    announcements = Announcement.query\
        .join(AnnouncementType, AnnouncementType.id == Announcement.type_id)\
        .filter(AnnouncementType.name == u'预约VB通知')\
        .filter(Announcement.show == True)\
        .filter(Announcement.deleted == False)\
        .all()
    for announcement in announcements:
        if not current_user.notified_by(announcement=announcement):
            flash(u'[%s]%s' % (announcement.title, announcement.body), category='announcement')
            announcement.notify(reader=current_user)
    page = request.args.get('page', 1, type=int)
    query = Schedule.query\
        .join(Period, Period.id == Schedule.period_id)\
        .join(CourseType, CourseType.id == Period.type_id)\
        .filter(CourseType.name == u'VB')\
        .filter(Schedule.available == True)\
        .filter(Schedule.date >= date.today())\
        .order_by(Schedule.date.asc())\
        .order_by(Period.id.asc())
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    schedules = pagination.items
    return render_template('book/vb.html', schedules=schedules, pagination=pagination, announcements=announcements)


@book.route('/vb/book/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_VB)
def book_vb(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not schedule.available:
        flash(u'所选时段尚未开放', category='error')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if not schedule.unstarted:
        flash(u'所选时段已不接受预约', category='error')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if schedule.full:
        flash(u'该时段名额已经约满', category='error')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if current_user.booked(schedule):
        flash(u'您已经预约过该时段，请不要重复预约', category='warning')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if current_user.booking_y_gre_same_day(schedule):
        flash(u'您当天已经预约过Y-GRE课程，不要太贪心哦~', category='warning')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    same_day_bookings = current_user.booking_vb_same_day(schedule)
    if same_day_bookings >= 2 and not current_user.can(Permission.BOOK_ANY):
        flash(u'您当天已经预约过%d节VB课程，不要太贪心哦~' % same_day_bookings, category='warning')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    elif same_day_bookings >= 1 and not current_user.can(Permission.BOOK_VB_2):
        flash(u'您当天已经预约过VB课程，不要太贪心哦~', category='warning')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    current_user.book(schedule, u'预约')
    booking = Booking.query.filter_by(user_id=current_user.id, schedule_id=schedule_id).first()
    send_email(current_user.email, u'您已成功预约%s的%s课程' % (schedule.date, schedule.period.alias), 'book/mail/booking', user=current_user, schedule=schedule, booking=booking)
    flash(u'预约成功！', category='success')
    booked_ipads = Booking.query\
        .join(Punch, Punch.user_id == Booking.user_id)\
        .join(BookingState, BookingState.id == Booking.state_id)\
        .filter(Booking.schedule_id == schedule_id)\
        .filter(BookingState.name == u'预约')\
        .filter(Punch.lesson_id == current_user.last_punch.lesson_id)
    available_ipads = iPad.query\
        .join(iPadContent, iPadContent.ipad_id == iPad.id)\
        .join(iPadState, iPadState.id == iPad.state_id)\
        .filter(iPadContent.lesson_id == current_user.last_punch.lesson_id)\
        .filter(iPadState.name != u'退役')
    if booked_ipads.count() >= available_ipads.count():
        for manager in User.query.all():
            if manager.can(Permission.MANAGE_IPAD):
                send_email(manager.email, u'含有课程“%s”的iPad资源紧张' % current_user.last_punch.lesson.name, 'book/mail/short_of_ipad', schedule=schedule, lesson=current_user.last_punch.lesson, booked_ipads=booked_ipads, available_ipads=available_ipads)
    return redirect(url_for('book.vb', page=request.args.get('page')))


@book.route('/vb/wait/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_VB)
def wait_vb(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not schedule.available:
        flash(u'所选时段尚未开放', category='error')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if not schedule.unstarted:
        flash(u'所选时段已不接受预约', category='error')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if not schedule.full:
        flash(u'该时段仍有名额，请直接预约', category='warning')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if current_user.booked(schedule):
        flash(u'您已经预约过该时段，请不要重复预约', category='warning')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if current_user.booking_y_gre_same_day(schedule):
        flash(u'您当天已经预约过Y-GRE课程，不要太贪心哦~', category='warning')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    same_day_bookings = current_user.booking_vb_same_day(schedule)
    if same_day_bookings >= 2 and not current_user.can(Permission.BOOK_ANY):
        flash(u'您当天已经预约过%d节VB课程，不要太贪心哦~' % same_day_bookings, category='warning')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    elif same_day_bookings >= 1 and not current_user.can(Permission.BOOK_VB_2):
        flash(u'您当天已经预约过VB课程，不要太贪心哦~', category='warning')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    current_user.book(schedule, u'排队')
    flash(u'已将您加入候选名单', category='success')
    return redirect(url_for('book.vb', page=request.args.get('page')))


@book.route('/vb/unbook/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_VB)
def unbook_vb(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not schedule.available:
        flash(u'所选时段尚未开放', category='error')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if not schedule.unstarted:
        flash(u'所选时段已不能自行取消', category='error')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if not current_user.booked(schedule):
        flash(u'您目前尚未预约该时段', category='error')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    candidate = current_user.unbook(schedule)
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
    flash(u'取消成功！', category='success')
    return redirect(url_for('book.vb', page=request.args.get('page')))


@book.route('/vb/miss/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_VB)
def miss_vb(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not schedule.available:
        flash(u'所选时段尚未开放', category='error')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if not schedule.started:
        flash(u'所选时段已不能自行取消', category='error')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    if not current_user.booked(schedule):
        flash(u'您目前尚未预约该时段', category='warning')
        return redirect(url_for('book.vb', page=request.args.get('page')))
    current_user.miss(schedule)
    flash(u'取消成功！', category='success')
    return redirect(url_for('book.vb', page=request.args.get('page')))


@book.route('/y-gre')
@login_required
@permission_required(Permission.BOOK_Y_GRE)
def y_gre():
    announcements = Announcement.query\
        .join(AnnouncementType, AnnouncementType.id == Announcement.type_id)\
        .filter(AnnouncementType.name == u'预约Y-GRE通知')\
        .filter(Announcement.show == True)\
        .filter(Announcement.deleted == False)\
        .all()
    for announcement in announcements:
        if not current_user.notified_by(announcement=announcement):
            flash(u'[%s]%s' % (announcement.title, announcement.body), category='announcement')
            announcement.notify(reader=current_user)
    page = request.args.get('page', 1, type=int)
    query = Schedule.query\
        .join(Period, Period.id == Schedule.period_id)\
        .join(CourseType, CourseType.id == Period.type_id)\
        .filter(CourseType.name == u'Y-GRE')\
        .filter(Schedule.available == True)\
        .filter(Schedule.date >= date.today())\
        .order_by(Schedule.date.asc())\
        .order_by(Period.id.asc())
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    schedules = pagination.items
    return render_template('book/y_gre.html', schedules=schedules, pagination=pagination, announcements=announcements)


@book.route('/y-gre/book/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_Y_GRE)
def book_y_gre(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not schedule.available:
        flash(u'所选时段尚未开放', category='error')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if not schedule.unstarted:
        flash(u'所选时段已不接受预约', category='error')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if schedule.full:
        flash(u'该时段名额已经约满', category='error')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if current_user.booked(schedule):
        flash(u'您已经预约过该时段，请不要重复预约', category='warning')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if current_user.booking_vb_same_day(schedule):
        flash(u'您当天已经预约过VB课程，不要太贪心哦~', category='warning')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    same_day_bookings = current_user.booking_y_gre_same_day(schedule)
    if same_day_bookings >= 1 and not current_user.can(Permission.BOOK_ANY):
        flash(u'您当天已经预约过Y-GRE课程，不要太贪心哦~' % same_day_bookings, category='warning')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    current_user.book(schedule, u'预约')
    booking = Booking.query.filter_by(user_id=current_user.id, schedule_id=schedule_id).first()
    send_email(current_user.email, u'您已成功预约%s的%s课程' % (schedule.date, schedule.period.alias), 'book/mail/booking', user=current_user, schedule=schedule, booking=booking)
    flash(u'预约成功！', category='success')
    booked_ipads = Booking.query\
        .join(Punch, Punch.user_id == Booking.user_id)\
        .join(BookingState, BookingState.id == Booking.state_id)\
        .filter(Booking.schedule_id == schedule_id)\
        .filter(BookingState.name == u'预约')\
        .filter(Punch.lesson_id == current_user.last_punch.lesson_id)
    available_ipads = iPad.query\
        .join(iPadContent, iPadContent.ipad_id == iPad.id)\
        .join(iPadState, iPadState.id == iPad.state_id)\
        .filter(iPadContent.lesson_id == current_user.last_punch.lesson_id)\
        .filter(iPadState.name != u'退役')
    if booked_ipads.count() >= available_ipads.count():
        for manager in User.query.all():
            if manager.can(Permission.MANAGE_IPAD):
                send_email(manager.email, u'含有课程“%s”的iPad资源紧张' % current_user.last_punch.lesson.name, 'book/mail/short_of_ipad', schedule=schedule, lesson=current_user.last_punch.lesson, booked_ipads=booked_ipads, available_ipads=available_ipads)
    return redirect(url_for('book.y_gre', page=request.args.get('page')))


@book.route('/y-gre/wait/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_Y_GRE)
def wait_y_gre(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not schedule.available:
        flash(u'所选时段尚未开放', category='error')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if not schedule.unstarted:
        flash(u'所选时段已不接受预约', category='error')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if not schedule.full:
        flash(u'该时段仍有名额，请直接预约', category='error')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if current_user.booked(schedule):
        flash(u'您已经预约过该时段，请不要重复预约', category='warning')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if current_user.booking_vb_same_day(schedule):
        flash(u'您当天已经预约过VB课程，不要太贪心哦~', category='warning')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    same_day_bookings = current_user.booking_y_gre_same_day(schedule)
    if same_day_bookings >= 1 and not current_user.can(Permission.BOOK_ANY):
        flash(u'您当天已经预约过Y-GRE课程，不要太贪心哦~' % same_day_bookings, category='warning')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    current_user.book(schedule, u'排队')
    flash(u'已将您加入候选名单', category='success')
    return redirect(url_for('book.y_gre', page=request.args.get('page')))


@book.route('/y-gre/unbook/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_Y_GRE)
def unbook_y_gre(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not schedule.available:
        flash(u'所选时段尚未开放', category='error')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if not schedule.unstarted:
        flash(u'所选时段已不能自行取消', category='error')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if not current_user.booked(schedule):
        flash(u'您目前尚未预约该时段', category='warning')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    candidate = current_user.unbook(schedule)
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
    flash(u'取消成功！', category='success')
    return redirect(url_for('book.y_gre', page=request.args.get('page')))


@book.route('/y_gre/miss/<schedule_id>')
@login_required
@permission_required(Permission.BOOK_Y_GRE)
def miss_y_gre(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not schedule.available:
        flash(u'所选时段尚未开放', category='error')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if not schedule.started:
        flash(u'所选时段已不能自行取消', category='error')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    if not current_user.booked(schedule):
        flash(u'您目前尚未预约该时段', category='warning')
        return redirect(url_for('book.y_gre', page=request.args.get('page')))
    current_user.miss(schedule)
    flash(u'取消成功！', category='success')
    return redirect(url_for('book.y_gre', page=request.args.get('page')))