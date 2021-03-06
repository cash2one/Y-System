# -*- coding: utf-8 -*-

from datetime import date
from flask import render_template, redirect, url_for, flash, current_app, make_response, request
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import book
from .. import db
from ..models import User, Schedule, Period, CourseType, Booking
from ..email import send_email, send_emails
from ..notify import get_announcements, add_feed
from ..decorators import permission_required


@book.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['YSYS_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning('Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n' % (query.statement, query.parameters, query.duration, query.context))
    return response


@book.route('/vb')
@login_required
@permission_required(u'预约VB课程')
def vb():
    query = Schedule.query\
        .join(Period, Period.id == Schedule.period_id)\
        .join(CourseType, CourseType.id == Period.type_id)\
        .filter(CourseType.name == u'VB')\
        .filter(Schedule.available == True)\
        .filter(Schedule.date >= date.today())\
        .order_by(Schedule.date.asc())\
        .order_by(Period.id.asc())
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    schedules = pagination.items
    announcements = get_announcements(type_name=u'预约VB通知', user=current_user._get_current_object())
    return render_template('book/vb.html',
        pagination=pagination,
        schedules=schedules,
        announcements=announcements
    )


@book.route('/vb/book/<int:id>')
@login_required
@permission_required(u'预约VB课程')
def book_vb(id):
    schedule = Schedule.query.get_or_404(id)
    if not schedule.available:
        flash(u'所选时段尚未开放', category='error')
        return redirect(request.args.get('next') or url_for('book.vb'))
    if not schedule.unstarted:
        flash(u'所选时段已不接受预约', category='error')
        return redirect(request.args.get('next') or url_for('book.vb'))
    if schedule.full:
        flash(u'该时段名额已经约满', category='error')
        return redirect(request.args.get('next') or url_for('book.vb'))
    if current_user.booked(schedule):
        flash(u'您已经预约过该时段，请不要重复预约', category='warning')
        return redirect(request.args.get('next') or url_for('book.vb'))
    if current_user.booking_y_gre_same_day(schedule):
        flash(u'您当天已经预约过Y-GRE课程，不要太贪心哦~', category='warning')
        return redirect(request.args.get('next') or url_for('book.vb'))
    same_day_bookings = current_user.booking_vb_same_day(schedule)
    if same_day_bookings >= 2 and not current_user.can(u'预约任意课程'):
        flash(u'您当天已经预约过%d节VB课程，不要太贪心哦~' % same_day_bookings, category='warning')
        return redirect(request.args.get('next') or url_for('book.vb'))
    elif same_day_bookings >= 1 and not (current_user.can(u'预约VB课程×2') or current_user.can(u'预约任意课程')):
        flash(u'您当天已经预约过VB课程，不要太贪心哦~', category='warning')
        return redirect(request.args.get('next') or url_for('book.vb'))
    current_user.book(schedule, u'预约')
    booking = Booking.query.filter_by(user_id=current_user.id, schedule_id=schedule.id).first()
    send_email(current_user.email, u'您已成功预约%s的%s课程' % (schedule.date, schedule.period.alias), 'book/mail/booking', booking=booking)
    flash(u'预约成功！', category='success')
    add_feed(user=current_user._get_current_object(), event=u'预约%s的%s课程' % (schedule.date, schedule.period.alias), category=u'book')
    if current_user.has_tag_name(u'未缴全款'):
        flash(u'您尚未缴齐全款，请先办理补齐全款手续，以免影响课程学习！', category='warning')
    booked_ipads_quantity = schedule.booked_ipads_quantity(lesson=current_user.last_punch.section.lesson)
    available_ipads_quantity = current_user.last_punch.section.lesson.available_ipads.count()
    if booked_ipads_quantity >= available_ipads_quantity:
        send_emails([user.email for user in User.users_can(u'管理iPad设备').all()], u'含有课程“%s”的iPad资源紧张' % current_user.last_punch.section.lesson.name, 'book/mail/short_of_ipad',
            booking=booking,
            booked_ipads_quantity=booked_ipads_quantity,
            available_ipads_quantity=available_ipads_quantity
        )
    return redirect(request.args.get('next') or url_for('book.vb'))


@book.route('/vb/wait/<int:id>')
@login_required
@permission_required(u'预约VB课程')
def wait_vb(id):
    schedule = Schedule.query.get_or_404(id)
    if not schedule.available:
        flash(u'所选时段尚未开放', category='error')
        return redirect(request.args.get('next') or url_for('book.vb'))
    if not schedule.unstarted:
        flash(u'所选时段已不接受预约', category='error')
        return redirect(request.args.get('next') or url_for('book.vb'))
    if not schedule.full:
        flash(u'该时段仍有名额，请直接预约', category='warning')
        return redirect(request.args.get('next') or url_for('book.vb'))
    if current_user.booked(schedule):
        flash(u'您已经预约过该时段，请不要重复预约', category='warning')
        return redirect(request.args.get('next') or url_for('book.vb'))
    if current_user.booking_y_gre_same_day(schedule):
        flash(u'您当天已经预约过Y-GRE课程，不要太贪心哦~', category='warning')
        return redirect(request.args.get('next') or url_for('book.vb'))
    same_day_bookings = current_user.booking_vb_same_day(schedule)
    if same_day_bookings >= 2 and not current_user.can(u'预约任意课程'):
        flash(u'您当天已经预约过%d节VB课程，不要太贪心哦~' % same_day_bookings, category='warning')
        return redirect(request.args.get('next') or url_for('book.vb'))
    elif same_day_bookings >= 1 and not (current_user.can(u'预约VB课程×2') or current_user.can(u'预约任意课程')):
        flash(u'您当天已经预约过VB课程，不要太贪心哦~', category='warning')
        return redirect(request.args.get('next') or url_for('book.vb'))
    current_user.book(schedule, u'排队')
    flash(u'已将您加入候选名单', category='success')
    add_feed(user=current_user._get_current_object(), event=u'排队%s的%s课程' % (schedule.date, schedule.period.alias), category=u'book')
    return redirect(request.args.get('next') or url_for('book.vb'))


@book.route('/vb/unbook/<int:id>')
@login_required
@permission_required(u'预约VB课程')
def unbook_vb(id):
    schedule = Schedule.query.get_or_404(id)
    if not schedule.available:
        flash(u'所选时段尚未开放', category='error')
        return redirect(request.args.get('next') or url_for('book.vb'))
    if not schedule.unstarted:
        flash(u'所选时段已不能自行取消', category='error')
        return redirect(request.args.get('next') or url_for('book.vb'))
    if not current_user.booked(schedule):
        flash(u'您目前尚未预约该时段', category='error')
        return redirect(request.args.get('next') or url_for('book.vb'))
    waited_booking = current_user.unbook(schedule)
    flash(u'取消成功！', category='success')
    add_feed(user=current_user._get_current_object(), event=u'取消%s的%s课程' % (schedule.date, schedule.period.alias), category=u'book')
    if waited_booking:
        send_email(waited_booking.user.email, u'您已成功预约%s的%s课程' % (waited_booking.schedule.date, waited_booking.schedule.period.alias), 'book/mail/booking', booking=waited_booking)
        add_feed(user=waited_booking.user, event=u'预约%s的%s课程' % (waited_booking.schedule.date, waited_booking.schedule.period.alias), category=u'book')
        booked_ipads_quantity = waited_booking.schedule.booked_ipads_quantity(lesson=waited_booking.user.last_punch.section.lesson)
        available_ipads_quantity = waited_booking.user.last_punch.section.lesson.available_ipads.count()
        if booked_ipads_quantity >= available_ipads_quantity:
            send_emails([user.email for user in User.users_can(u'管理iPad设备').all()], u'含有课程“%s”的iPad资源紧张' % waited_booking.user.last_punch.section.lesson.name, 'book/mail/short_of_ipad',
                booking=waited_booking,
                booked_ipads_quantity=booked_ipads_quantity,
                available_ipads_quantity=available_ipads_quantity
            )
    return redirect(request.args.get('next') or url_for('book.vb'))


@book.route('/vb/miss/<int:id>')
@login_required
@permission_required(u'预约VB课程')
def miss_vb(id):
    schedule = Schedule.query.get_or_404(id)
    if not schedule.available:
        flash(u'所选时段尚未开放', category='error')
        return redirect(request.args.get('next') or url_for('book.vb'))
    if not schedule.started:
        flash(u'所选时段已不能自行取消', category='error')
        return redirect(request.args.get('next') or url_for('book.vb'))
    if not current_user.booked(schedule):
        flash(u'您目前尚未预约该时段', category='warning')
        return redirect(request.args.get('next') or url_for('book.vb'))
    current_user.miss(schedule)
    flash(u'取消成功！', category='success')
    add_feed(user=current_user._get_current_object(), event=u'取消%s的%s课程' % (schedule.date, schedule.period.alias), category=u'book')
    return redirect(request.args.get('next') or url_for('book.vb'))


@book.route('/y-gre')
@login_required
@permission_required(u'预约Y-GRE课程')
def y_gre():
    query = Schedule.query\
        .join(Period, Period.id == Schedule.period_id)\
        .join(CourseType, CourseType.id == Period.type_id)\
        .filter(CourseType.name == u'Y-GRE')\
        .filter(Schedule.available == True)\
        .filter(Schedule.date >= date.today())\
        .order_by(Schedule.date.asc())\
        .order_by(Period.id.asc())
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    schedules = pagination.items
    announcements = get_announcements(type_name=u'预约Y-GRE通知', user=current_user._get_current_object())
    return render_template('book/y_gre.html',
        pagination=pagination,
        schedules=schedules,
        announcements=announcements
    )


@book.route('/y-gre/book/<int:id>')
@login_required
@permission_required(u'预约Y-GRE课程')
def book_y_gre(id):
    schedule = Schedule.query.get_or_404(id)
    if not schedule.available:
        flash(u'所选时段尚未开放', category='error')
        return redirect(request.args.get('next') or url_for('book.y_gre'))
    if not schedule.unstarted:
        flash(u'所选时段已不接受预约', category='error')
        return redirect(request.args.get('next') or url_for('book.y_gre'))
    if schedule.full:
        flash(u'该时段名额已经约满', category='error')
        return redirect(request.args.get('next') or url_for('book.y_gre'))
    if current_user.booked(schedule):
        flash(u'您已经预约过该时段，请不要重复预约', category='warning')
        return redirect(request.args.get('next') or url_for('book.y_gre'))
    if current_user.booking_vb_same_day(schedule):
        flash(u'您当天已经预约过VB课程，不要太贪心哦~', category='warning')
        return redirect(request.args.get('next') or url_for('book.y_gre'))
    same_day_bookings = current_user.booking_y_gre_same_day(schedule)
    if same_day_bookings >= 1 and not current_user.can(u'预约任意课程'):
        flash(u'您当天已经预约过Y-GRE课程，不要太贪心哦~' % same_day_bookings, category='warning')
        return redirect(request.args.get('next') or url_for('book.y_gre'))
    current_user.book(schedule, u'预约')
    booking = Booking.query.filter_by(user_id=current_user.id, schedule_id=schedule.id).first()
    send_email(current_user.email, u'您已成功预约%s的%s课程' % (schedule.date, schedule.period.alias), 'book/mail/booking', booking=booking)
    flash(u'预约成功！', category='success')
    add_feed(user=current_user._get_current_object(), event=u'预约%s的%s课程' % (schedule.date, schedule.period.alias), category=u'book')
    if current_user.has_tag_name(u'未缴全款'):
        flash(u'您尚未缴齐全款，请先办理补齐全款手续，以免影响课程学习！', category='warning')
    booked_ipads_quantity = schedule.booked_ipads_quantity(lesson=current_user.last_punch.section.lesson)
    available_ipads_quantity = current_user.last_punch.section.lesson.available_ipads.count()
    if booked_ipads_quantity >= available_ipads_quantity:
        send_emails([user.email for user in User.users_can(u'管理iPad设备').all()], u'含有课程“%s”的iPad资源紧张' % current_user.last_punch.section.lesson.name, 'book/mail/short_of_ipad',
            booking=booking,
            booked_ipads_quantity=booked_ipads_quantity,
            available_ipads_quantity=available_ipads_quantity
        )
    return redirect(request.args.get('next') or url_for('book.y_gre'))


@book.route('/y-gre/wait/<int:id>')
@login_required
@permission_required(u'预约Y-GRE课程')
def wait_y_gre(id):
    schedule = Schedule.query.get_or_404(id)
    if not schedule.available:
        flash(u'所选时段尚未开放', category='error')
        return redirect(request.args.get('next') or url_for('book.y_gre'))
    if not schedule.unstarted:
        flash(u'所选时段已不接受预约', category='error')
        return redirect(request.args.get('next') or url_for('book.y_gre'))
    if not schedule.full:
        flash(u'该时段仍有名额，请直接预约', category='error')
        return redirect(request.args.get('next') or url_for('book.y_gre'))
    if current_user.booked(schedule):
        flash(u'您已经预约过该时段，请不要重复预约', category='warning')
        return redirect(request.args.get('next') or url_for('book.y_gre'))
    if current_user.booking_vb_same_day(schedule):
        flash(u'您当天已经预约过VB课程，不要太贪心哦~', category='warning')
        return redirect(request.args.get('next') or url_for('book.y_gre'))
    same_day_bookings = current_user.booking_y_gre_same_day(schedule)
    if same_day_bookings >= 1 and not current_user.can(u'预约任意课程'):
        flash(u'您当天已经预约过Y-GRE课程，不要太贪心哦~' % same_day_bookings, category='warning')
        return redirect(request.args.get('next') or url_for('book.y_gre'))
    current_user.book(schedule, u'排队')
    flash(u'已将您加入候选名单', category='success')
    add_feed(user=current_user._get_current_object(), event=u'排队%s的%s课程' % (schedule.date, schedule.period.alias), category=u'book')
    return redirect(request.args.get('next') or url_for('book.y_gre'))


@book.route('/y-gre/unbook/<int:id>')
@login_required
@permission_required(u'预约Y-GRE课程')
def unbook_y_gre(id):
    schedule = Schedule.query.get_or_404(id)
    if not schedule.available:
        flash(u'所选时段尚未开放', category='error')
        return redirect(request.args.get('next') or url_for('book.y_gre'))
    if not schedule.unstarted:
        flash(u'所选时段已不能自行取消', category='error')
        return redirect(request.args.get('next') or url_for('book.y_gre'))
    if not current_user.booked(schedule):
        flash(u'您目前尚未预约该时段', category='warning')
        return redirect(request.args.get('next') or url_for('book.y_gre'))
    waited_booking = current_user.unbook(schedule)
    flash(u'取消成功！', category='success')
    add_feed(user=current_user._get_current_object(), event=u'取消%s的%s课程' % (schedule.date, schedule.period.alias), category=u'book')
    if waited_booking:
        send_email(waited_booking.user.email, u'您已成功预约%s的%s课程' % (waited_booking.schedule.date, waited_booking.schedule.period.alias), 'book/mail/booking', booking=booking)
        add_feed(user=waited_booking.user, event=u'预约%s的%s课程' % (waited_booking.schedule.date, waited_booking.schedule.period.alias), category=u'book')
        booked_ipads_quantity = waited_booking.schedule.booked_ipads_quantity(lesson=waited_booking.user.last_punch.section.lesson)
        available_ipads_quantity = waited_booking.user.last_punch.section.lesson.available_ipads.count()
        if booked_ipads_quantity >= available_ipads_quantity:
            send_emails([user.email for user in User.users_can(u'管理iPad设备').all()], u'含有课程“%s”的iPad资源紧张' % waited_booking.user.last_punch.section.lesson.name, 'book/mail/short_of_ipad',
                booking=waited_booking,
                booked_ipads_quantity=booked_ipads_quantity,
                available_ipads_quantity=available_ipads_quantity
            )
    return redirect(request.args.get('next') or url_for('book.y_gre'))


@book.route('/y_gre/miss/<int:id>')
@login_required
@permission_required(u'预约Y-GRE课程')
def miss_y_gre(id):
    schedule = Schedule.query.get_or_404(id)
    if not schedule.available:
        flash(u'所选时段尚未开放', category='error')
        return redirect(request.args.get('next') or url_for('book.y_gre'))
    if not schedule.started:
        flash(u'所选时段已不能自行取消', category='error')
        return redirect(request.args.get('next') or url_for('book.y_gre'))
    if not current_user.booked(schedule):
        flash(u'您目前尚未预约该时段', category='warning')
        return redirect(request.args.get('next') or url_for('book.y_gre'))
    current_user.miss(schedule)
    flash(u'取消成功！', category='success')
    add_feed(user=current_user._get_current_object(), event=u'取消%s的%s课程' % (schedule.date, schedule.period.alias), category=u'book')
    return redirect(request.args.get('next') or url_for('book.y_gre'))