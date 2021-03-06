# -*- coding: utf-8 -*-

from datetime import datetime, date, time, timedelta
from json import dumps
from sqlalchemy import or_, and_
from flask import render_template, redirect, url_for, abort, flash, current_app, make_response, request, jsonify
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import manage
from .forms import SearchForm
from .forms import BookingTokenForm, RentiPadForm, RentalEmailForm, ConfirmiPadForm, SelectLessonForm, RentiPadByLessonForm, iPadSerialForm
from .forms import PunchSectionForm, ConfirmPunchForm, EditPunchLessonForm, EditPunchSectionForm
from .forms import NewScheduleForm, NewPeriodForm, EditPeriodForm
from .forms import NewAssignmentScoreForm, EditAssignmentScoreForm
from .forms import NewVBTestScoreForm, EditVBTestScoreForm
from .forms import NewYGRETestScoreForm, EditYGRETestScoreForm
from .forms import NewGRETestScoreForm, EditGRETestScoreForm
from .forms import NewTOEFLTestScoreForm, EditTOEFLTestScoreForm
from .forms import NewUserForm, NewAdminForm, ConfirmUserForm, RestoreUserForm
from .forms import NewEducationRecordForm, NewEmploymentRecordForm, NewScoreRecordForm, NewInviterForm, NewPurchaseForm
from .forms import EditNameForm, EditGenderForm, EditBirthdateForm, EditIDNumberForm, EditUserTagForm, EditStudentRoleForm, EditUserRoleForm
from .forms import EditEmailForm, EditMobileForm, EditAddressForm, EditQQForm, EditWeChatForm
from .forms import EditEmergencyContactNameForm, EditEmergencyContactRelationshipForm, EditEmergencyContactMobileForm
from .forms import EditPurposeForm, EditReferrerForm
from .forms import EditApplicationForm
from .forms import EditWorkInSameFieldForm, EditDeformityForm
from .forms import EditVBCourseForm, EditYGRECourseForm
from .forms import NewCourseForm, EditCourseForm
from .forms import NewGroupForm, NewGroupMemberForm
from .forms import NewTagForm, EditTagForm
from .forms import NewiPadForm, EditiPadForm, FilteriPadForm
from .forms import EditStudyPlanForm
from .forms import NewNotaBeneForm, EditNotaBeneForm
from .forms import NewFeedbackForm, EditFeedbackForm
from .forms import NewAnnouncementForm, EditAnnouncementForm
from .forms import NewProductForm, EditProductForm
from .forms import NewRoleForm, EditRoleForm
from .forms import NewPermissionForm, EditPermissionForm
from .. import db
from ..models import Permission, Role, User, IDType, Gender, Relationship
from ..models import PurposeType, ReferrerType, InvitationType
from ..models import EducationRecord, EducationType, EmploymentRecord, ScoreRecord, ScoreType
from ..models import Course, CourseType, CourseRegistration
from ..models import GroupRegistration
from ..models import Tag, UserTag
from ..models import Booking, BookingState
from ..models import Rental
from ..models import Punch
from ..models import Period, Schedule
from ..models import Lesson, Section
from ..models import Assignment, AssignmentScore, AssignmentScoreGrade
from ..models import Test, VBTestScore, YGRETestScore, GREAWScore, ScoreLabel, GRETest, GRETestScore, TOEFLTest, TOEFLTestScore
from ..models import iPad, iPadState, iPadContent, Room
from ..models import StudyPlan, NotaBene, Feedback
from ..models import Announcement
from ..models import Product, Purchase
from ..models import Feed
from ..email import send_email, send_emails
from ..notify import get_announcements, add_feed
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
    if room_id == 0:
        ipads_num = iPad.query\
            .filter_by(room_id=None, deleted=False)\
            .count()
    else:
        ipads_num = iPad.query\
            .filter_by(room_id=room_id, deleted=False)\
            .count()
    announcements = get_announcements(type_name=u'管理主页通知', user=current_user._get_current_object())
    return render_template('manage/summary.html',
        show_summary_ipad_1103=show_summary_ipad_1103,
        show_summary_ipad_1707=show_summary_ipad_1707,
        show_summary_ipad_others=show_summary_ipad_others,
        room_id=room_id,
        ipads_num=ipads_num,
        announcements=announcements
    )


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
@login_required
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
@login_required
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
                'l4_9': {
                    'total': Booking.of_current_vb_schedule([u'L4', u'L5', u'L6', u'L7', u'L8', u'L9']),
                    'show_up': Booking.show_ups([u'L4', u'L5', u'L6', u'L7', u'L8', u'L9']),
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
    show_today_bookings = True
    show_future_bookings = False
    show_history_bookings = False
    if current_user.is_authenticated:
        show_today_bookings = bool(request.cookies.get('show_today_bookings', '1'))
        show_future_bookings = bool(request.cookies.get('show_future_bookings', ''))
        show_history_bookings = bool(request.cookies.get('show_history_bookings', ''))
    if show_today_bookings:
        query = Booking.query\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .filter(Schedule.date == date.today())\
            .order_by(Schedule.period_id.asc())\
            .order_by(Booking.timestamp.desc())
    if show_history_bookings:
        query = Booking.query\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .filter(Schedule.date < date.today())\
            .order_by(Schedule.date.desc())\
            .order_by(Schedule.period_id.asc())\
            .order_by(Booking.timestamp.desc())
    if show_future_bookings:
        query = Booking.query\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .filter(Schedule.date > date.today())\
            .order_by(Schedule.date.asc())\
            .order_by(Schedule.period_id.asc())\
            .order_by(Booking.timestamp.desc())
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    bookings = pagination.items
    return render_template('manage/booking.html',
        show_today_bookings=show_today_bookings,
        show_future_bookings=show_future_bookings,
        show_history_bookings=show_history_bookings,
        pagination=pagination,
        bookings=bookings
    )


@manage.route('/booking/today')
@login_required
@permission_required(u'管理课程预约')
def today_bookings():
    resp = make_response(redirect(url_for('manage.booking')))
    resp.set_cookie('show_today_bookings', '1', max_age=30*24*60*60)
    resp.set_cookie('show_future_bookings', '', max_age=30*24*60*60)
    resp.set_cookie('show_history_bookings', '', max_age=30*24*60*60)
    return resp


@manage.route('/booking/future')
@login_required
@permission_required(u'管理课程预约')
def future_bookings():
    resp = make_response(redirect(url_for('manage.booking')))
    resp.set_cookie('show_today_bookings', '', max_age=30*24*60*60)
    resp.set_cookie('show_future_bookings', '1', max_age=30*24*60*60)
    resp.set_cookie('show_history_bookings', '', max_age=30*24*60*60)
    return resp


@manage.route('/booking/history')
@login_required
@permission_required(u'管理课程预约')
def history_bookings():
    resp = make_response(redirect(url_for('manage.booking')))
    resp.set_cookie('show_today_bookings', '', max_age=30*24*60*60)
    resp.set_cookie('show_future_bookings', '', max_age=30*24*60*60)
    resp.set_cookie('show_history_bookings', '1', max_age=30*24*60*60)
    return resp


@manage.route('/booking/set-state/valid/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(u'管理课程预约')
def set_booking_state_valid(user_id, schedule_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    if booking is None:
        flash(u'该预约记录不存在', category='error')
        return redirect(request.args.get('next') or url_for('manage.booking'))
    if booking.schedule.full:
        flash(u'该时段名额已经约满', category='error')
        return redirect(request.args.get('next') or url_for('manage.booking'))
    booking.set_state(u'预约')
    db.session.commit()
    send_email(booking.user.email, u'您已成功预约%s的%s课程' % (booking.schedule.date, booking.schedule.period.alias), 'book/mail/booking', booking=booking)
    flash(u'给%s预约%s的%s课程' % (booking.user.name_alias, booking.schedule.date, booking.schedule.period.alias), category='success')
    add_feed(user=current_user._get_current_object(), event=u'给%s预约%s的%s课程' % (booking.user.name_alias, booking.schedule.date, booking.schedule.period.alias), category=u'manage')
    booked_ipads_quantity = schedule.booked_ipads_quantity(lesson=booking.user.last_punch.section.lesson)
    available_ipads_quantity = booking.user.last_punch.section.lesson.available_ipads.count()
    if booked_ipads_quantity >= available_ipads_quantity:
        send_emails([user.email for user in User.users_can(u'管理iPad设备').all()], u'含有课程“%s”的iPad资源紧张' % booking.user.last_punch.section.lesson.name, 'book/mail/short_of_ipad',
            booking=booking,
            booked_ipads_quantity=booked_ipads_quantity,
            available_ipads_quantity=available_ipads_quantity
        )
    return redirect(request.args.get('next') or url_for('manage.booking'))


@manage.route('/booking/set-state/wait/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(u'管理课程预约')
def set_booking_state_wait(user_id, schedule_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    if booking is None:
        flash(u'该预约记录不存在', category='error')
        return redirect(request.args.get('next') or url_for('manage.booking'))
    booking.set_state(u'排队')
    flash(u'给%s排队%s的%s课程' % (booking.user.name_alias, booking.schedule.date, booking.schedule.period.alias), category='success')
    add_feed(user=current_user._get_current_object(), event=u'给%s排队%s的%s课程' % (booking.user.name_alias, booking.schedule.date, booking.schedule.period.alias), category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.booking'))


@manage.route('/booking/set-state/invalid/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(u'管理课程预约')
def set_booking_state_invalid(user_id, schedule_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    if booking is None:
        flash(u'该预约记录不存在', category='error')
        return redirect(request.args.get('next') or url_for('manage.booking'))
    booking.set_state(u'失效')
    flash(u'标记%s预约的%s的%s课程为：失效' % (booking.user.name_alias, booking.schedule.date, booking.schedule.period.alias), category='success')
    add_feed(user=current_user._get_current_object(), event=u'标记%s预约的%s的%s课程为：失效' % (booking.user.name_alias, booking.schedule.date, booking.schedule.period.alias), category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.booking'))


@manage.route('/booking/set-state/kept/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(u'管理课程预约')
def set_booking_state_kept(user_id, schedule_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    if booking is None:
        flash(u'该预约记录不存在', category='error')
        return redirect(request.args.get('next') or url_for('manage.booking'))
    booking.set_state(u'赴约')
    flash(u'标记%s预约的%s的%s课程为：赴约' % (booking.user.name_alias, booking.schedule.date, booking.schedule.period.alias), category='success')
    add_feed(user=current_user._get_current_object(), event=u'标记%s预约的%s的%s课程为：赴约' % (booking.user.name_alias, booking.schedule.date, booking.schedule.period.alias), category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.booking'))


@manage.route('/booking/set-state/late/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(u'管理课程预约')
def set_booking_state_late(user_id, schedule_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    if booking is None:
        flash(u'该预约记录不存在', category='error')
        return redirect(request.args.get('next') or url_for('manage.booking'))
    booking.set_state(u'迟到')
    flash(u'标记%s预约的%s的%s课程为：迟到' % (booking.user.name_alias, booking.schedule.date, booking.schedule.period.alias), category='success')
    add_feed(user=current_user._get_current_object(), event=u'标记%s预约的%s的%s课程为：迟到' % (booking.user.name_alias, booking.schedule.date, booking.schedule.period.alias), category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.booking'))


@manage.route('/booking/set-state/missed/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(u'管理课程预约')
def set_booking_state_missed(user_id, schedule_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    if booking is None:
        flash(u'该预约记录不存在', category='error')
        return redirect(request.args.get('next') or url_for('manage.booking'))
    booking.set_state(u'爽约')
    flash(u'标记%s预约的%s的%s课程为：爽约' % (booking.user.name_alias, booking.schedule.date, booking.schedule.period.alias), category='success')
    add_feed(user=current_user._get_current_object(), event=u'标记%s预约的%s的%s课程为：爽约' % (booking.user.name_alias, booking.schedule.date, booking.schedule.period.alias), category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.booking'))


@manage.route('/booking/set-state/canceled/<int:user_id>/<int:schedule_id>')
@login_required
@permission_required(u'管理课程预约')
def set_booking_state_canceled(user_id, schedule_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    booking = Booking.query.filter_by(user_id=user_id, schedule_id=schedule_id).first()
    if booking is None:
        flash(u'该预约记录不存在', category='error')
        return redirect(request.args.get('next') or url_for('manage.booking'))
    waited_booking = booking.set_state(u'取消')
    db.session.commit()
    flash(u'标记%s预约的%s的%s课程为：取消' % (booking.user.name_alias, booking.schedule.date, booking.schedule.period.alias), category='success')
    add_feed(user=current_user._get_current_object(), event=u'标记%s预约的%s的%s课程为：取消' % (booking.user.name_alias, booking.schedule.date, booking.schedule.period.alias), category=u'manage')
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
    return redirect(request.args.get('next') or url_for('manage.booking'))


def time_now(utcOffset=0):
    t = datetime.utcnow() + timedelta(hours=utcOffset)
    return t.time()


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
    add_feed(user=current_user._get_current_object(), event=u'批量标记“爽约”：%s条；标记“失效”：%s条' % (len(history_unmarked_missed_bookings + today_unmarked_missed_bookings), len(history_unmarked_waited_bookings + today_unmarked_waited_bookings)), category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.booking'))


@manage.route('/rental')
@login_required
@permission_required(u'管理iPad借阅')
def rental():
    show_today_rentals = True
    show_today_rentals_1103 = False
    show_today_rentals_1707 = False
    show_history_rentals = False
    if current_user.is_authenticated:
        show_today_rentals = bool(request.cookies.get('show_today_rentals', '1'))
        show_today_rentals_1103 = bool(request.cookies.get('show_today_rentals_1103', ''))
        show_today_rentals_1707 = bool(request.cookies.get('show_today_rentals_1707', ''))
        show_history_rentals = bool(request.cookies.get('show_history_rentals', ''))
    if show_today_rentals:
        query = Rental.query\
            .join(Schedule, Schedule.id == Rental.schedule_id)\
            .filter(Schedule.date >= date.today())\
            .order_by(Rental.rent_time.desc())
    if show_today_rentals_1103:
        query = Rental.query\
            .join(Schedule, Schedule.id == Rental.schedule_id)\
            .join(iPad, iPad.id == Rental.ipad_id)\
            .join(Room, Room.id == iPad.room_id)\
            .filter(Room.name == u'1103')\
            .filter(Schedule.date >= date.today())\
            .order_by(Rental.rent_time.desc())
    if show_today_rentals_1707:
        query = Rental.query\
            .join(Schedule, Schedule.id == Rental.schedule_id)\
            .join(iPad, iPad.id == Rental.ipad_id)\
            .join(Room, Room.id == iPad.room_id)\
            .filter(Room.name == u'1707')\
            .filter(Schedule.date >= date.today())\
            .order_by(Rental.rent_time.desc())
    if show_history_rentals:
        query = Rental.query\
            .join(Schedule, Schedule.id == Rental.schedule_id)\
            .filter(Schedule.date < date.today())\
            .order_by(Schedule.date.desc())\
            .order_by(Rental.return_time.desc())
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    rentals = pagination.items
    return render_template('manage/rental.html',
        show_today_rentals=show_today_rentals,
        show_today_rentals_1103=show_today_rentals_1103,
        show_today_rentals_1707=show_today_rentals_1707,
        show_history_rentals=show_history_rentals,
        pagination=pagination,
        rentals=rentals
    )


@manage.route('/rental/today')
@login_required
@permission_required(u'管理iPad借阅')
def today_rentals():
    resp = make_response(redirect(url_for('manage.rental')))
    resp.set_cookie('show_today_rentals', '1', max_age=30*24*60*60)
    resp.set_cookie('show_today_rentals_1103', '', max_age=30*24*60*60)
    resp.set_cookie('show_today_rentals_1707', '', max_age=30*24*60*60)
    resp.set_cookie('show_history_rentals', '', max_age=30*24*60*60)
    return resp


@manage.route('/rental/today/1103')
@login_required
@permission_required(u'管理iPad借阅')
def today_rentals_1103():
    resp = make_response(redirect(url_for('manage.rental')))
    resp.set_cookie('show_today_rentals', '', max_age=30*24*60*60)
    resp.set_cookie('show_today_rentals_1103', '1', max_age=30*24*60*60)
    resp.set_cookie('show_today_rentals_1707', '', max_age=30*24*60*60)
    resp.set_cookie('show_history_rentals', '', max_age=30*24*60*60)
    return resp


@manage.route('/rental/today/1707')
@login_required
@permission_required(u'管理iPad借阅')
def today_rentals_1707():
    resp = make_response(redirect(url_for('manage.rental')))
    resp.set_cookie('show_today_rentals', '', max_age=30*24*60*60)
    resp.set_cookie('show_today_rentals_1103', '', max_age=30*24*60*60)
    resp.set_cookie('show_today_rentals_1707', '1', max_age=30*24*60*60)
    resp.set_cookie('show_history_rentals', '', max_age=30*24*60*60)
    return resp


@manage.route('/rental/history')
@login_required
@permission_required(u'管理iPad借阅')
def history_rentals():
    resp = make_response(redirect(url_for('manage.rental')))
    resp.set_cookie('show_today_rentals', '', max_age=30*24*60*60)
    resp.set_cookie('show_today_rentals_1103', '', max_age=30*24*60*60)
    resp.set_cookie('show_today_rentals_1707', '', max_age=30*24*60*60)
    resp.set_cookie('show_history_rentals', '1', max_age=30*24*60*60)
    return resp


@manage.route('/rental/rent/step-1', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_1():
    form = BookingTokenForm()
    if form.validate_on_submit():
        booking = Booking.query.filter_by(token=form.token.data).first()
        if not booking:
            flash(u'预约码无效', category='error')
            return redirect(url_for('manage.rental_rent_step_1', next=request.args.get('next')))
        if not booking.valid or booking.kept or booking.late:
            flash(u'该预约处于“%s”状态' % booking.state.name, category='error')
            return redirect(url_for('manage.rental_rent_step_1', next=request.args.get('next')))
        if booking.schedule.date != date.today():
            flash(u'预约的日期（%s）不在今天' % booking.schedule.date, category='error')
            return redirect(url_for('manage.rental_rent_step_1', next=request.args.get('next')))
        if booking.schedule.ended:
            booking.set_state(u'爽约')
        if booking.schedule.started_n_min(n_min=current_app.config['TOLERATE_MINUTES']):
            booking.set_state(u'迟到')
        if booking.schedule.unstarted_n_min(n_min=current_app.config['TOLERATE_MINUTES']):
            booking.set_state(u'赴约')
        return redirect(url_for('manage.rental_rent_step_2', user_id=booking.user_id, schedule_id=booking.schedule_id, next=request.args.get('next')))
    return render_template('manage/rental_rent_step_1.html', form=form)


@manage.route('/rental/rent/step-2/<int:user_id>/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_2(user_id, schedule_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    if user.has_tag_name(u'未缴全款'):
        flash(u'%s尚未缴齐全款，需要先办理补齐全款手续！' % user.name_alias, category='warning')
    schedule = Schedule.query.get_or_404(schedule_id)
    form = RentiPadForm(user=user)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_rent_step_3', user_id=user_id, ipad_id=int(form.ipad.data), schedule_id=schedule_id, next=request.args.get('next')))
    return render_template('manage/rental_rent_step_2.html', user=user, schedule=schedule, form=form)


@manage.route('/rental/rent/step-3/<int:user_id>/<int:ipad_id>/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_3(user_id, ipad_id, schedule_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
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
            return redirect(url_for('manage.rental_rent_step_3', user_id=user_id, ipad_id=ipad_id, schedule_id=schedule_id, next=request.args.get('next')))
        if ipad.state.name not in [u'待机', u'候补']:
            flash(u'序列号为%s的iPad处于“%s”状态，不能借出' % (ipad.serial, ipad.state.name), category='error')
            return redirect(url_for('manage.rental_rent_step_3', user_id=user_id, ipad_id=ipad_id, schedule_id=schedule_id, next=request.args.get('next')))
        if user.has_unreturned_ipads:
            flash(u'%s有未归换的iPad' % user.name, category='error')
            return redirect(url_for('manage.rental_rent_step_3', user_id=user_id, ipad_id=ipad_id, schedule_id=schedule_id, next=request.args.get('next')))
        rental = Rental(user_id=user.id, ipad_id=ipad.id, schedule_id=schedule.id, rent_agent_id=current_user.id)
        db.session.add(rental)
        ipad.set_state(u'借出', battery_life=form.battery_life.data, modified_by=current_user._get_current_object())
        flash(u'iPad借出信息登记成功', category='success')
        add_feed(user=user, event=u'借出iPad：%s' % ipad.alias2, category=u'rental')
        add_feed(user=current_user._get_current_object(), event=u'将iPad“%s”借给%s' % (ipad.alias2, user.name_alias), category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.rental'))
    return render_template('manage/rental_rent_step_3.html', user=user, ipad=ipad, schedule=schedule, form=form)


@manage.route('/rental/rent/step-2-lesson/<int:user_id>/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_2_lesson(user_id, schedule_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    schedule = Schedule.query.get_or_404(schedule_id)
    form = SelectLessonForm()
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_rent_step_3_lesson', user_id=user_id, lesson_id=int(form.lesson.data), schedule_id=schedule_id, next=request.args.get('next')))
    return render_template('manage/rental_rent_step_2_lesson.html', user=user, schedule=schedule, form=form)


@manage.route('rental/rent/step-3-lesson/<int:user_id>/<int:lesson_id>/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_3_lesson(user_id, lesson_id, schedule_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    lesson = Lesson.query.get_or_404(lesson_id)
    schedule = Schedule.query.get_or_404(schedule_id)
    form = RentiPadByLessonForm(lesson=lesson)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_rent_step_4_lesson', user_id=user_id, lesson_id=lesson_id, ipad_id=int(form.ipad.data), schedule_id=schedule_id, next=request.args.get('next')))
    return render_template('manage/rental_rent_step_3_lesson.html', user=user, lesson=lesson, schedule=schedule, form=form)


@manage.route('rental/rent/step-4-lesson/<int:user_id>/<int:lesson_id>/<int:ipad_id>/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_4_lesson(user_id, lesson_id, ipad_id, schedule_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
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
            return redirect(url_for('manage.rental_rent_step_4_lesson', user_id=user_id, lesson_id=lesson_id, ipad_id=ipad_id, schedule_id=schedule_id, next=request.args.get('next')))
        if ipad.state.name not in [u'待机', u'候补']:
            flash(u'序列号为%s的iPad处于“%s”状态，不能借出' % (ipad.serial, ipad.state.name), category='error')
            return redirect(url_for('manage.rental_rent_step_4_lesson', user_id=user_id, lesson_id=lesson_id, ipad_id=ipad_id, schedule_id=schedule_id, next=request.args.get('next')))
        if user.has_unreturned_ipads:
            flash(u'%s有未归换的iPad' % user.name, category='error')
            return redirect(url_for('manage.rental_rent_step_4_lesson', user_id=user_id, lesson_id=lesson_id, ipad_id=ipad_id, schedule_id=schedule_id, next=request.args.get('next')))
        rental = Rental(user_id=user.id, ipad_id=ipad.id, schedule_id=schedule.id, rent_agent_id=current_user.id)
        db.session.add(rental)
        ipad.set_state(u'借出', battery_life=form.battery_life.data, modified_by=current_user._get_current_object())
        flash(u'iPad借出信息登记成功', category='success')
        add_feed(user=user, event=u'借出iPad：%s' % ipad.alias2, category=u'rental')
        add_feed(user=current_user._get_current_object(), event=u'将iPad“%s”借给%s' % (ipad.alias2, user.name_alias), category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.rental'))
    return render_template('manage/rental_rent_step_4_lesson.html', user=user, lesson=lesson, ipad=ipad, schedule=schedule, form=form)


@manage.route('/rental/rent/step-1-alt', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_1_alt():
    form = RentalEmailForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower(), created=True, activated=True, deleted=False).first()
        if user is None:
            flash(u'邮箱不存在', category='error')
            return redirect(url_for('manage.rental_rent_step_1_alt', next=request.args.get('next')))
        return redirect(url_for('manage.rental_rent_step_2_alt', user_id=user.id, next=request.args.get('next')))
    return render_template('manage/rental_rent_step_1_alt.html', form=form)


@manage.route('/rental/rent/step-2-alt/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_2_alt(user_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    if user.has_tag_name(u'未缴全款'):
        flash(u'%s尚未缴齐全款，需要先办理补齐全款手续！' % user.name_alias, category='warning')
    form = RentiPadForm(user=user)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_rent_step_3_alt', user_id=user_id, ipad_id=int(form.ipad.data), next=request.args.get('next')))
    return render_template('manage/rental_rent_step_2_alt.html', user=user, form=form)


@manage.route('/rental/rent/step-3-alt/<int:user_id>/<int:ipad_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_3_alt(user_id, ipad_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    ipad = iPad.query.get_or_404(ipad_id)
    if ipad.deleted:
        abort(404)
    schedule = Schedule.current_schedule(user.last_punch.section.lesson.type.name)
    if schedule is None:
        flash(u'目前没有开放的%s时段，无法借出iPad' % user.last_punch.section.lesson.type.name, category='error')
        return redirect(request.args.get('next') or url_for('manage.rental'))
    form = ConfirmiPadForm()
    if form.validate_on_submit():
        serial = form.serial.data
        if serial != ipad.serial:
            flash(u'iPad序列号信息有误', category='error')
            return redirect(url_for('manage.rental_rent_step_3_alt', user_id=user_id, ipad_id=ipad_id, next=request.args.get('next')))
        if ipad.state.name not in [u'待机', u'候补']:
            flash(u'序列号为%s的iPad处于“%s”状态，不能借出' % (ipad.serial, ipad.state.name), category='error')
            return redirect(url_for('manage.rental_rent_step_3_alt', user_id=user_id, ipad_id=ipad_id, next=request.args.get('next')))
        if user.has_unreturned_ipads:
            flash(u'%s有未归换的iPad' % user.name, category='error')
            return redirect(url_for('manage.rental_rent_step_3_alt', user_id=user_id, ipad_id=ipad_id, next=request.args.get('next')))
        rental = Rental(user_id=user.id, ipad_id=ipad.id, schedule_id=schedule.id, walk_in=True, rent_agent_id=current_user.id)
        db.session.add(rental)
        ipad.set_state(u'借出', battery_life=form.battery_life.data, modified_by=current_user._get_current_object())
        flash(u'iPad借出信息登记成功', category='success')
        add_feed(user=user, event=u'借出iPad：%s' % ipad.alias2, category=u'rental')
        add_feed(user=current_user._get_current_object(), event=u'将iPad“%s”借给%s' % (ipad.alias2, user.name_alias), category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.rental'))
    return render_template('manage/rental_rent_step_3_alt.html', user=user, ipad=ipad, form=form)


@manage.route('/rental/rent/step-2-lesson-alt/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_2_lesson_alt(user_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    form = SelectLessonForm()
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_rent_step_3_lesson_alt', user_id=user_id, lesson_id=int(form.lesson.data), next=request.args.get('next')))
    return render_template('manage/rental_rent_step_2_lesson_alt.html', user=user, form=form)


@manage.route('rental/rent/step-3-lesson-alt/<int:user_id>/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_3_lesson_alt(user_id, lesson_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    lesson = Lesson.query.get_or_404(lesson_id)
    form = RentiPadByLessonForm(lesson=lesson)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_rent_step_4_lesson_alt', user_id=user_id, lesson_id=lesson_id, ipad_id=int(form.ipad.data), next=request.args.get('next')))
    return render_template('manage/rental_rent_step_3_lesson_alt.html', user=user, lesson=lesson, form=form)


@manage.route('rental/rent/step-4-lesson-alt/<int:user_id>/<int:lesson_id>/<int:ipad_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_rent_step_4_lesson_alt(user_id, lesson_id, ipad_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    lesson = Lesson.query.get_or_404(lesson_id)
    ipad = iPad.query.get_or_404(ipad_id)
    if ipad.deleted:
        abort(404)
    schedule = Schedule.current_schedule(lesson.type.name)
    if schedule is None:
        flash(u'目前没有开放的%s时段，无法借出iPad' % lesson.type.name, category='error')
        return redirect(request.args.get('next') or url_for('manage.rental'))
    form = ConfirmiPadForm()
    if form.validate_on_submit():
        serial = form.serial.data
        if serial != ipad.serial:
            flash(u'iPad序列号信息有误', category='error')
            return redirect(url_for('manage.rental_rent_step_4_lesson_alt', user_id=user_id, lesson_id=lesson_id, ipad_id=ipad_id, next=request.args.get('next')))
        if ipad.state.name not in [u'待机', u'候补']:
            flash(u'序列号为%s的iPad处于“%s”状态，不能借出' % (ipad.serial, ipad.state.name), category='error')
            return redirect(url_for('manage.rental_rent_step_4_lesson_alt', user_id=user_id, lesson_id=lesson_id, ipad_id=ipad_id, next=request.args.get('next')))
        if user.has_unreturned_ipads:
            flash(u'%s有未归换的iPad' % user.name, category='error')
            return redirect(url_for('manage.rental_rent_step_4_lesson_alt', user_id=user_id, lesson_id=lesson_id, ipad_id=ipad_id, next=request.args.get('next')))
        rental = Rental(user_id=user.id, ipad_id=ipad.id, schedule_id=schedule.id, walk_in=True, rent_agent_id=current_user.id)
        db.session.add(rental)
        ipad.set_state(u'借出', battery_life=form.battery_life.data, modified_by=current_user._get_current_object())
        flash(u'iPad借出信息登记成功', category='success')
        add_feed(user=user, event=u'借出iPad：%s' % ipad.alias2, category=u'rental')
        add_feed(user=current_user._get_current_object(), event=u'将iPad“%s”借给%s' % (ipad.alias2, user.name_alias), category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.rental'))
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
            return redirect(url_for('manage.rental_return_step_1', next=request.args.get('next')))
        if ipad.state.name != u'借出':
            flash(u'序列号为%s的iPad处于%s状态，尚未借出' % (serial, ipad.state.name), category='error')
            return redirect(url_for('manage.rental_return_step_1', next=request.args.get('next')))
        rental = Rental.query.filter_by(ipad_id=ipad.id, returned=False).first()
        if rental is None:
            flash(u'没有序列号为%s的iPad的借阅记录' % serial, category='error')
            return redirect(url_for('manage.rental_return_step_1', next=request.args.get('next')))
        if not form.root.data:
            rental.set_returned(return_agent_id=current_user.id, ipad_state=u'维护')
            db.session.commit()
            send_emails([user.email for user in User.users_can(u'管理iPad设备').all()], u'iPad“%s”处于维护状态' % ipad.alias2, 'manage/mail/maintain_ipad',
                ipad=ipad,
                time=datetime.utcnow(),
                manager=current_user._get_current_object()
            )
            flash(u'已回收序列号为%s的iPad，并设为维护状态' % serial, category='warning')
            add_feed(user=user, event=u'归还iPad：%s' % ipad.alias2, category=u'rental')
            add_feed(user=current_user._get_current_object(), event=u'将iPad“%s”从%s回收，并设为维护状态' % (ipad.alias2, user.name_alias), category=u'manage')
            return redirect(url_for('manage.rental_return_step_2', user_id=rental.user_id, next=request.args.get('next')))
        if not form.battery.data:
            rental.set_returned(return_agent_id=current_user.id, ipad_state=u'充电')
            flash(u'已回收序列号为%s的iPad，并设为充电状态' % serial, category='warning')
            add_feed(user=user, event=u'归还iPad：%s' % ipad.alias2, category=u'rental')
            add_feed(user=current_user._get_current_object(), event=u'将iPad“%s”从%s回收，并设为充电状态' % (ipad.alias2, user.name_alias), category=u'manage')
            return redirect(url_for('manage.rental_return_step_2', user_id=rental.user_id, next=request.args.get('next')))
        rental.set_returned(return_agent_id=current_user.id)
        flash(u'已回收序列号为%s的iPad' % serial, category='success')
        add_feed(user=user, event=u'归还iPad：%s' % ipad.alias2, category=u'rental')
        add_feed(user=current_user._get_current_object(), event=u'将iPad“%s”从%s回收' % (ipad.alias2, user.name_alias), category=u'manage')
        return redirect(url_for('manage.rental_return_step_2', user_id=rental.user_id, next=request.args.get('next')))
    return render_template('manage/rental_return_step_1.html', form=form)


@manage.route('/rental/return/step-2/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_return_step_2(user_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    form = PunchSectionForm(user=user)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_return_step_3', user_id=user_id, section_id=int(form.section.data), next=request.args.get('next')))
    return render_template('manage/rental_return_step_2.html', user=user, form=form)


@manage.route('/rental/return/step-3/<int:user_id>/<int:section_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_return_step_3(user_id, section_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    section = Section.query.get_or_404(section_id)
    form = ConfirmPunchForm()
    if form.validate_on_submit():
        user.punch(section=section)
        flash(u'已保存%s的进度信息为：%s' % (user.name, section.alias2), category='success')
        add_feed(user=user, event=u'研修进度打卡：%s' % section.alias2, category=u'punch')
        add_feed(user=current_user._get_current_object(), event=u'保存%s的进度信息为：%s' % (user.name_alias, section.alias2), category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.rental'))
    return render_template('manage/rental_return_step_3.html', user=user, section=section, form=form)


@manage.route('/rental/return/step-1-alt', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_return_step_1_alt():
    form = RentalEmailForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower(), created=True, activated=True, deleted=False).first()
        if user is None:
            flash(u'邮箱不存在', category='error')
            return redirect(url_for('manage.rental_return_step_1_alt', next=request.args.get('next')))
        return redirect(url_for('manage.rental_return_step_2_alt', user_id=user.id, next=request.args.get('next')))
    return render_template('manage/rental_return_step_1_alt.html', form=form)


@manage.route('/rental/return/step-2-alt/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_return_step_2_alt(user_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    form = PunchSectionForm(user=user)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_return_step_3_alt', user_id=user_id, section_id=int(form.section.data), next=request.args.get('next')))
    return render_template('manage/rental_return_step_2_alt.html', user=user, form=form)


@manage.route('/rental/return/step-3-alt/<int:user_id>/<int:section_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_return_step_3_alt(user_id, section_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    section = Section.query.get_or_404(section_id)
    form = ConfirmPunchForm()
    if form.validate_on_submit():
        user.punch(section=section)
        flash(u'已保存%s的进度信息为：%s' % (user.name, section.alias2), category='success')
        add_feed(user=user, event=u'研修进度打卡：%s' % section.alias2, category=u'punch')
        add_feed(user=current_user._get_current_object(), event=u'保存%s的进度信息为：%s' % (user.name_alias, section.alias2), category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.rental'))
    return render_template('manage/rental_return_step_3_alt.html', user=user, section=section, form=form)


@manage.route('/rental/exchange/step-1/<int:rental_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_exchange_step_1(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    if rental.returned:
        flash(u'iPad已处于归还状态', category='error')
        return redirect(request.args.get('next') or url_for('manage.rental'))
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
            send_emails([user.email for user in User.users_can(u'管理iPad设备').all()], u'iPad“%s”处于维护状态' % ipad.alias2, 'manage/mail/maintain_ipad',
                ipad=ipad,
                time=datetime.utcnow(),
                manager=current_user._get_current_object()
            )
            flash(u'已回收序列号为%s的iPad，并设为维护状态' % serial, category='warning')
            add_feed(user=user, event=u'归还iPad：%s' % ipad.alias2, category=u'rental')
            add_feed(user=current_user._get_current_object(), event=u'将iPad“%s”从%s回收，并设为维护状态' % (ipad.alias2, user.name_alias), category=u'manage')
            return redirect(url_for('manage.rental_exchange_step_2', rental_id=rental_id, next=request.args.get('next')))
        if not form.battery.data:
            rental.set_returned(return_agent_id=current_user.id, ipad_state=u'充电')
            flash(u'已回收序列号为%s的iPad，并设为充电状态' % serial, category='warning')
            add_feed(user=user, event=u'归还iPad：%s' % ipad.alias2, category=u'rental')
            add_feed(user=current_user._get_current_object(), event=u'将iPad“%s”从%s回收，并设为充电状态' % (ipad.alias2, user.name_alias), category=u'manage')
            return redirect(url_for('manage.rental_exchange_step_2', rental_id=rental_id, next=request.args.get('next')))
        rental.set_returned(return_agent_id=current_user.id)
        flash(u'已回收序列号为%s的iPad' % serial, category='success')
        add_feed(user=user, event=u'归还iPad：%s' % ipad.alias2, category=u'rental')
        add_feed(user=current_user._get_current_object(), event=u'将iPad“%s”从%s回收' % (ipad.alias2, user.name_alias), category=u'manage')
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
    if not user.created or user.deleted:
        abort(404)
    form = PunchSectionForm(user=user)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_exchange_step_3', rental_id=rental_id, section_id=int(form.section.data), next=request.args.get('next')))
    return render_template('manage/rental_exchange_step_2.html', rental=rental, form=form)


@manage.route('/rental/exchange/step-3/<int:rental_id>/<int:section_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_exchange_step_3(rental_id, section_id):
    rental = Rental.query.get_or_404(rental_id)
    if not rental.returned:
        flash(u'iPad尚未归还', category='error')
        return redirect(url_for('manage.rental_exchange_step_1', rental_id=rental_id, next=request.args.get('next')))
    user = User.query.get_or_404(rental.user_id)
    if not user.created or user.deleted:
        abort(404)
    section = Section.query.get_or_404(section_id)
    form = ConfirmPunchForm()
    if form.validate_on_submit():
        user.punch(section=section)
        flash(u'已保存%s的进度信息为：%s' % (user.name, section.alias2), category='success')
        add_feed(user=user, event=u'研修进度打卡：%s' % section.alias2, category=u'punch')
        add_feed(user=current_user._get_current_object(), event=u'保存%s的进度信息为：%s' % (user.name_alias, section.alias2), category=u'manage')
        return redirect(url_for('manage.rental_exchange_step_4', rental_id=rental_id, next=request.args.get('next')))
    return render_template('manage/rental_exchange_step_3.html', rental=rental, section=section, form=form)


@manage.route('/rental/exchange/step-4/<int:rental_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_exchange_step_4(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    if not rental.returned:
        flash(u'iPad尚未归还', category='error')
        return redirect(url_for('manage.rental_exchange_step_1', rental_id=rental_id, next=request.args.get('next')))
    user = User.query.get_or_404(rental.user_id)
    if not user.created or user.deleted:
        abort(404)
    form = RentiPadForm(user=user)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_exchange_step_5', rental_id=rental_id, ipad_id=int(form.ipad.data), next=request.args.get('next')))
    return render_template('manage/rental_exchange_step_4.html', rental=rental, form=form)


@manage.route('/rental/exchange/step-5/<int:rental_id>/<int:ipad_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_exchange_step_5(rental_id, ipad_id):
    rental = Rental.query.get_or_404(rental_id)
    if not rental.returned:
        flash(u'iPad尚未归还', category='error')
        return redirect(url_for('manage.rental_exchange_step_1', rental_id=rental_id, next=request.args.get('next')))
    user = User.query.get_or_404(rental.user_id)
    if not user.created or user.deleted:
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
            return redirect(url_for('manage.rental_exchange_step_5', rental_id=rental_id, ipad_id=ipad_id, next=request.args.get('next')))
        if ipad.state.name not in [u'待机', u'候补']:
            flash(u'序列号为%s的iPad处于“%s”状态，不能借出' % (ipad.serial, ipad.state.name), category='error')
            return redirect(url_for('manage.rental_exchange_step_5', rental_id=rental_id, ipad_id=ipad_id, next=request.args.get('next')))
        if user.has_unreturned_ipads:
            flash(u'%s有未归换的iPad' % user.name, category='error')
            return redirect(url_for('manage.rental_exchange_step_5', rental_id=rental_id, ipad_id=ipad_id, next=request.args.get('next')))
        new_rental = Rental(user_id=user.id, ipad_id=ipad.id, schedule_id=schedule.id, walk_in=rental.walk_in, rent_agent_id=current_user.id)
        db.session.add(new_rental)
        ipad.set_state(u'借出', battery_life=form.battery_life.data, modified_by=current_user._get_current_object())
        flash(u'iPad借出信息登记成功', category='success')
        add_feed(user=user, event=u'借出iPad：%s' % ipad.alias2, category=u'rental')
        add_feed(user=current_user._get_current_object(), event=u'将iPad“%s”借给%s' % (ipad.alias2, user.name_alias), category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.rental'))
    return render_template('manage/rental_exchange_step_5.html', rental=rental, ipad=ipad, form=form)


@manage.route('/rental/exchange/step-4-lesson/<int:rental_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_exchange_step_4_lesson(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    if not rental.returned:
        flash(u'iPad尚未归还', category='error')
        return redirect(url_for('manage.rental_exchange_step_1', rental_id=rental_id, next=request.args.get('next')))
    user = User.query.get_or_404(rental.user_id)
    if not user.created or user.deleted:
        abort(404)
    form = SelectLessonForm()
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_exchange_step_5_lesson', rental_id=rental_id, lesson_id=int(form.lesson.data), next=request.args.get('next')))
    return render_template('manage/rental_exchange_step_4_lesson.html', rental=rental, form=form)


@manage.route('rental/exchange/step-5-lesson/<int:rental_id>/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_exchange_step_5_lesson(rental_id, lesson_id):
    rental = Rental.query.get_or_404(rental_id)
    if not rental.returned:
        flash(u'iPad尚未归还', category='error')
        return redirect(url_for('manage.rental_exchange_step_1', rental_id=rental_id, next=request.args.get('next')))
    user = User.query.get_or_404(rental.user_id)
    if not user.created or user.deleted:
        abort(404)
    lesson = Lesson.query.get_or_404(lesson_id)
    form = RentiPadByLessonForm(lesson=lesson)
    if form.validate_on_submit():
        return redirect(url_for('manage.rental_exchange_step_6_lesson', rental_id=rental_id, lesson_id=lesson_id, ipad_id=int(form.ipad.data), next=request.args.get('next')))
    return render_template('manage/rental_exchange_step_5_lesson.html', rental=rental, lesson=lesson, form=form)


@manage.route('rental/exchange/step-6-lesson/<int:rental_id>/<int:lesson_id>/<int:ipad_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理iPad借阅')
def rental_exchange_step_6_lesson(rental_id, lesson_id, ipad_id):
    rental = Rental.query.get_or_404(rental_id)
    if not rental.returned:
        flash(u'iPad尚未归还', category='error')
        return redirect(url_for('manage.rental_exchange_step_1', rental_id=rental_id, next=request.args.get('next')))
    user = User.query.get_or_404(rental.user_id)
    if not user.created or user.deleted:
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
            return redirect(url_for('manage.rental_exchange_step_6_lesson', rental_id=rental_id, lesson_id=lesson_id, ipad_id=ipad_id, next=request.args.get('next')))
        if ipad.state.name not in [u'待机', u'候补']:
            flash(u'序列号为%s的iPad处于“%s”状态，不能借出' % (ipad.serial, ipad.state.name), category='error')
            return redirect(url_for('manage.rental_exchange_step_6_lesson', rental_id=rental_id, lesson_id=lesson_id, ipad_id=ipad_id, next=request.args.get('next')))
        if user.has_unreturned_ipads:
            flash(u'%s有未归换的iPad' % user.name, category='error')
            return redirect(url_for('manage.rental_exchange_step_6_lesson', rental_id=rental_id, lesson_id=lesson_id, ipad_id=ipad_id, next=request.args.get('next')))
        new_rental = Rental(user_id=user.id, ipad_id=ipad.id, schedule_id=schedule.id, walk_in=rental.walk_in, rent_agent_id=current_user.id)
        db.session.add(new_rental)
        ipad.set_state(u'借出', battery_life=form.battery_life.data, modified_by=current_user._get_current_object())
        flash(u'iPad借出信息登记成功', category='success')
        add_feed(user=user, event=u'借出iPad：%s' % ipad.alias2, category=u'rental')
        add_feed(user=current_user._get_current_object(), event=u'将iPad“%s”借给%s' % (ipad.alias2, user.name_alias), category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.rental'))
    return render_template('manage/rental_exchange_step_6_lesson.html', rental=rental, lesson=lesson, ipad=ipad, form=form)


@manage.route('/punch/edit/step-1/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理研修进度')
def edit_punch_step_1(user_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    form = EditPunchLessonForm(user=user)
    if form.validate_on_submit():
        return redirect(url_for('manage.edit_punch_step_2', user_id=user_id, lesson_id=int(form.lesson.data), next=request.args.get('next')))
    form.lesson.data = unicode(user.last_punch.section.lesson_id)
    return render_template('manage/edit_punch_step_1.html', user=user, form=form)


@manage.route('/punch/edit/step-2/<int:user_id>/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理研修进度')
def edit_punch_step_2(user_id, lesson_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    lesson = Lesson.query.get_or_404(lesson_id)
    form = EditPunchSectionForm(lesson=lesson)
    if form.validate_on_submit():
        return redirect(url_for('manage.edit_punch_step_3', user_id=user_id, section_id=int(form.section.data), next=request.args.get('next')))
    return render_template('manage/edit_punch_step_2.html', user=user, lesson=lesson, form=form)


@manage.route('/punch/edit/step-3/<int:user_id>/<int:section_id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理研修进度')
def edit_punch_step_3(user_id, section_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    section = Section.query.get_or_404(section_id)
    form = ConfirmPunchForm()
    if form.validate_on_submit():
        user.punch(section=section)
        flash(u'已保存%s的进度信息为：%s' % (user.name_alias, section.alias2), category='success')
        add_feed(user=user, event=u'研修进度打卡：%s' % section.alias2, category=u'punch')
        add_feed(user=current_user._get_current_object(), event=u'保存%s的进度信息为：%s' % (user.name_alias, section.alias2), category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.user'))
    return render_template('manage/edit_punch_step_3.html', user=user, section=section, form=form)


@manage.route('/punch/<int:user_id>/<int:section_id>')
@login_required
@permission_required(u'管理研修进度')
def punch(user_id, section_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    section = Section.query.get_or_404(section_id)
    user.punch(section=section)
    flash(u'已为%s标记进度：%s' % (user.name_alias, section.alias2), category='success')
    add_feed(user=user, event=u'研修进度打卡：%s' % section.alias2, category=u'punch')
    add_feed(user=current_user._get_current_object(), event=u'为%s标记进度：%s' % (user.name_alias, section.alias2), category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.user'))


@manage.route('/unpunch/<int:user_id>/<int:section_id>')
@login_required
@permission_required(u'管理研修进度')
def unpunch(user_id, section_id):
    user = User.query.get_or_404(user_id)
    if not user.created or user.deleted:
        abort(404)
    section = Section.query.get_or_404(section_id)
    user.unpunch(section=section)
    flash(u'已取消标记%s的进度：%s' % (user.name_alias, section.alias2), category='success')
    add_feed(user=current_user._get_current_object(), event=u'取消标记%s的进度：%s' % (user.name_alias, section.alias2), category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.user'))


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
            return redirect(url_for('manage.period', page=request.args.get('page', 1, type=int)))
        period = Period(
            name=form.name.data,
            start_time=start_time,
            end_time=end_time,
            type_id=int(form.period_type.data),
            show=form.show.data,
            modified_by_id=current_user.id
        )
        db.session.add(period)
        flash(u'已添加时段模板：%s' % form.name.data, category='success')
        add_feed(user=current_user._get_current_object(), event=u'添加时段模板：%s' % form.name.data, category=u'manage')
        return redirect(url_for('manage.period', page=request.args.get('page', 1, type=int)))
    show_vb_periods = True
    show_y_gre_periods = False
    if current_user.is_authenticated:
        show_vb_periods = bool(request.cookies.get('show_vb_periods', '1'))
        show_y_gre_periods = bool(request.cookies.get('show_y_gre_periods', ''))
    if show_vb_periods:
        query = Period.query\
            .join(CourseType, CourseType.id == Period.type_id)\
            .filter(CourseType.name == u'VB')\
            .filter(Period.deleted == False)
    if show_y_gre_periods:
        query = Period.query\
            .join(CourseType, CourseType.id == Period.type_id)\
            .filter(CourseType.name == u'Y-GRE')\
            .filter(Period.deleted == False)
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    periods = pagination.items
    return render_template('manage/period.html',
        form=form,
        show_vb_periods=show_vb_periods,
        show_y_gre_periods=show_y_gre_periods,
        pagination=pagination,
        periods=periods
    )


@manage.route('/period/vb')
@login_required
@permission_required(u'管理预约时段')
def vb_periods():
    resp = make_response(redirect(url_for('manage.period')))
    resp.set_cookie('show_vb_periods', '1', max_age=30*24*60*60)
    resp.set_cookie('show_y_gre_periods', '', max_age=30*24*60*60)
    return resp


@manage.route('/period/y-gre')
@login_required
@permission_required(u'管理预约时段')
def y_gre_periods():
    resp = make_response(redirect(url_for('manage.period')))
    resp.set_cookie('show_vb_periods', '', max_age=30*24*60*60)
    resp.set_cookie('show_y_gre_periods', '1', max_age=30*24*60*60)
    return resp


@manage.route('/period/toggle-show/<int:id>')
@login_required
@permission_required(u'管理预约时段')
def toggle_period_show(id):
    period = Period.query.get_or_404(id)
    if period.deleted:
        abort(404)
    period.toggle_show(modified_by=current_user._get_current_object())
    if period.show:
        flash(u'“%s”的可选状态改为：可选' % period.alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'更改预约时段“%s”的可选状态改为：可选' % period.alias, category=u'manage')
    else:
        flash(u'“%s”的可选状态改为：不可选' % period.alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'更改预约时段“%s”的可选状态改为：不可选' % period.alias, category=u'manage')
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
        add_feed(user=current_user._get_current_object(), event=u'更新时段模板：%s' % form.name.data, category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.period'))
    form.name.data = period.name
    form.start_time.data = period.start_time.strftime('%H:%M')
    form.end_time.data = period.end_time.strftime('%H:%M')
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
    period.safe_delete(modified_by=current_user._get_current_object())
    flash(u'已删除时段模板：%s' % period.name, category='success')
    add_feed(user=current_user._get_current_object(), event=u'删除时段模板：%s' % period.name, category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.period'))


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
                flash(u'该时段已存在：%s，%s' % (schedule.date, schedule.period.alias), category='warning')
            else:
                period = Period.query.get_or_404(int(period_id))
                if period.deleted:
                    abort(404)
                if datetime(day.year, day.month, day.day, period.end_time.hour, period.end_time.minute) - timedelta(hours=current_app.config['UTC_OFFSET']) < datetime.utcnow():
                    flash(u'该时段已过期：%s，%s' % (day, period.alias), category='error')
                else:
                    schedule = Schedule(date=day, period_id=int(period_id), quota=form.quota.data, available=form.publish_now.data, modified_by_id=current_user.id)
                    db.session.add(schedule)
                    db.session.commit()
                    flash(u'添加时段：%s，%s' % (schedule.date, schedule.period.alias), category='success')
                    add_feed(user=current_user._get_current_object(), event=u'添加时段：%s，%s' % (schedule.date, schedule.period.alias), category=u'manage')
        return redirect(url_for('manage.schedule', page=request.args.get('page', 1, type=int)))
    show_today_schedules = True
    show_future_schedules = False
    show_history_schedules = False
    if current_user.is_authenticated:
        show_today_schedules = bool(request.cookies.get('show_today_schedules', '1'))
        show_future_schedules = bool(request.cookies.get('show_future_schedules', ''))
        show_history_schedules = bool(request.cookies.get('show_history_schedules', ''))
    if show_today_schedules:
        query = Schedule.query\
            .filter(Schedule.date == date.today())\
            .order_by(Schedule.period_id.asc())
    if show_future_schedules:
        query = Schedule.query\
            .filter(Schedule.date > date.today())\
            .order_by(Schedule.date.asc())\
            .order_by(Schedule.period_id.asc())
    if show_history_schedules:
        query = Schedule.query\
            .filter(Schedule.date < date.today())\
            .order_by(Schedule.date.desc())\
            .order_by(Schedule.period_id.asc())
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    schedules = pagination.items
    return render_template('manage/schedule.html',
        form=form,
        show_today_schedules=show_today_schedules,
        show_future_schedules=show_future_schedules,
        show_history_schedules=show_history_schedules,
        pagination=pagination,
        schedules=schedules
    )


@manage.route('/schedule/today')
@login_required
@permission_required(u'管理预约时段')
def today_schedules():
    resp = make_response(redirect(url_for('manage.schedule')))
    resp.set_cookie('show_today_schedules', '1', max_age=30*24*60*60)
    resp.set_cookie('show_future_schedules', '', max_age=30*24*60*60)
    resp.set_cookie('show_history_schedules', '', max_age=30*24*60*60)
    return resp


@manage.route('/schedule/future')
@login_required
@permission_required(u'管理预约时段')
def future_schedules():
    resp = make_response(redirect(url_for('manage.schedule')))
    resp.set_cookie('show_today_schedules', '', max_age=30*24*60*60)
    resp.set_cookie('show_future_schedules', '1', max_age=30*24*60*60)
    resp.set_cookie('show_history_schedules', '', max_age=30*24*60*60)
    return resp


@manage.route('/schedule/history')
@login_required
@permission_required(u'管理预约时段')
def history_schedules():
    resp = make_response(redirect(url_for('manage.schedule')))
    resp.set_cookie('show_today_schedules', '', max_age=30*24*60*60)
    resp.set_cookie('show_future_schedules', '', max_age=30*24*60*60)
    resp.set_cookie('show_history_schedules', '1', max_age=30*24*60*60)
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
    add_feed(user=current_user._get_current_object(), event=u'发布时段：%s，%s' % (schedule.date, schedule.period.alias), category=u'manage')
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
    add_feed(user=current_user._get_current_object(), event=u'撤销时段：%s，%s' % (schedule.date, schedule.period.alias), category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.schedule'))


@manage.route('/schedule/increase-quota/<int:id>')
@login_required
@permission_required(u'管理预约时段')
def increase_schedule_quota(id):
    schedule = Schedule.query.get_or_404(id)
    if schedule.out_of_date:
        flash(u'所选时段已经过期', category='error')
        return redirect(request.args.get('next') or url_for('manage.schedule'))
    waited_booking = schedule.increase_quota(modified_by=current_user._get_current_object())
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
    flash(u'所选时段名额+1', category='success')
    add_feed(user=current_user._get_current_object(), event=u'给时段增加1个名额：%s，%s' % (schedule.date, schedule.period.alias), category=u'manage')
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
    add_feed(user=current_user._get_current_object(), event=u'给时段缩减1个名额：%s，%s' % (schedule.date, schedule.period.alias), category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.schedule'))


@manage.route('/lesson')
@login_required
@permission_required(u'管理课程')
def lesson():
    show_vb_lessons = True
    show_y_gre_lessons = False
    if current_user.is_authenticated:
        show_vb_lessons = bool(request.cookies.get('show_vb_lessons', '1'))
        show_y_gre_lessons = bool(request.cookies.get('show_y_gre_lessons', ''))
    if show_vb_lessons:
        query = Lesson.query\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(CourseType.name == u'VB')\
            .order_by(Lesson.id.asc())
    if show_y_gre_lessons:
        query = Lesson.query\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(CourseType.name == u'Y-GRE')\
            .order_by(Lesson.id.asc())
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    lessons = pagination.items
    return render_template('manage/lesson.html',
        show_vb_lessons=show_vb_lessons,
        show_y_gre_lessons=show_y_gre_lessons,
        pagination=pagination,
        lessons=lessons
    )


@manage.route('/lesson/vb')
@login_required
@permission_required(u'管理课程')
def vb_lessons():
    resp = make_response(redirect(url_for('manage.lesson')))
    resp.set_cookie('show_vb_lessons', '1', max_age=30*24*60*60)
    resp.set_cookie('show_y_gre_lessons', '', max_age=30*24*60*60)
    return resp


@manage.route('/lesson/y-gre')
@login_required
@permission_required(u'管理课程')
def y_gre_lessons():
    resp = make_response(redirect(url_for('manage.lesson')))
    resp.set_cookie('show_vb_lessons', '', max_age=30*24*60*60)
    resp.set_cookie('show_y_gre_lessons', '1', max_age=30*24*60*60)
    return resp


@manage.route('/assignment', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理作业')
def assignment():
    form = NewAssignmentScoreForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower(), created=True, activated=True, deleted=False).first()
        if user is None:
            flash(u'用户邮箱不存在：%s' % form.email.data.lower(), category='error')
            return redirect(url_for('manage.assignment', page=request.args.get('page', 1, type=int)))
        score = AssignmentScore(
            user_id=user.id,
            assignment_id=int(form.assignment.data),
            grade_id=int(form.grade.data),
            modified_by_id=current_user.id
        )
        db.session.add(score)
        db.session.commit()
        flash(u'已添加作业记录：%s' % score.alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'添加作业记录：%s' % score.alias, category=u'manage')
        return redirect(url_for('manage.assignment_score', id=int(form.assignment.data)))
    show_vb_assignments = True
    show_y_gre_assignments = False
    if current_user.is_authenticated:
        show_vb_assignments = bool(request.cookies.get('show_vb_assignments', '1'))
        show_y_gre_assignments = bool(request.cookies.get('show_y_gre_assignments', ''))
    if show_vb_assignments:
        query = Assignment.query\
            .join(Lesson, Lesson.id == Assignment.lesson_id)\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(CourseType.name == u'VB')\
            .order_by(Assignment.id.asc())
    if show_y_gre_assignments:
        query = Assignment.query\
            .join(Lesson, Lesson.id == Assignment.lesson_id)\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(CourseType.name == u'Y-GRE')\
            .order_by(Assignment.id.asc())
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    assignments = pagination.items
    return render_template('manage/assignment.html',
        form=form,
        show_vb_assignments=show_vb_assignments,
        show_y_gre_assignments=show_y_gre_assignments,
        pagination=pagination,
        assignments=assignments
    )


@manage.route('/assignment/vb')
@login_required
@permission_required(u'管理作业')
def vb_assignments():
    resp = make_response(redirect(url_for('manage.assignment')))
    resp.set_cookie('show_vb_assignments', '1', max_age=30*24*60*60)
    resp.set_cookie('show_y_gre_assignments', '', max_age=30*24*60*60)
    return resp


@manage.route('/assignment/y-gre')
@login_required
@permission_required(u'管理作业')
def y_gre_assignments():
    resp = make_response(redirect(url_for('manage.assignment')))
    resp.set_cookie('show_vb_assignments', '', max_age=30*24*60*60)
    resp.set_cookie('show_y_gre_assignments', '1', max_age=30*24*60*60)
    return resp


@manage.route('/assignment/score/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理作业')
def assignment_score(id):
    assignment = Assignment.query.get_or_404(id)
    if assignment.finished_by_alias.count() == 0:
        return redirect(url_for('manage.assignment'))
    form = NewAssignmentScoreForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower(), created=True, activated=True, deleted=False).first()
        if user is None:
            flash(u'用户邮箱不存在：%s' % form.email.data.lower(), category='error')
            return redirect(url_for('manage.assignment_score', id=assignment.id))
        score = AssignmentScore(
            user_id=user.id,
            assignment_id=int(form.assignment.data),
            grade_id=int(form.grade.data),
            modified_by_id=current_user.id
        )
        db.session.add(score)
        db.session.commit()
        flash(u'已添加作业记录：%s' % score.alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'添加作业记录：%s' % score.alias, category=u'manage')
        return redirect(url_for('manage.assignment_score', id=int(form.assignment.data)))
    form.assignment.data = unicode(assignment.id)
    query = AssignmentScore.query\
        .join(User, User.id == AssignmentScore.user_id)\
        .filter(AssignmentScore.assignment_id == assignment.id)\
        .filter(User.created == True)\
        .filter(User.activated == True)\
        .filter(User.deleted == False)\
        .order_by(AssignmentScore.modified_at.desc())
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    scores = pagination.items
    return render_template('manage/assignment_score.html',
        form=form,
        assignment=assignment,
        pagination=pagination,
        scores=scores
    )


@manage.route('/assignment/score/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理作业')
def edit_assignment_score(id):
    score = AssignmentScore.query.get_or_404(id)
    form = EditAssignmentScoreForm()
    if form.validate_on_submit():
        score.assignment_id = int(form.assignment.data)
        score.grade_id = int(form.grade.data)
        score.modified_at = datetime.utcnow()
        score.modified_by_id = current_user.id
        db.session.add(score)
        db.session.commit()
        flash(u'已更新作业记录：%s' % score.alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'更新作业记录：%s' % score.alias, category=u'manage')
        return redirect(url_for('manage.assignment_score', id=int(form.assignment.data)))
    form.assignment.data = unicode(score.assignment_id)
    form.grade.data = unicode(score.grade_id)
    return render_template('manage/edit_assignment_score.html', form=form, score=score)


@manage.route('/assignment/score/delete/<int:id>')
@login_required
@permission_required(u'管理作业')
def delete_assignment_score(id):
    score = AssignmentScore.query.get_or_404(id)
    db.session.delete(score)
    flash(u'已删除作业记录：%s' % score.alias, category='success')
    add_feed(user=current_user._get_current_object(), event=u'删除作业记录：%s' % score.alias, category=u'manage')
    return redirect(url_for('manage.assignment_score', id=score.assignment_id))


@manage.route('/test', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理考试')
def test():
    vb_form = NewVBTestScoreForm(prefix='vb')
    if vb_form.submit.data and vb_form.validate_on_submit():
        user = User.query.filter_by(email=vb_form.email.data.lower(), created=True, activated=True, deleted=False).first()
        if user is None:
            flash(u'用户邮箱不存在：%s' % vb_form.email.data.lower(), category='error')
            return redirect(url_for('manage.test', page=request.args.get('page', 1, type=int)))
        score = VBTestScore(
            user_id=user.id,
            test_id=int(vb_form.test.data),
            score=float(vb_form.score.data),
            retrieved=vb_form.retrieved.data,
            modified_by_id=current_user.id
        )
        db.session.add(score)
        db.session.commit()
        flash(u'已添加VB考试记录：%s' % score.alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'添加VB考试记录：%s' % score.alias, category=u'manage')
        return redirect(url_for('manage.test_score', test_type=u'vb', id=int(vb_form.test.data)))
    y_gre_form = NewYGRETestScoreForm(prefix='y_gre')
    if y_gre_form.submit.data and y_gre_form.validate_on_submit():
        user = User.query.filter_by(email=y_gre_form.email.data.lower(), created=True, activated=True, deleted=False).first()
        if user is None:
            flash(u'用户邮箱不存在：%s' % y_gre_form.email.data.lower(), category='error')
            return redirect(url_for('manage.test', page=request.args.get('page', 1, type=int)))
        q_score = None
        if y_gre_form.q_score.data:
            q_score = int(y_gre_form.q_score.data)
        aw_score = None
        if y_gre_form.aw_score.data:
            aw_score = int(y_gre_form.aw_score.data)
        score = YGRETestScore(
            user_id=user.id,
            test_id=int(y_gre_form.test.data),
            v_score=y_gre_form.v_score.data,
            q_score=q_score,
            aw_score_id=aw_score,
            retrieved=y_gre_form.retrieved.data,
            modified_by_id=current_user.id
        )
        db.session.add(score)
        db.session.commit()
        flash(u'已添加Y-GRE考试记录：%s' % score.alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'添加Y-GRE考试记录：%s' % score.alias, category=u'manage')
        return redirect(url_for('manage.test_score', test_type=u'y_gre', id=int(y_gre_form.test.data)))
    gre_form = NewGRETestScoreForm(prefix='gre')
    if gre_form.submit.data and gre_form.validate_on_submit():
        user = User.query.filter_by(email=gre_form.email.data.lower(), created=True, activated=True, deleted=False).first()
        if user is None:
            flash(u'用户邮箱不存在：%s' % gre_form.email.data.lower(), category='error')
            return redirect(url_for('manage.test', page=request.args.get('page', 1, type=int)))
        label_id = None
        if int(gre_form.score_label.data) > 0:
            label_id = int(gre_form.score_label.data)
            if user.gre_test_scores.filter_by(label_id=label_id).first() is not None:
                flash(u'%s已经拥有“%s”成绩' % (user.name_alias, ScoreLabel.query.get(label_id).name), category='error')
                return redirect(url_for('manage.test', page=request.args.get('page', 1, type=int)))
        test = GRETest.query.filter_by(date=gre_form.test_date.data).first()
        if test is None:
            test = GRETest(date=gre_form.test_date.data)
            db.session.add(test)
            db.session.commit()
        aw_score_id = None
        if gre_form.aw_score.data:
            aw_score_id = int(gre_form.aw_score.data)
        score = GRETestScore(
            user_id=user.id,
            test_id=test.id,
            label_id=label_id,
            v_score=gre_form.v_score.data,
            q_score=gre_form.q_score.data,
            aw_score_id=aw_score_id,
            modified_by_id=current_user.id
        )
        db.session.add(score)
        db.session.commit()
        flash(u'已添加GRE考试记录：%s' % score.alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'添加GRE考试记录：%s' % score.alias, category=u'manage')
        return redirect(url_for('manage.test_score', test_type=u'gre', id=test.id))
    toefl_form = NewTOEFLTestScoreForm(prefix='toefl')
    if toefl_form.submit.data and toefl_form.validate_on_submit():
        user = User.query.filter_by(email=toefl_form.email.data.lower(), created=True, activated=True, deleted=False).first()
        if user is None:
            flash(u'用户邮箱不存在：%s' % toefl_form.email.data.lower(), category='error')
            return redirect(url_for('manage.test', page=request.args.get('page', 1, type=int)))
        label_id = None
        if int(toefl_form.score_label.data) > 0:
            label_id = int(toefl_form.score_label.data)
            if user.toefl_test_scores.filter_by(label_id=label_id).first() is not None:
                flash(u'%s已经拥有“%s”成绩' % (user.name_alias, ScoreLabel.query.get(label_id).name), category='error')
                return redirect(url_for('manage.test', page=request.args.get('page', 1, type=int)))
        test = TOEFLTest.query.filter_by(date=toefl_form.test_date.data).first()
        if test is None:
            test = TOEFLTest(date=toefl_form.test_date.data)
            db.session.add(test)
            db.session.commit()
        score = TOEFLTestScore(
            user_id=user.id,
            test_id=test.id,
            label_id=label_id,
            total_score=toefl_form.total.data,
            reading_score=toefl_form.reading.data,
            listening_score=toefl_form.listening.data,
            speaking_score=toefl_form.speaking.data,
            writing_score=toefl_form.writing.data,
            modified_by_id=current_user.id
        )
        db.session.add(score)
        db.session.commit()
        flash(u'已添加TOEFL考试记录：%s' % score.alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'添加TOEFL考试记录：%s' % score.alias, category=u'manage')
        return redirect(url_for('manage.test_score', test_type=u'toefl', id=test.id))
    show_vb_tests = True
    show_y_gre_tests = False
    show_gre_tests = False
    show_toefl_tests = False
    if current_user.is_authenticated:
        show_vb_tests = bool(request.cookies.get('show_vb_tests', '1'))
        show_y_gre_tests = bool(request.cookies.get('show_y_gre_tests', ''))
        show_gre_tests = bool(request.cookies.get('show_gre_tests', ''))
        show_toefl_tests = bool(request.cookies.get('show_toefl_tests', ''))
    if show_vb_tests:
        test_type = u'vb'
        query = Test.query\
            .join(Lesson, Lesson.id == Test.lesson_id)\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(CourseType.name == u'VB')\
            .order_by(Test.id.asc())
    if show_y_gre_tests:
        test_type = u'y_gre'
        query = Test.query\
            .join(Lesson, Lesson.id == Test.lesson_id)\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(CourseType.name == u'Y-GRE')\
            .order_by(Test.id.asc())
    if show_gre_tests:
        test_type = u'gre'
        query = GRETest.query\
            .order_by(GRETest.date.desc())
    if show_toefl_tests:
        test_type = u'toefl'
        query = TOEFLTest.query\
            .order_by(TOEFLTest.date.desc())
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    tests = pagination.items
    return render_template('manage/test.html',
        vb_form=vb_form,
        y_gre_form=y_gre_form,
        gre_form=gre_form,
        toefl_form=toefl_form,
        show_vb_tests=show_vb_tests,
        show_y_gre_tests=show_y_gre_tests,
        show_gre_tests=show_gre_tests,
        show_toefl_tests=show_toefl_tests,
        test_type=test_type,
        pagination=pagination,
        tests=tests
    )


@manage.route('/test/vb')
@login_required
@permission_required(u'管理考试')
def vb_tests():
    resp = make_response(redirect(url_for('manage.test')))
    resp.set_cookie('show_vb_tests', '1', max_age=30*24*60*60)
    resp.set_cookie('show_y_gre_tests', '', max_age=30*24*60*60)
    resp.set_cookie('show_gre_tests', '', max_age=30*24*60*60)
    resp.set_cookie('show_toefl_tests', '', max_age=30*24*60*60)
    return resp


@manage.route('/test/y-gre')
@login_required
@permission_required(u'管理考试')
def y_gre_tests():
    resp = make_response(redirect(url_for('manage.test')))
    resp.set_cookie('show_vb_tests', '', max_age=30*24*60*60)
    resp.set_cookie('show_y_gre_tests', '1', max_age=30*24*60*60)
    resp.set_cookie('show_gre_tests', '', max_age=30*24*60*60)
    resp.set_cookie('show_toefl_tests', '', max_age=30*24*60*60)
    return resp


@manage.route('/test/gre')
@login_required
@permission_required(u'管理考试')
def gre_tests():
    resp = make_response(redirect(url_for('manage.test')))
    resp.set_cookie('show_vb_tests', '', max_age=30*24*60*60)
    resp.set_cookie('show_y_gre_tests', '', max_age=30*24*60*60)
    resp.set_cookie('show_gre_tests', '1', max_age=30*24*60*60)
    resp.set_cookie('show_toefl_tests', '', max_age=30*24*60*60)
    return resp


@manage.route('/test/toefl')
@login_required
@permission_required(u'管理考试')
def toefl_tests():
    resp = make_response(redirect(url_for('manage.test')))
    resp.set_cookie('show_vb_tests', '', max_age=30*24*60*60)
    resp.set_cookie('show_y_gre_tests', '', max_age=30*24*60*60)
    resp.set_cookie('show_gre_tests', '', max_age=30*24*60*60)
    resp.set_cookie('show_toefl_tests', '1', max_age=30*24*60*60)
    return resp


@manage.route('/test/score/<test_type>/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理考试')
def test_score(test_type, id):
    if test_type == u'vb':
        test = Test.query.get_or_404(id)
        if test.finished_by_alias.count() == 0:
            return redirect(url_for('manage.test'))
        form = NewVBTestScoreForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.lower(), created=True, activated=True, deleted=False).first()
            if user is None:
                flash(u'用户邮箱不存在：%s' % form.email.data.lower(), category='error')
                return redirect(url_for('manage.test_score', test_type=test_type, id=test.id))
            score = VBTestScore(
                user_id=user.id,
                test_id=int(form.test.data),
                score=float(form.score.data),
                retrieved=form.retrieved.data,
                modified_by_id=current_user.id
            )
            db.session.add(score)
            db.session.commit()
            flash(u'已添加VB考试记录：%s' % score.alias, category='success')
            add_feed(user=current_user._get_current_object(), event=u'添加VB考试记录：%s' % score.alias, category=u'manage')
            return redirect(url_for('manage.test_score', test_type=test_type, id=int(form.test.data)))
        form.test.data = unicode(test.id)
        query = VBTestScore.query\
            .join(User, User.id == VBTestScore.user_id)\
            .filter(VBTestScore.test_id == test.id)\
            .filter(User.created == True)\
            .filter(User.activated == True)\
            .filter(User.deleted == False)\
            .order_by(VBTestScore.modified_at.desc())
    if test_type == u'y_gre':
        test = Test.query.get_or_404(id)
        if test.finished_by_alias.count() == 0:
            return redirect(url_for('manage.test'))
        form = NewYGRETestScoreForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.lower(), created=True, activated=True, deleted=False).first()
            if user is None:
                flash(u'用户邮箱不存在：%s' % form.email.data.lower(), category='error')
                return redirect(url_for('manage.test_score', test_type=test_type, id=test.id))
            q_score = None
            if form.q_score.data:
                q_score = int(form.q_score.data)
            aw_score = None
            if form.aw_score.data:
                aw_score = int(form.aw_score.data)
            score = YGRETestScore(
                user_id=user.id,
                test_id=int(form.test.data),
                v_score=form.v_score.data,
                q_score=q_score,
                aw_score_id=aw_score,
                retrieved=form.retrieved.data,
                modified_by_id=current_user.id
            )
            db.session.add(score)
            db.session.commit()
            flash(u'已添加Y-GRE考试记录：%s' % score.alias, category='success')
            add_feed(user=current_user._get_current_object(), event=u'添加Y-GRE考试记录：%s' % score.alias, category=u'manage')
            return redirect(url_for('manage.test_score', test_type=test_type, id=int(form.test.data)))
        form.test.data = unicode(test.id)
        query = YGRETestScore.query\
            .join(User, User.id == YGRETestScore.user_id)\
            .filter(YGRETestScore.test_id == test.id)\
            .filter(User.created == True)\
            .filter(User.activated == True)\
            .filter(User.deleted == False)\
            .order_by(YGRETestScore.modified_at.desc())
    if test_type == u'gre':
        test = GRETest.query.get_or_404(id)
        if test.finished_by_alias.count() == 0:
            return redirect(url_for('manage.test'))
        form = NewGRETestScoreForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.lower(), created=True, activated=True, deleted=False).first()
            if user is None:
                flash(u'用户邮箱不存在：%s' % form.email.data.lower(), category='error')
                return redirect(url_for('manage.test_score', test_type=test_type, id=test.id))
            label_id = None
            if int(form.score_label.data) > 0:
                label_id = int(form.score_label.data)
                if user.gre_test_scores.filter_by(label_id=label_id).first() is not None:
                    flash(u'%s已经拥有“%s”成绩' % (user.name_alias, ScoreLabel.query.get(label_id).name), category='error')
                    return redirect(url_for('manage.test_score', test_type=test_type, id=test.id))
            test = GRETest.query.filter_by(date=form.test_date.data).first()
            if test is None:
                test = GRETest(date=form.test_date.data)
                db.session.add(test)
                db.session.commit()
            aw_score_id = None
            if form.aw_score.data:
                aw_score_id = int(form.aw_score.data)
            score = GRETestScore(
                user_id=user.id,
                test_id=test.id,
                label_id=label_id,
                v_score=form.v_score.data,
                q_score=form.q_score.data,
                aw_score_id=aw_score_id,
                modified_by_id=current_user.id
            )
            db.session.add(score)
            db.session.commit()
            flash(u'已添加GRE考试记录：%s' % score.alias, category='success')
            add_feed(user=current_user._get_current_object(), event=u'添加GRE考试记录：%s' % score.alias, category=u'manage')
            return redirect(url_for('manage.test_score', test_type=test_type, id=test.id))
        form.test_date.data = test.date
        query = GRETestScore.query\
            .join(User, User.id == GRETestScore.user_id)\
            .filter(GRETestScore.test_id == test.id)\
            .filter(User.created == True)\
            .filter(User.activated == True)\
            .filter(User.deleted == False)\
            .order_by(GRETestScore.modified_at.desc())
    if test_type == u'toefl':
        test = TOEFLTest.query.get_or_404(id)
        if test.finished_by_alias.count() == 0:
            return redirect(url_for('manage.test'))
        form = NewTOEFLTestScoreForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.lower(), created=True, activated=True, deleted=False).first()
            if user is None:
                flash(u'用户邮箱不存在：%s' % form.email.data.lower(), category='error')
                return redirect(url_for('manage.test_score', test_type=test_type, id=test.id))
            label_id = None
            if int(form.score_label.data) > 0:
                label_id = int(form.score_label.data)
                if user.toefl_test_scores.filter_by(label_id=label_id).first() is not None:
                    flash(u'%s已经拥有“%s”成绩' % (user.name_alias, ScoreLabel.query.get(label_id).name), category='error')
                    return redirect(url_for('manage.test_score', test_type=test_type, id=test.id))
            test = TOEFLTest.query.filter_by(date=form.test_date.data).first()
            if test is None:
                test = TOEFLTest(date=form.test_date.data)
                db.session.add(test)
                db.session.commit()
            score = TOEFLTestScore(
                user_id=user.id,
                test_id=test.id,
                label_id=label_id,
                total_score=form.total.data,
                reading_score=form.reading.data,
                listening_score=form.listening.data,
                speaking_score=form.speaking.data,
                writing_score=form.writing.data,
                modified_by_id=current_user.id
            )
            db.session.add(score)
            db.session.commit()
            flash(u'已添加TOEFL考试记录：%s' % score.alias, category='success')
            add_feed(user=current_user._get_current_object(), event=u'添加TOEFL考试记录：%s' % score.alias, category=u'manage')
            return redirect(url_for('manage.test_score', test_type=test_type, id=test.id))
        form.test_date.data = test.date
        query = TOEFLTestScore.query\
            .join(User, User.id == TOEFLTestScore.user_id)\
            .filter(TOEFLTestScore.test_id == test.id)\
            .filter(User.created == True)\
            .filter(User.activated == True)\
            .filter(User.deleted == False)\
            .order_by(TOEFLTestScore.modified_at.desc())
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    scores = pagination.items
    return render_template('manage/test_score.html',
        test_type=test_type,
        form=form,
        test=test,
        pagination=pagination,
        scores=scores
    )


@manage.route('/test/paper/toggle-retrieve/<test_type>/<int:id>')
@login_required
@permission_required(u'管理考试')
def toggle_test_paper_retrieve(test_type, id):
    if test_type == u'vb':
        score = VBTestScore.query.get_or_404(id)
    if test_type == u'y_gre':
        score = YGRETestScore.query.get_or_404(id)
    score.toggle_retrieve(modified_by=current_user._get_current_object())
    if score.retrieved:
        flash(u'已回收试卷：%s' % score.alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'回收试卷：%s' % score.alias, category=u'manage')
    else:
        flash(u'已发放试卷：%s' % score.alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'发放试卷：%s' % score.alias, category=u'manage')
    return redirect(url_for('manage.test_score', test_type=test_type, id=score.test_id))


@manage.route('/test/score/edit/<test_type>/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理考试')
def edit_test_score(test_type, id):
    if test_type == u'vb':
        score = VBTestScore.query.get_or_404(id)
        form = EditVBTestScoreForm()
        if form.validate_on_submit():
            score.test_id = int(form.test.data)
            score.score = float(form.score.data)
            score.retrieved = form.retrieved.data
            score.modified_at = datetime.utcnow()
            score.modified_by_id = current_user.id
            db.session.add(score)
            db.session.commit()
            flash(u'已更新VB考试记录：%s' % score.alias, category='success')
            add_feed(user=current_user._get_current_object(), event=u'更新VB考试记录：%s' % score.alias, category=u'manage')
            return redirect(url_for('manage.test_score', test_type=test_type, id=int(form.test.data)))
        form.test.data = unicode(score.test_id)
        form.score.data = u'%g' % score.score
        form.retrieved.data = score.retrieved
    if test_type == u'y_gre':
        score = YGRETestScore.query.get_or_404(id)
        form = EditYGRETestScoreForm()
        if form.validate_on_submit():
            score.test_id = int(form.test.data)
            score.v_score = form.v_score.data
            if form.q_score.data:
                score.q_score = int(form.q_score.data)
            if form.aw_score.data:
                score.aw_score_id = int(form.aw_score.data)
            score.retrieved = form.retrieved.data
            score.modified_at = datetime.utcnow()
            score.modified_by_id = current_user.id
            db.session.add(score)
            db.session.commit()
            flash(u'已更新Y-GRE考试记录：%s' % score.alias, category='success')
            add_feed(user=current_user._get_current_object(), event=u'更新Y-GRE考试记录：%s' % score.alias, category=u'manage')
            return redirect(url_for('manage.test_score', test_type=test_type, id=int(form.test.data)))
        form.test.data = unicode(score.test_id)
        form.v_score.data = score.v_score
        form.q_score.data = u'%g' % score.q_score
        form.aw_score.data = unicode(score.aw_score_id)
        form.retrieved.data = score.retrieved
    if test_type == u'gre':
        score = GRETestScore.query.get_or_404(id)
        form = EditGRETestScoreForm()
        if form.validate_on_submit():
            label_id = None
            if int(form.score_label.data) > 0:
                label_id = int(form.score_label.data)
                if score.user.gre_test_scores.filter_by(label_id=label_id).first() is not None:
                    flash(u'%s已经拥有“%s”成绩' % (score.user.name_alias, ScoreLabel.query.get(label_id).name), category='error')
                    return redirect(url_for('manage.edit_test_score', test_type=test_type, id=score.id))
            test = GRETest.query.filter_by(date=form.test_date.data).first()
            if test is None:
                test = GRETest(date=form.test_date.data)
                db.session.add(test)
                db.session.commit()
            aw_score_id = None
            if form.aw_score.data:
                aw_score_id = int(form.aw_score.data)
            score.test_id = test.id
            score.label_id = label_id
            score.v_score = form.v_score.data
            score.q_score = form.q_score.data
            score.aw_score_id = aw_score_id
            score.modified_at = datetime.utcnow()
            score.modified_by_id = current_user.id
            db.session.add(score)
            db.session.commit()
            flash(u'已更新GRE考试记录：%s' % score.alias, category='success')
            add_feed(user=current_user._get_current_object(), event=u'更新GRE考试记录：%s' % score.alias, category=u'manage')
            return redirect(url_for('manage.test_score', test_type=test_type, id=test.id))
        form.test_date.data = score.test.date
        form.score_label.data = u'0'
        if score.label_id:
            form.score_label.data = unicode(score.label_id)
        form.v_score.data = score.v_score
        form.q_score.data = score.q_score
        if score.aw_score_id:
            form.aw_score.data = unicode(score.aw_score_id)
    if test_type == u'toefl':
        score = TOEFLTestScore.query.get_or_404(id)
        form = EditTOEFLTestScoreForm()
        if form.validate_on_submit():
            label_id = None
            if int(form.score_label.data) > 0:
                label_id = int(form.score_label.data)
                if score.user.toefl_test_scores.filter_by(label_id=label_id).first() is not None:
                    flash(u'%s已经拥有“%s”成绩' % (score.user.name_alias, ScoreLabel.query.get(label_id).name), category='error')
                    return redirect(url_for('manage.edit_test_score', test_type=test_type, id=score.id))
            test = TOEFLTest.query.filter_by(date=form.test_date.data).first()
            if test is None:
                test = TOEFLTest(date=form.test_date.data)
                db.session.add(test)
                db.session.commit()
            score.test_id = test.id
            score.label_id = label_id
            score.total_score = form.total.data
            score.reading_score = form.reading.data
            score.listening_score = form.listening.data
            score.speaking_score = form.speaking.data
            score.writing_score = form.writing.data
            score.modified_at = datetime.utcnow()
            score.modified_by_id = current_user.id
            db.session.add(score)
            db.session.commit()
            flash(u'已更新TOEFL考试记录：%s' % score.alias, category='success')
            add_feed(user=current_user._get_current_object(), event=u'更新TOEFL考试记录：%s' % score.alias, category=u'manage')
            return redirect(url_for('manage.test_score', test_type=test_type, id=test.id))
        form.test_date.data = score.test.date
        form.score_label.data = u'0'
        if score.label_id:
            form.score_label.data = unicode(score.label_id)
        form.total.data = score.total_score
        form.reading.data = score.reading_score
        form.listening.data = score.listening_score
        form.speaking.data = score.speaking_score
        form.writing.data = score.writing_score
    return render_template('manage/edit_test_score.html', test_type=test_type, form=form, score=score)


@manage.route('/test/score/delete/<test_type>/<int:id>')
@login_required
@permission_required(u'管理考试')
def delete_test_score(test_type, id):
    if test_type == u'vb':
        score = VBTestScore.query.get_or_404(id)
        db.session.delete(score)
        flash(u'已删除VB考试记录：%s' % score.alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'删除VB考试记录：%s' % score.alias, category=u'manage')
    if test_type == u'y_gre':
        score = YGRETestScore.query.get_or_404(id)
        db.session.delete(score)
        flash(u'已删除Y-GRE考试记录：%s' % score.alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'删除Y-GRE考试记录：%s' % score.alias, category=u'manage')
    if test_type == u'gre':
        score = GRETestScore.query.get_or_404(id)
        db.session.delete(score)
        flash(u'已删除GRE考试记录：%s' % score.alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'删除GRE考试记录：%s' % score.alias, category=u'manage')
    if test_type == u'toefl':
        score = TOEFLTestScore.query.get_or_404(id)
        db.session.delete(score)
        flash(u'已删除TOEFL考试记录：%s' % score.alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'删除TOEFL考试记录：%s' % score.alias, category=u'manage')
    return redirect(url_for('manage.test_score', test_type=test_type, id=score.test_id))


@manage.route('/user', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理')
def user():
    # create admin form
    form = NewAdminForm(creator=current_user._get_current_object())
    if form.submit.data and form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash(u'%s已经被注册' % form.email.data.lower(), category='error')
            return redirect(url_for('manage.user', page=request.args.get('page', 1, type=int)))
        admin = User(
            email=form.email.data.lower(),
            role_id=int(form.role.data),
            password=form.id_number.data.upper()[-6:],
            name=form.name.data,
            id_type_id=form.id_type.data,
            id_number=form.id_number.data.upper(),
            gender_id=int(form.gender.data),
            birthdate=form.birthdate.data
        )
        db.session.add(admin)
        db.session.commit()
        current_user.create_user(user=admin)
        flash(u'成功添加%s：%s' % (admin.role.name, admin.name), category='success')
        add_feed(user=current_user._get_current_object(), event=u'添加%s：%s' % (admin.role.name, admin.name), category=u'manage')
        return redirect(url_for('manage.user', page=request.args.get('page', 1, type=int)))
    # search user form
    search_form = SearchForm(prefix='search')
    if search_form.validate_on_submit():
        keyword = search_form.keyword.data
        return redirect(url_for('manage.search_user_results', keyword=keyword))
    # tabs
    show_activated_users = True
    show_unactivated_users = False
    show_suspended_users = False
    show_draft_users = False
    show_deleted_users = False
    show_volunteers = False
    show_moderators = False
    show_administrators = False
    show_developers = False
    show_search_users = False
    if current_user.is_authenticated:
        show_activated_users = bool(request.cookies.get('show_activated_users', '1'))
        show_unactivated_users = bool(request.cookies.get('show_unactivated_users', ''))
        show_suspended_users = bool(request.cookies.get('show_suspended_users', ''))
        show_draft_users = bool(request.cookies.get('show_draft_users', ''))
        show_deleted_users = bool(request.cookies.get('show_deleted_users', ''))
        show_volunteers = bool(request.cookies.get('show_volunteers', ''))
        show_moderators = bool(request.cookies.get('show_moderators', ''))
        show_administrators = bool(request.cookies.get('show_administrators', ''))
        show_developers = bool(request.cookies.get('show_developers', ''))
        show_search_users = bool(request.cookies.get('show_search_users', ''))
    if show_activated_users:
        query = User.query\
            .join(Role, Role.id == User.role_id)\
            .filter(User.created == True)\
            .filter(User.activated == True)\
            .filter(User.deleted == False)\
            .filter(or_(
                Role.name == u'单VB',
                Role.name == u'Y-GRE 普通',
                Role.name == u'Y-GRE VB×2',
                Role.name == u'Y-GRE A权限'
            ))\
            .order_by(User.last_seen_at.desc())
    activated_users_num = User.query\
        .join(Role, Role.id == User.role_id)\
        .filter(User.created == True)\
        .filter(User.activated == True)\
        .filter(User.deleted == False)\
        .filter(or_(
            Role.name == u'单VB',
            Role.name == u'Y-GRE 普通',
            Role.name == u'Y-GRE VB×2',
            Role.name == u'Y-GRE A权限'
        ))\
        .count()
    if show_unactivated_users:
        query = User.query\
            .join(Role, Role.id == User.role_id)\
            .filter(User.created == True)\
            .filter(User.activated == False)\
            .filter(User.deleted == False)\
            .filter(or_(
                Role.name == u'单VB',
                Role.name == u'Y-GRE 普通',
                Role.name == u'Y-GRE VB×2',
                Role.name == u'Y-GRE A权限'
            ))\
            .order_by(User.last_seen_at.desc())
    unactivated_users_num = User.query\
        .join(Role, Role.id == User.role_id)\
        .filter(User.created == True)\
        .filter(User.activated == False)\
        .filter(User.deleted == False)\
        .filter(or_(
            Role.name == u'单VB',
            Role.name == u'Y-GRE 普通',
            Role.name == u'Y-GRE VB×2',
            Role.name == u'Y-GRE A权限'
        ))\
        .count()
    if show_suspended_users:
        query = User.query\
            .join(Role, Role.id == User.role_id)\
            .filter(User.created == True)\
            .filter(User.deleted == False)\
            .filter(Role.name == u'挂起')\
            .order_by(User.last_seen_at.desc())
    suspended_users_num = User.query\
        .join(Role, Role.id == User.role_id)\
        .filter(User.created == True)\
        .filter(User.deleted == False)\
        .filter(Role.name == u'挂起')\
        .count()
    if show_draft_users:
        query = User.query\
            .join(Role, Role.id == User.role_id)\
            .filter(User.created == False)
    draft_users_num = User.query\
        .join(Role, Role.id == User.role_id)\
        .filter(User.created == False)\
        .count()
    if show_deleted_users:
        if current_user.is_administrator or current_user.is_developer:
            query = User.query\
                .join(Role, Role.id == User.role_id)\
                .filter(User.created == True)\
                .filter(User.deleted == True)\
                .order_by(User.last_seen_at.desc())
        else:
            return redirect(url_for('manage.activated_users'))
    deleted_users_num = User.query\
        .join(Role, Role.id == User.role_id)\
        .filter(User.created == True)\
        .filter(User.deleted == True)\
        .count()
    if show_volunteers:
        if current_user.is_volunteer or current_user.is_moderator or current_user.is_administrator or current_user.is_developer:
            query = User.query\
                .join(Role, Role.id == User.role_id)\
                .filter(User.created == True)\
                .filter(User.deleted == False)\
                .filter(Role.name == u'志愿者')\
                .order_by(User.last_seen_at.desc())
        else:
            return redirect(url_for('manage.activated_users'))
    volunteers_num = User.query\
        .join(Role, Role.id == User.role_id)\
        .filter(User.created == True)\
        .filter(User.deleted == False)\
        .filter(Role.name == u'志愿者')\
        .count()
    if show_moderators:
        if current_user.is_moderator or current_user.is_administrator or current_user.is_developer:
            query = User.query\
                .join(Role, Role.id == User.role_id)\
                .filter(User.created == True)\
                .filter(User.deleted == False)\
                .filter(Role.name == u'协管员')\
                .order_by(User.last_seen_at.desc())
        else:
            return redirect(url_for('manage.activated_users'))
    moderators_num = User.query\
        .join(Role, Role.id == User.role_id)\
        .filter(User.created == True)\
        .filter(User.deleted == False)\
        .filter(Role.name == u'协管员')\
        .count()
    if show_administrators:
        if current_user.is_administrator or current_user.is_developer:
            query = User.query\
                .join(Role, Role.id == User.role_id)\
                .filter(User.created == True)\
                .filter(User.deleted == False)\
                .filter(Role.name == u'管理员')\
                .order_by(User.last_seen_at.desc())
        else:
            return redirect(url_for('manage.activated_users'))
    administrators_num = User.query\
        .join(Role, Role.id == User.role_id)\
        .filter(User.created == True)\
        .filter(User.deleted == False)\
        .filter(Role.name == u'管理员')\
        .count()
    if show_developers:
        if current_user.is_developer:
            query = User.query\
                .join(Role, Role.id == User.role_id)\
                .filter(User.created == True)\
                .filter(User.deleted == False)\
                .filter(Role.name == u'开发人员')\
                .order_by(User.last_seen_at.desc())
        else:
            return redirect(url_for('manage.activated_users'))
    developers_num = User.query\
        .join(Role, Role.id == User.role_id)\
        .filter(User.created == True)\
        .filter(User.deleted == False)\
        .filter(Role.name == u'开发人员')\
        .count()
    if show_search_users:
        users = []
        keyword = request.args.get('keyword')
        if keyword:
            users = User.query\
                .filter(User.created == True)\
                .filter(User.deleted == False)\
                .filter(or_(
                    User.name.like('%' + keyword + '%'),
                    User.email.like('%' + keyword + '%')
                ))\
                .order_by(User.last_seen_at.desc())\
                .limit(current_app.config['RECORD_PER_QUERY'])\
                .all()
            search_form.keyword.data = keyword
        else:
            return redirect(url_for('manage.activated_users'))
        users = [user for user in users if not user.is_superior_than(user=current_user._get_current_object())]
        search_results_num = len(users)
        pagination = False
    if not show_search_users:
        search_results_num = 0
        page = request.args.get('page', 1, type=int)
        pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
        users = pagination.items
    return render_template('manage/user.html',
        form=form,
        search_form=search_form,
        show_activated_users=show_activated_users,
        activated_users_num=activated_users_num,
        show_unactivated_users=show_unactivated_users,
        unactivated_users_num=unactivated_users_num,
        show_suspended_users=show_suspended_users,
        suspended_users_num=suspended_users_num,
        show_draft_users=show_draft_users,
        draft_users_num=draft_users_num,
        show_deleted_users=show_deleted_users,
        deleted_users_num=deleted_users_num,
        show_volunteers=show_volunteers,
        volunteers_num=volunteers_num,
        show_moderators=show_moderators,
        moderators_num=moderators_num,
        show_administrators=show_administrators,
        administrators_num=administrators_num,
        show_developers=show_developers,
        developers_num=developers_num,
        show_search_users=show_search_users,
        search_results_num=search_results_num,
        pagination=pagination,
        users=users
    )


@manage.route('/user/activated')
@login_required
@permission_required(u'管理')
def activated_users():
    resp = make_response(redirect(url_for('manage.user')))
    resp.set_cookie('show_activated_users', '1', max_age=30*24*60*60)
    resp.set_cookie('show_unactivated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_suspended_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_draft_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_deleted_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_volunteers', '', max_age=30*24*60*60)
    resp.set_cookie('show_moderators', '', max_age=30*24*60*60)
    resp.set_cookie('show_administrators', '', max_age=30*24*60*60)
    resp.set_cookie('show_developers', '', max_age=30*24*60*60)
    resp.set_cookie('show_search_users', '', max_age=30*24*60*60)
    return resp


@manage.route('/user/unactivated')
@login_required
@permission_required(u'管理')
def unactivated_users():
    resp = make_response(redirect(url_for('manage.user')))
    resp.set_cookie('show_activated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_unactivated_users', '1', max_age=30*24*60*60)
    resp.set_cookie('show_suspended_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_draft_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_deleted_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_volunteers', '', max_age=30*24*60*60)
    resp.set_cookie('show_moderators', '', max_age=30*24*60*60)
    resp.set_cookie('show_administrators', '', max_age=30*24*60*60)
    resp.set_cookie('show_developers', '', max_age=30*24*60*60)
    resp.set_cookie('show_search_users', '', max_age=30*24*60*60)
    return resp


@manage.route('/user/suspended')
@login_required
@permission_required(u'管理')
def suspended_users():
    resp = make_response(redirect(url_for('manage.user')))
    resp.set_cookie('show_activated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_unactivated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_suspended_users', '1', max_age=30*24*60*60)
    resp.set_cookie('show_draft_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_deleted_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_volunteers', '', max_age=30*24*60*60)
    resp.set_cookie('show_moderators', '', max_age=30*24*60*60)
    resp.set_cookie('show_administrators', '', max_age=30*24*60*60)
    resp.set_cookie('show_developers', '', max_age=30*24*60*60)
    resp.set_cookie('show_search_users', '', max_age=30*24*60*60)
    return resp


@manage.route('/user/draft')
@login_required
@permission_required(u'管理')
def draft_users():
    resp = make_response(redirect(url_for('manage.user')))
    resp.set_cookie('show_activated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_unactivated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_suspended_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_draft_users', '1', max_age=30*24*60*60)
    resp.set_cookie('show_deleted_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_volunteers', '', max_age=30*24*60*60)
    resp.set_cookie('show_moderators', '', max_age=30*24*60*60)
    resp.set_cookie('show_administrators', '', max_age=30*24*60*60)
    resp.set_cookie('show_developers', '', max_age=30*24*60*60)
    resp.set_cookie('show_search_users', '', max_age=30*24*60*60)
    return resp


@manage.route('/user/deleted')
@login_required
@administrator_required
def deleted_users():
    resp = make_response(redirect(url_for('manage.user')))
    resp.set_cookie('show_activated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_unactivated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_suspended_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_draft_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_deleted_users', '1', max_age=30*24*60*60)
    resp.set_cookie('show_volunteers', '', max_age=30*24*60*60)
    resp.set_cookie('show_moderators', '', max_age=30*24*60*60)
    resp.set_cookie('show_administrators', '', max_age=30*24*60*60)
    resp.set_cookie('show_developers', '', max_age=30*24*60*60)
    resp.set_cookie('show_search_users', '', max_age=30*24*60*60)
    return resp


@manage.route('/user/volunteers')
@login_required
@permission_required(u'管理')
def volunteers():
    resp = make_response(redirect(url_for('manage.user')))
    resp.set_cookie('show_activated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_unactivated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_suspended_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_draft_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_deleted_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_volunteers', '1', max_age=30*24*60*60)
    resp.set_cookie('show_moderators', '', max_age=30*24*60*60)
    resp.set_cookie('show_administrators', '', max_age=30*24*60*60)
    resp.set_cookie('show_developers', '', max_age=30*24*60*60)
    resp.set_cookie('show_search_users', '', max_age=30*24*60*60)
    return resp


@manage.route('/user/moderators')
@login_required
@permission_required(u'管理用户')
def moderators():
    resp = make_response(redirect(url_for('manage.user')))
    resp.set_cookie('show_activated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_unactivated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_suspended_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_draft_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_deleted_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_volunteers', '', max_age=30*24*60*60)
    resp.set_cookie('show_moderators', '1', max_age=30*24*60*60)
    resp.set_cookie('show_administrators', '', max_age=30*24*60*60)
    resp.set_cookie('show_developers', '', max_age=30*24*60*60)
    resp.set_cookie('show_search_users', '', max_age=30*24*60*60)
    return resp


@manage.route('/user/administrators')
@login_required
@administrator_required
def administrators():
    resp = make_response(redirect(url_for('manage.user')))
    resp.set_cookie('show_activated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_unactivated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_suspended_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_draft_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_deleted_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_volunteers', '', max_age=30*24*60*60)
    resp.set_cookie('show_moderators', '', max_age=30*24*60*60)
    resp.set_cookie('show_administrators', '1', max_age=30*24*60*60)
    resp.set_cookie('show_developers', '', max_age=30*24*60*60)
    resp.set_cookie('show_search_users', '', max_age=30*24*60*60)
    return resp


@manage.route('/user/developers')
@login_required
@developer_required
def developers():
    resp = make_response(redirect(url_for('manage.user')))
    resp.set_cookie('show_activated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_unactivated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_suspended_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_draft_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_deleted_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_volunteers', '', max_age=30*24*60*60)
    resp.set_cookie('show_moderators', '', max_age=30*24*60*60)
    resp.set_cookie('show_administrators', '', max_age=30*24*60*60)
    resp.set_cookie('show_developers', '1', max_age=30*24*60*60)
    resp.set_cookie('show_search_users', '', max_age=30*24*60*60)
    return resp


@manage.route('/user/search/results')
@login_required
@permission_required(u'管理')
def search_user_results():
    resp = make_response(redirect(url_for('manage.user', keyword=request.args.get('keyword'))))
    resp.set_cookie('show_activated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_unactivated_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_suspended_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_draft_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_deleted_users', '', max_age=30*24*60*60)
    resp.set_cookie('show_volunteers', '', max_age=30*24*60*60)
    resp.set_cookie('show_moderators', '', max_age=30*24*60*60)
    resp.set_cookie('show_administrators', '', max_age=30*24*60*60)
    resp.set_cookie('show_developers', '', max_age=30*24*60*60)
    resp.set_cookie('show_search_users', '1', max_age=30*24*60*60)
    return resp


@manage.route('/user/create', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理用户')
def create_user():
    form = NewUserForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data.lower(),
            role_id=int(form.role.data),
            password=form.id_number.data.upper()[-6:],
            name=form.name.data,
            id_type_id=int(form.id_type.data),
            id_number=form.id_number.data.upper(),
            gender_id=int(form.gender.data),
            birthdate=form.birthdate.data,
            mobile=form.mobile.data,
            wechat=form.wechat.data,
            qq=form.qq.data,
            address=form.address.data,
            emergency_contact_name=form.emergency_contact_name.data,
            emergency_contact_relationship_id=int(form.emergency_contact_relationship.data),
            emergency_contact_mobile=form.emergency_contact_mobile.data,
            application_aim=form.application_aim.data,
            application_agency=form.application_agency.data
        )
        db.session.add(user)
        db.session.commit()
        # education
        if form.high_school.data:
            user.add_education_record(
                education_type=EducationType.query.filter_by(name=u'高中').first(),
                school=form.high_school.data,
                year=form.high_school_year.data
            )
        if form.bachelor_school.data:
            user.add_education_record(
                education_type=EducationType.query.filter_by(name=u'本科').first(),
                school=form.bachelor_school.data,
                major=form.bachelor_major.data,
                gpa=form.bachelor_gpa.data,
                full_gpa=form.bachelor_full_gpa.data,
                year=form.bachelor_year.data
            )
            if u'北京大学' in form.bachelor_school.data:
                user.add_tag(tag=Tag.query.filter_by(name=u'北大').first())
            if u'清华' in form.bachelor_school.data:
                user.add_tag(tag=Tag.query.filter_by(name=u'清华').first())
            if int(form.bachelor_full_gpa.data) == 100 and int(form.bachelor_gpa.data) >= 90:
                user.add_tag(tag=Tag.query.filter_by(name=u'GPA90+').first())
        if form.master_school.data:
            user.add_education_record(
                education_type=EducationType.query.filter_by(name=u'硕士').first(),
                school=form.master_school.data,
                major=form.master_major.data,
                gpa=form.master_gpa.data,
                full_gpa=form.master_full_gpa.data,
                year=form.master_year.data
            )
            if u'北京大学' in form.master_school.data:
                user.add_tag(tag=Tag.query.filter_by(name=u'北大').first())
            if u'清华' in form.master_school.data:
                user.add_tag(tag=Tag.query.filter_by(name=u'清华').first())
            if int(form.master_full_gpa.data) == 100 and int(form.master_gpa.data) >= 90:
                user.add_tag(tag=Tag.query.filter_by(name=u'GPA90+').first())
        if form.doctor_school.data:
            user.add_education_record(
                education_type=EducationType.query.filter_by(name=u'博士').first(),
                school=form.doctor_school.data,
                major=form.doctor_major.data,
                gpa=form.doctor_gpa.data,
                full_gpa=form.doctor_full_gpa.data,
                year=form.doctor_year.data
            )
            if u'北京大学' in form.doctor_school.data:
                user.add_tag(tag=Tag.query.filter_by(name=u'北大').first())
            if u'清华' in form.doctor_school.data:
                user.add_tag(tag=Tag.query.filter_by(name=u'清华').first())
            if int(form.doctor_full_gpa.data) == 100 and int(form.doctor_gpa.data) >= 90:
                user.add_tag(tag=Tag.query.filter_by(name=u'GPA90+').first())
        # employment
        if form.employer_1.data:
            user.add_employment_record(
                employer=form.employer_1.data,
                position=form.position_1.data,
                year=form.job_year_1.data
            )
        if form.employer_2.data:
            user.add_employment_record(
                employer=form.employer_2.data,
                position=form.position_2.data,
                year=form.job_year_2.data
            )
        # scores
        if form.cee_total.data:
            user.add_score_record(
                score_type=ScoreType.query.filter_by(name=u'高考总分').first(),
                score=form.cee_total.data,
                full_score=form.cee_total_full.data
            )
        if form.cee_math.data:
            user.add_score_record(
                score_type=ScoreType.query.filter_by(name=u'高考数学').first(),
                score=form.cee_math.data,
                full_score=form.cee_math_full.data
            )
            if int(form.cee_math_full.data) == 150 and int(form.cee_math.data) >= 135:
                user.add_tag(tag=Tag.query.filter_by(name=u'高考数学135+').first())
        if form.cee_english.data:
            user.add_score_record(
                score_type=ScoreType.query.filter_by(name=u'高考英语').first(),
                score=form.cee_english.data,
                full_score=form.cee_english_full.data
            )
        if form.cet_4.data:
            user.add_score_record(
                score_type=ScoreType.query.filter_by(name=u'大学英语四级').first(),
                score=form.cet_4.data
            )
        if form.cet_6.data:
            user.add_score_record(
                score_type=ScoreType.query.filter_by(name=u'大学英语六级').first(),
                score=form.cet_6.data
            )
            if int(form.cet_6.data) >= 600:
                user.add_tag(tag=Tag.query.filter_by(name=u'六级600+').first())
        if form.tem_4.data:
            user.add_score_record(
                score_type=ScoreType.query.filter_by(name=u'专业英语四级').first(),
                score=form.tem_4.data
            )
        if form.tem_8.data:
            user.add_score_record(
                score_type=ScoreType.query.filter_by(name=u'专业英语八级').first(),
                score=form.tem_8.data
            )
        if form.competition.data:
            user.add_score_record(
                score_type=ScoreType.query.filter_by(name=u'竞赛').first(),
                remark=form.competition.data
            )
            user.add_tag(tag=Tag.query.filter_by(name=u'竞赛').first())
        if form.other_score.data:
            user.add_score_record(
                score_type=ScoreType.query.filter_by(name=u'其它').first(),
                remark=form.other_score.data
            )
        # registration
        for purpose_type_id in form.purposes.data:
            user.add_purpose(purpose_type=PurposeType.query.get(int(purpose_type_id)))
        if form.other_purpose.data:
            user.add_purpose(purpose_type=PurposeType.query.filter_by(name=u'其它').first(), remark=form.other_purpose.data)
        for referrer_type_id in form.referrers.data:
            user.add_referrer(referrer_type=ReferrerType.query.get(int(referrer_type_id)))
        if form.other_referrer.data:
            user.add_referrer(referrer_type=ReferrerType.query.filter_by(name=u'其它').first(), remark=form.other_referrer.data)
        if form.inviter_email.data:
            inviter = User.query.filter_by(email=form.inviter_email.data.lower(), created=True, activated=True, deleted=False).first()
            if inviter is None:
                flash(u'推荐人邮箱不存在：%s' % form.inviter_email.data.lower(), category='error')
                return redirect(url_for('manage.create_user', id=user.id, next=request.args.get('next')))
            inviter.invite_user(user=user, invitation_type=InvitationType.query.filter_by(name=u'积分').first())
        if int(form.vb_course.data):
            user.register_course(course=Course.query.get(int(form.vb_course.data)))
        if int(form.y_gre_course.data):
            user.register_course(course=Course.query.get(int(form.y_gre_course.data)))
        for product_id in form.products.data:
            user.add_purchase(product=Product.query.get(int(product_id)))
        flash(u'资料填写完成，请确认信息', category='success')
        add_feed(user=current_user._get_current_object(), event=u'完成用户资料填写：%s' % user.name_alias, category=u'manage')
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
    if user.created:
        flash(u'%s已经被创建' % user.name_alias, category='error')
        return redirect(request.args.get('next') or url_for('manage.user'))
    if user.activated:
        flash(u'%s已经被激活' % user.name_alias, category='error')
        return redirect(request.args.get('next') or url_for('manage.user'))
    # name
    edit_name_form = EditNameForm(prefix='edit_name')
    if edit_name_form.validate_on_submit():
        user.name = edit_name_form.name.data
        db.session.add(user)
        flash(u'已更新用户姓名', category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    edit_name_form.name.data = user.name
    # gender
    edit_gender_form = EditGenderForm(prefix='edit_gender')
    if edit_gender_form.submit.data and edit_gender_form.validate_on_submit():
        user.gender_id = int(edit_gender_form.gender.data)
        db.session.add(user)
        flash(u'已更新性别', category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    edit_gender_form.gender.data = unicode(user.gender_id)
    # birthdate
    edit_birthdate_form = EditBirthdateForm(prefix='edit_birthdate')
    if edit_birthdate_form.submit.data and edit_birthdate_form.validate_on_submit():
        user.birthdate = edit_birthdate_form.birthdate.data
        db.session.add(user)
        flash(u'已更新出生日期', category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    edit_birthdate_form.birthdate.data = user.birthdate
    # ID number
    edit_id_number_form = EditIDNumberForm(prefix='edit_id_number')
    if edit_id_number_form.submit.data and edit_id_number_form.validate_on_submit():
        user.id_type_id = int(edit_id_number_form.id_type.data)
        user.id_number = edit_id_number_form.id_number.data
        db.session.add(user)
        flash(u'已更新身份证件', category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    edit_id_number_form.id_type.data = unicode(user.id_type_id)
    edit_id_number_form.id_number.data = user.id_number
    # tag
    edit_tag_form = EditUserTagForm(prefix='edit_tag')
    if edit_tag_form.submit.data and edit_tag_form.validate_on_submit():
        for tag in user.has_tags:
            user.remove_tag(tag=tag.tag)
        for tag_id in edit_tag_form.tags.data:
            user.add_tag(tag=Tag.query.get(int(tag_id)))
        flash(u'已更新用户标签', category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    edit_tag_form.tags.data = []
    for tag in user.has_tags:
        edit_tag_form.tags.data.append(unicode(tag.tag_id))
    # email
    edit_email_form = EditEmailForm(prefix='edit_email')
    if edit_email_form.submit.data and edit_email_form.validate_on_submit():
        if User.query.filter_by(email=edit_email_form.email.data.lower()).first() and edit_email_form.email.data.lower() != user.email:
            flash(u'%s已经被注册' % edit_email_form.email.data.lower(), category='error')
            return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
        if edit_email_form.email.data.lower() != user.email:
            user.email = edit_email_form.email.data.lower()
            db.session.add(user)
        flash(u'已更新用户邮箱', category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    edit_email_form.email.data = user.email
    # mobile
    edit_mobile_form = EditMobileForm(prefix='edit_mobile')
    if edit_mobile_form.submit.data and edit_mobile_form.validate_on_submit():
        user.mobile = edit_mobile_form.mobile.data
        db.session.add(user)
        flash(u'已更新移动电话', category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    edit_mobile_form.mobile.data = user.mobile
    # address
    edit_address_form = EditAddressForm(prefix='edit_address')
    if edit_address_form.submit.data and edit_address_form.validate_on_submit():
        user.address = edit_address_form.address.data
        db.session.add(user)
        flash(u'已更新联系地址', category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    edit_address_form.address.data = user.address
    # QQ
    edit_qq_form = EditQQForm(prefix='edit_qq')
    if edit_qq_form.submit.data and edit_qq_form.validate_on_submit():
        user.qq = edit_qq_form.qq.data
        db.session.add(user)
        flash(u'已更新QQ号', category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    edit_qq_form.qq.data = user.qq
    # WeChat
    edit_wechat_form = EditWeChatForm(prefix='edit_wechat')
    if edit_wechat_form.submit.data and edit_wechat_form.validate_on_submit():
        user.wechat = edit_wechat_form.wechat.data
        db.session.add(user)
        flash(u'已更新微信账号', category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    edit_wechat_form.wechat.data = user.wechat
    # emergency contact name
    edit_emergency_contact_name_form = EditEmergencyContactNameForm(prefix='edit_emergency_contact_name')
    if edit_emergency_contact_name_form.submit.data and edit_emergency_contact_name_form.validate_on_submit():
        user.emergency_contact_name = edit_emergency_contact_name_form.emergency_contact_name.data
        db.session.add(user)
        flash(u'已更新紧急联系人姓名', category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    edit_emergency_contact_name_form.emergency_contact_name.data = user.emergency_contact_name
    # emergency contact relationship
    edit_emergency_contact_relationship_form = EditEmergencyContactRelationshipForm(prefix='edit_emergency_contact_relationship')
    if edit_emergency_contact_relationship_form.submit.data and edit_emergency_contact_relationship_form.validate_on_submit():
        user.emergency_contact_relationship_id = int(edit_emergency_contact_relationship_form.emergency_contact_relationship.data)
        db.session.add(user)
        flash(u'已更新紧急联系人关系', category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    edit_emergency_contact_relationship_form.emergency_contact_relationship.data = unicode(user.emergency_contact_relationship_id)
    # emergency contact mobile
    edit_emergency_contact_mobile_form = EditEmergencyContactMobileForm(prefix='edit_emergency_contact_mobile')
    if edit_emergency_contact_mobile_form.submit.data and edit_emergency_contact_mobile_form.validate_on_submit():
        user.emergency_contact_mobile = edit_emergency_contact_mobile_form.emergency_contact_mobile.data
        db.session.add(user)
        flash(u'已更新紧急联系人移动电话', category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    edit_emergency_contact_mobile_form.emergency_contact_mobile.data = user.emergency_contact_mobile
    # education
    new_education_record_form = NewEducationRecordForm(prefix='new_education_record')
    if new_education_record_form.submit.data and new_education_record_form.validate_on_submit():
        education_type = EducationType.query.get(int(new_education_record_form.education_type.data))
        user.add_education_record(
            education_type=education_type,
            school=new_education_record_form.school.data,
            major=new_education_record_form.major.data,
            gpa=new_education_record_form.gpa.data,
            full_gpa=new_education_record_form.full_gpa.data,
            year=new_education_record_form.year.data
        )
        flash(u'已添加教育经历：%s %s' % (education_type.name, new_education_record_form.school.data), category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    # employment
    new_employment_record_form = NewEmploymentRecordForm(prefix='new_employment_record')
    if new_employment_record_form.submit.data and new_employment_record_form.validate_on_submit():
        user.add_employment_record(
            employer=new_employment_record_form.employer.data,
            position=new_employment_record_form.position.data,
            year=new_employment_record_form.year.data
        )
        flash(u'已添加工作经历：%s %s' % (new_employment_record_form.employer.data, new_employment_record_form.position.data), category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    # scores
    new_score_record_form = NewScoreRecordForm(prefix='new_score_record')
    if new_score_record_form.submit.data and new_score_record_form.validate_on_submit():
        score_type = ScoreType.query.get(int(new_score_record_form.score_type.data))
        if score_type.name in [u'高考总分', u'高考数学', u'高考英语', u'大学英语四级', u'大学英语六级', u'专业英语四级', u'专业英语八级']:
            user.add_score_record(
                score_type=score_type,
                score=new_score_record_form.score.data,
                full_score=new_score_record_form.full_score.data
            )
        if score_type.name in [u'竞赛', u'其它']:
            user.add_score_record(
                score_type=score_type,
                remark=new_score_record_form.score.data
            )
        flash(u'已添加既往成绩：%s' % score_type.name, category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    # purpose
    edit_purpose_form = EditPurposeForm(prefix='edit_purpose')
    if edit_purpose_form.submit.data and edit_purpose_form.validate_on_submit():
        for purpose in user.purposes:
            if purpose.type.name != u'其它':
                user.remove_purpose(purpose_type=purpose.type)
        for purpose_type_id in edit_purpose_form.purposes.data:
            user.add_purpose(purpose_type=PurposeType.query.get(int(purpose_type_id)))
        if edit_purpose_form.other_purpose.data:
            user.add_purpose(purpose_type=PurposeType.query.filter_by(name=u'其它').first(), remark=edit_purpose_form.other_purpose.data)
        flash(u'已更新研修目的', category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    edit_purpose_form.purposes.data = []
    for purpose in user.purposes:
        if purpose.type.name != u'其它':
            edit_purpose_form.purposes.data.append(unicode(purpose.type_id))
        else:
            edit_purpose_form.other_purpose.data = purpose.remark
    # application
    edit_application_form = EditApplicationForm(prefix='edit_application')
    if edit_application_form.submit.data and edit_application_form.validate_on_submit():
        user.application_aim = edit_application_form.application_aim.data
        user.application_agency = edit_application_form.application_agency.data
        db.session.add(user)
        flash(u'已更新申请信息', category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    edit_application_form.application_aim.data = user.application_aim
    edit_application_form.application_agency.data = user.application_agency
    # referrer
    edit_referrer_form = EditReferrerForm(prefix='edit_referrer')
    if edit_referrer_form.submit.data and edit_referrer_form.validate_on_submit():
        for referrer in user.referrers:
            if referrer.type.name != u'其它':
                user.remove_referrer(referrer_type=referrer.type)
        for referrer_type_id in edit_referrer_form.referrers.data:
            user.add_referrer(referrer_type=ReferrerType.query.get(int(referrer_type_id)))
        if edit_referrer_form.other_referrer.data:
            user.add_referrer(referrer_type=ReferrerType.query.filter_by(name=u'其它').first(), remark=edit_referrer_form.other_referrer.data)
        flash(u'已更新了解渠道', category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    edit_referrer_form.referrers.data = []
    for referrer in user.referrers:
        if referrer.type.name != u'其它':
            edit_referrer_form.referrers.data.append(unicode(referrer.type_id))
        else:
            edit_referrer_form.other_referrer.data = referrer.remark
    # inviter
    new_inviter_form = NewInviterForm(prefix='new_inviter')
    if new_inviter_form.submit.data and new_inviter_form.validate_on_submit():
        inviter = User.query.filter_by(email=new_inviter_form.inviter_email.data.lower(), created=True, activated=True, deleted=False).first()
        if inviter is None:
            flash(u'推荐人邮箱不存在：%s' % new_inviter_form.inviter_email.data.lower(), category='error')
            return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
        if inviter.invited_user(user=user):
            flash(u'推荐人已存在：%s' % new_inviter_form.inviter_email.data.lower(), category='warning')
            return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
        inviter.invite_user(user=user, invitation_type=InvitationType.query.filter_by(name=u'积分').first())
        flash(u'已添加推荐人：%s' % inviter.name_alias, category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    # purchase
    new_purchase_form = NewPurchaseForm(prefix='new_purchase')
    if new_purchase_form.submit.data and new_purchase_form.validate_on_submit():
        product = Product.query.get_or_404(int(new_purchase_form.product.data))
        if product.name in [u'按月延长有效期', u'一次性延长2年有效期'] and user.overdue:
            user.add_overdue_suspension(modified_by=current_user._get_current_object())
        user.add_purchase(product=product, quantity=new_purchase_form.quantity.data)
        flash(u'已添加研修产品：%s×%s' % (product.alias, new_purchase_form.quantity.data), category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    # role
    edit_role_form = EditStudentRoleForm(prefix='edit_role')
    if edit_role_form.submit.data and edit_role_form.validate_on_submit():
        user.role_id = int(edit_role_form.role.data)
        db.session.add(user)
        flash(u'已更新用户权限', category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    edit_role_form.role.data = unicode(user.role_id)
    # VB course
    edit_vb_course_form = EditVBCourseForm(prefix='edit_vb_course')
    if edit_vb_course_form.submit.data and edit_vb_course_form.validate_on_submit():
        if user.vb_course:
            user.unregister_course(user.vb_course)
        if int(edit_vb_course_form.vb_course.data):
            user.register_course(Course.query.get(int(edit_vb_course_form.vb_course.data)))
        flash(u'已更新VB班级', category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    if user.vb_course:
        edit_vb_course_form.vb_course.data = unicode(user.vb_course.id)
    # Y-GRE course
    edit_y_gre_course_form = EditYGRECourseForm(prefix='edit_y_gre_course')
    if edit_y_gre_course_form.submit.data and edit_y_gre_course_form.validate_on_submit():
        if user.y_gre_course:
            user.unregister_course(user.y_gre_course)
        if int(edit_y_gre_course_form.y_gre_course.data):
            user.register_course(Course.query.get(int(edit_y_gre_course_form.y_gre_course.data)))
        flash(u'已更新Y-GRE班', category='success')
        return redirect(url_for('manage.create_user_confirm', id=user.id, next=request.args.get('next')))
    if user.y_gre_course:
        edit_y_gre_course_form.y_gre_course.data = unicode(user.y_gre_course.id)
    # confirm
    confirm_user_form = ConfirmUserForm(prefix='confirm_user')
    if confirm_user_form.submit.data and confirm_user_form.validate_on_submit():
        user.worked_in_same_field = confirm_user_form.worked_in_same_field.data
        user.deformity = confirm_user_form.deformity.data
        db.session.add(user)
        if confirm_user_form.paid_in_full.data:
            user.remove_tag(tag=Tag.query.filter_by(name=u'未缴全款').first())
        else:
            user.add_tag(tag=Tag.query.filter_by(name=u'未缴全款').first())
        receptionist = User.query.filter_by(email=confirm_user_form.receptionist_email.data.lower(), created=True, activated=True, deleted=False).first()
        if receptionist is None:
            flash(u'接待人邮箱不存在：%s' % confirm_user_form.receptionist_email.data.lower(), category='error')
        receptionist.receive_user(user=user)
        current_user.create_user(user=user)
        flash(u'成功添加%s：%s' % (user.role.name, user.name), category='success')
        add_feed(user=current_user._get_current_object(), event=u'添加%s：%s' % (user.role.name, user.name), category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.user'))
    confirm_user_form.worked_in_same_field.data = user.worked_in_same_field
    confirm_user_form.deformity.data = user.deformity
    return render_template('manage/create_user_confirm.html',
        edit_name_form=edit_name_form,
        edit_gender_form=edit_gender_form,
        edit_birthdate_form=edit_birthdate_form,
        edit_id_number_form=edit_id_number_form,
        edit_tag_form=edit_tag_form,
        edit_email_form=edit_email_form,
        edit_mobile_form=edit_mobile_form,
        edit_address_form=edit_address_form,
        edit_qq_form=edit_qq_form,
        edit_wechat_form=edit_wechat_form,
        edit_emergency_contact_name_form=edit_emergency_contact_name_form,
        edit_emergency_contact_relationship_form=edit_emergency_contact_relationship_form,
        edit_emergency_contact_mobile_form=edit_emergency_contact_mobile_form,
        new_education_record_form=new_education_record_form,
        new_employment_record_form=new_employment_record_form,
        new_score_record_form=new_score_record_form,
        edit_purpose_form=edit_purpose_form,
        edit_application_form=edit_application_form,
        edit_referrer_form=edit_referrer_form,
        new_inviter_form=new_inviter_form,
        new_purchase_form=new_purchase_form,
        edit_role_form=edit_role_form,
        edit_vb_course_form=edit_vb_course_form,
        edit_y_gre_course_form=edit_y_gre_course_form,
        confirm_user_form=confirm_user_form,
        user=user
    )


@manage.route('/user/create/delete/<int:id>')
@login_required
@permission_required(u'管理用户')
def create_user_delete(id):
    user = User.query.get_or_404(id)
    if user.deleted:
        abort(404)
    if user.is_superior_than(user=current_user._get_current_object()):
        abort(403)
    if user.created:
        flash(u'%s已经被创建' % user.name_alias, category='error')
        return redirect(request.args.get('next') or url_for('manage.user'))
    if user.activated:
        flash(u'%s已经被激活' % user.name_alias, category='error')
        return redirect(request.args.get('next') or url_for('manage.user'))
    user.delete()
    flash(u'已删除用户：%s' % user.name_alias, category='success')
    add_feed(user=current_user._get_current_object(), event=u'删除用户：%s' % user.name_alias, category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.user'))


@manage.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理用户')
def edit_user(id):
    user = User.query.get_or_404(id)
    if not user.created or user.deleted:
        abort(404)
    if (not current_user.is_moderator and user.is_superior_than(user=current_user._get_current_object())) or (current_user.is_moderator and (user.id != current_user.id or not current_user.is_superior_than(user=user))):
        abort(403)
    # name
    edit_name_form = EditNameForm(prefix='edit_name')
    if edit_name_form.submit.data and edit_name_form.validate_on_submit():
        user.name = edit_name_form.name.data
        db.session.add(user)
        flash(u'已更新用户姓名', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新用户姓名为“%s”' % (user.name_alias, edit_name_form.name.data), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    edit_name_form.name.data = user.name
    # gender
    edit_gender_form = EditGenderForm(prefix='edit_gender')
    if edit_gender_form.submit.data and edit_gender_form.validate_on_submit():
        user.gender_id = int(edit_gender_form.gender.data)
        db.session.add(user)
        flash(u'已更新性别', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新性别为“%s”' % (user.name_alias, Gender.query.get(int(edit_gender_form.gender.data)).name), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    edit_gender_form.gender.data = unicode(user.gender_id)
    # birthdate
    edit_birthdate_form = EditBirthdateForm(prefix='edit_birthdate')
    if edit_birthdate_form.submit.data and edit_birthdate_form.validate_on_submit():
        user.birthdate = edit_birthdate_form.birthdate.data
        db.session.add(user)
        flash(u'已更新出生日期', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新出生日期为“%s”' % (user.name_alias, edit_birthdate_form.birthdate.data), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    edit_birthdate_form.birthdate.data = user.birthdate
    # ID number
    edit_id_number_form = EditIDNumberForm(prefix='edit_id_number')
    if edit_id_number_form.submit.data and edit_id_number_form.validate_on_submit():
        user.id_type_id = int(edit_id_number_form.id_type.data)
        user.id_number = edit_id_number_form.id_number.data
        db.session.add(user)
        flash(u'已更新身份证件', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新身份证件为“%s：%s”' % (user.name_alias, IDType.query.get(int(edit_id_number_form.id_type.data)).name, edit_id_number_form.id_number.data), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    edit_id_number_form.id_type.data = unicode(user.id_type_id)
    edit_id_number_form.id_number.data = user.id_number
    # role
    edit_role_form = EditUserRoleForm(prefix='edit_role', editor=current_user._get_current_object(), is_self=(user.id == current_user.id))
    if edit_role_form.submit.data and edit_role_form.validate_on_submit():
        user.role_id = int(edit_role_form.role.data)
        db.session.add(user)
        flash(u'已更新用户权限', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新用户权限为“%s”' % (user.name_alias, Role.query.get(int(edit_role_form.role.data)).name), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    edit_role_form.role.data = unicode(user.role_id)
    # VB course
    edit_vb_course_form = EditVBCourseForm(prefix='edit_vb_course')
    if edit_vb_course_form.submit.data and edit_vb_course_form.validate_on_submit():
        if user.vb_course:
            user.unregister_course(user.vb_course)
        if int(edit_vb_course_form.vb_course.data):
            user.register_course(Course.query.get(int(edit_vb_course_form.vb_course.data)))
        flash(u'已更新VB班级', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新VB班级为“%s”' % (user.name_alias, Course.query.get(int(edit_vb_course_form.vb_course.data)).name), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    if user.vb_course:
        edit_vb_course_form.vb_course.data = unicode(user.vb_course.id)
    # Y-GRE course
    edit_y_gre_course_form = EditYGRECourseForm(prefix='edit_y_gre_course')
    if edit_y_gre_course_form.submit.data and edit_y_gre_course_form.validate_on_submit():
        if user.y_gre_course:
            user.unregister_course(user.y_gre_course)
        if int(edit_y_gre_course_form.y_gre_course.data):
            user.register_course(Course.query.get(int(edit_y_gre_course_form.y_gre_course.data)))
        flash(u'已更新Y-GRE班', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新Y-GRE班级为“%s”' % (user.name_alias, Course.query.get(int(edit_y_gre_course_form.y_gre_course.data)).name), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    if user.y_gre_course:
        edit_y_gre_course_form.y_gre_course.data = unicode(user.y_gre_course.id)
    # tag
    edit_tag_form = EditUserTagForm(prefix='edit_tag')
    if edit_tag_form.submit.data and edit_tag_form.validate_on_submit():
        for tag in user.has_tags:
            user.remove_tag(tag=tag.tag)
        new_tags = []
        for tag_id in edit_tag_form.tags.data:
            user.add_tag(tag=Tag.query.get(int(tag_id)))
        new_tags.append(Tag.query.get(int(tag_id)).name)
        flash(u'已更新用户标签', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新用户标签为“%s”' % (user.name_alias, u'、'.join(new_tags)), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    edit_tag_form.tags.data = []
    for tag in user.has_tags:
        edit_tag_form.tags.data.append(unicode(tag.tag_id))
    # email
    edit_email_form = EditEmailForm(prefix='edit_email')
    if edit_email_form.submit.data and edit_email_form.validate_on_submit():
        if User.query.filter_by(email=edit_email_form.email.data.lower()).first() and edit_email_form.email.data.lower() != user.email:
            flash(u'%s已经被注册' % edit_email_form.email.data.lower(), category='error')
            return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
        if edit_email_form.email.data.lower() != user.email:
            if user.confirmed:
                token = user.generate_email_change_token(edit_email_form.email.data.lower())
                send_email(edit_email_form.email.data.lower(), u'确认您的邮箱账户', 'auth/mail/change_email', user=user, token=token)
                flash(u'一封确认邮件已经发送至邮箱：%s' % edit_email_form.email.data.lower(), category='info')
                return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
            user.email = edit_email_form.email.data.lower()
            db.session.add(user)
        flash(u'已更新用户邮箱', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新用户邮箱为“%s”' % (user.name_alias, edit_email_form.email.data.lower()), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    edit_email_form.email.data = user.email
    # mobile
    edit_mobile_form = EditMobileForm(prefix='edit_mobile')
    if edit_mobile_form.submit.data and edit_mobile_form.validate_on_submit():
        user.mobile = edit_mobile_form.mobile.data
        db.session.add(user)
        flash(u'已更新移动电话', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新移动电话为“%s”' % (user.name_alias, edit_mobile_form.mobile.data), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    edit_mobile_form.mobile.data = user.mobile
    # address
    edit_address_form = EditAddressForm(prefix='edit_address')
    if edit_address_form.submit.data and edit_address_form.validate_on_submit():
        user.address = edit_address_form.address.data
        db.session.add(user)
        flash(u'已更新联系地址', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新联系地址为“%s”' % (user.name_alias, edit_address_form.address.data), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    edit_address_form.address.data = user.address
    # QQ
    edit_qq_form = EditQQForm(prefix='edit_qq')
    if edit_qq_form.submit.data and edit_qq_form.validate_on_submit():
        user.qq = edit_qq_form.qq.data
        db.session.add(user)
        flash(u'已更新QQ号', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新QQ号为“%s”' % (user.name_alias, edit_qq_form.qq.data), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    edit_qq_form.qq.data = user.qq
    # WeChat
    edit_wechat_form = EditWeChatForm(prefix='edit_wechat')
    if edit_wechat_form.submit.data and edit_wechat_form.validate_on_submit():
        user.wechat = edit_wechat_form.wechat.data
        db.session.add(user)
        flash(u'已更新微信账号', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新微信账号为“%s”' % (user.name_alias, edit_wechat_form.wechat.data), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    edit_wechat_form.wechat.data = user.wechat
    # emergency contact name
    edit_emergency_contact_name_form = EditEmergencyContactNameForm(prefix='edit_emergency_contact_name')
    if edit_emergency_contact_name_form.submit.data and edit_emergency_contact_name_form.validate_on_submit():
        user.emergency_contact_name = edit_emergency_contact_name_form.emergency_contact_name.data
        db.session.add(user)
        flash(u'已更新紧急联系人姓名', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新紧急联系人姓名为“%s”' % (user.name_alias, edit_emergency_contact_name_form.emergency_contact_name.data), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    edit_emergency_contact_name_form.emergency_contact_name.data = user.emergency_contact_name
    # emergency contact relationship
    edit_emergency_contact_relationship_form = EditEmergencyContactRelationshipForm(prefix='edit_emergency_contact_relationship')
    if edit_emergency_contact_relationship_form.submit.data and edit_emergency_contact_relationship_form.validate_on_submit():
        user.emergency_contact_relationship_id = int(edit_emergency_contact_relationship_form.emergency_contact_relationship.data)
        db.session.add(user)
        flash(u'已更新紧急联系人关系', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新紧急联系人关系为“%s”' % (user.name_alias, Relationship.query.get(int(edit_emergency_contact_relationship_form.emergency_contact_relationship.data)).name), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    edit_emergency_contact_relationship_form.emergency_contact_relationship.data = unicode(user.emergency_contact_relationship_id)
    # emergency contact mobile
    edit_emergency_contact_mobile_form = EditEmergencyContactMobileForm(prefix='edit_emergency_contact_mobile')
    if edit_emergency_contact_mobile_form.submit.data and edit_emergency_contact_mobile_form.validate_on_submit():
        user.emergency_contact_mobile = edit_emergency_contact_mobile_form.emergency_contact_mobile.data
        db.session.add(user)
        flash(u'已更新紧急联系人移动电话', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新紧急联系人移动电话为“%s”' % (user.name_alias, edit_emergency_contact_mobile_form.emergency_contact_mobile.data), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    edit_emergency_contact_mobile_form.emergency_contact_mobile.data = user.emergency_contact_mobile
    # education
    new_education_record_form = NewEducationRecordForm(prefix='new_education_record')
    if new_education_record_form.submit.data and new_education_record_form.validate_on_submit():
        education_type = EducationType.query.get(int(new_education_record_form.education_type.data))
        user.add_education_record(
            education_type=education_type,
            school=new_education_record_form.school.data,
            major=new_education_record_form.major.data,
            gpa=new_education_record_form.gpa.data,
            full_gpa=new_education_record_form.full_gpa.data,
            year=new_education_record_form.year.data
        )
        flash(u'已添加教育经历：%s %s' % (education_type.name, new_education_record_form.school.data), category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：添加教育经历“%s %s”' % (user.name_alias, education_type.name, new_education_record_form.school.data), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    # employment
    new_employment_record_form = NewEmploymentRecordForm(prefix='new_employment_record')
    if new_employment_record_form.submit.data and new_employment_record_form.validate_on_submit():
        user.add_employment_record(
            employer=new_employment_record_form.employer.data,
            position=new_employment_record_form.position.data,
            year=new_employment_record_form.year.data
        )
        flash(u'已添加工作经历：%s %s' % (new_employment_record_form.employer.data, new_employment_record_form.position.data), category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：添加工作经历“%s %s”' % (user.name_alias, new_employment_record_form.employer.data, new_employment_record_form.position.data), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    # scores
    new_score_record_form = NewScoreRecordForm(prefix='new_score_record')
    if new_score_record_form.submit.data and new_score_record_form.validate_on_submit():
        score_type = ScoreType.query.get(int(new_score_record_form.score_type.data))
        if score_type.name in [u'高考总分', u'高考数学', u'高考英语', u'大学英语四级', u'大学英语六级', u'专业英语四级', u'专业英语八级']:
            user.add_score_record(
                score_type=score_type,
                score=new_score_record_form.score.data,
                full_score=new_score_record_form.full_score.data
            )
        if score_type.name in [u'竞赛', u'其它']:
            user.add_score_record(
                score_type=score_type,
                remark=new_score_record_form.score.data
            )
        flash(u'已添加既往成绩：%s' % score_type.name, category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：添加既往成绩“%s”' % (user.name_alias, score_type.name), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    # purpose
    edit_purpose_form = EditPurposeForm(prefix='edit_purpose')
    if edit_purpose_form.submit.data and edit_purpose_form.validate_on_submit():
        for purpose in user.purposes:
            if purpose.type.name != u'其它':
                user.remove_purpose(purpose_type=purpose.type)
        for purpose_type_id in edit_purpose_form.purposes.data:
            user.add_purpose(purpose_type=PurposeType.query.get(int(purpose_type_id)))
        if edit_purpose_form.other_purpose.data:
            user.add_purpose(purpose_type=PurposeType.query.filter_by(name=u'其它').first(), remark=edit_purpose_form.other_purpose.data)
        flash(u'已更新研修目的', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新研修目的' % user.name_alias, category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    edit_purpose_form.purposes.data = []
    for purpose in user.purposes:
        if purpose.type.name != u'其它':
            edit_purpose_form.purposes.data.append(unicode(purpose.type_id))
        else:
            edit_purpose_form.other_purpose.data = purpose.remark
    # application
    edit_application_form = EditApplicationForm(prefix='edit_application')
    if edit_application_form.submit.data and edit_application_form.validate_on_submit():
        user.application_aim = edit_application_form.application_aim.data
        user.application_agency = edit_application_form.application_agency.data
        db.session.add(user)
        flash(u'已更新申请信息', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新申请信息为“%s %s”' % (user.name_alias, edit_application_form.application_aim.data, edit_application_form.application_agency.data), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    edit_application_form.application_aim.data = user.application_aim
    edit_application_form.application_agency.data = user.application_agency
    # referrer
    edit_referrer_form = EditReferrerForm(prefix='edit_referrer')
    if edit_referrer_form.submit.data and edit_referrer_form.validate_on_submit():
        for referrer in user.referrers:
            if referrer.type.name != u'其它':
                user.remove_referrer(referrer_type=referrer.type)
        for referrer_type_id in edit_referrer_form.referrers.data:
            user.add_referrer(referrer_type=ReferrerType.query.get(int(referrer_type_id)))
        if edit_referrer_form.other_referrer.data:
            user.add_referrer(referrer_type=ReferrerType.query.filter_by(name=u'其它').first(), remark=edit_referrer_form.other_referrer.data)
        flash(u'已更新了解渠道', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新了解渠道' % user.name_alias, category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    edit_referrer_form.referrers.data = []
    for referrer in user.referrers:
        if referrer.type.name != u'其它':
            edit_referrer_form.referrers.data.append(unicode(referrer.type_id))
        else:
            edit_referrer_form.other_referrer.data = referrer.remark
    # inviter
    new_inviter_form = NewInviterForm(prefix='new_inviter')
    if new_inviter_form.submit.data and new_inviter_form.validate_on_submit():
        inviter = User.query.filter_by(email=new_inviter_form.inviter_email.data.lower(), created=True, activated=True, deleted=False).first()
        if inviter is None:
            flash(u'推荐人邮箱不存在：%s' % new_inviter_form.inviter_email.data.lower(), category='error')
            return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
        if inviter.id == user.id:
            flash(u'推荐人邮箱有误：%s' % new_inviter_form.inviter_email.data.lower(), category='error')
            return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
        if inviter.invited_user(user=user):
            flash(u'推荐人已存在：%s' % new_inviter_form.inviter_email.data.lower(), category='warning')
            return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
        inviter.invite_user(user=user, invitation_type=InvitationType.query.filter_by(name=u'积分').first())
        flash(u'已添加推荐人：%s' % inviter.name_alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：添加推荐人“%s”' % (user.name_alias, inviter.name_alias), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    # purchase
    new_purchase_form = NewPurchaseForm(prefix='new_purchase')
    if new_purchase_form.submit.data and new_purchase_form.validate_on_submit():
        product = Product.query.get_or_404(int(new_purchase_form.product.data))
        user.add_purchase(product=product, quantity=new_purchase_form.quantity.data)
        flash(u'已添加研修产品：%s×%s' % (product.alias, new_purchase_form.quantity.data), category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：添加研修产品“%s×%s”' % (user.name_alias, product.alias, new_purchase_form.quantity.data), category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    # worked_in_same_field
    edit_worked_in_same_field_form = EditWorkInSameFieldForm(prefix='edit_worked_in_same_field')
    if edit_worked_in_same_field_form.submit.data and edit_worked_in_same_field_form.validate_on_submit():
        user.worked_in_same_field = edit_worked_in_same_field_form.worked_in_same_field.data
        db.session.add(user)
        flash(u'已更新“（曾）在培训/留学机构任职”状态', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新“（曾）在培训/留学机构任职”状态' % user.name_alias, category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    edit_worked_in_same_field_form.worked_in_same_field.data = user.worked_in_same_field
    # deformity
    edit_deformity_form = EditDeformityForm(prefix='edit_deformity')
    if edit_deformity_form.submit.data and edit_deformity_form.validate_on_submit():
        user.deformity = edit_deformity_form.deformity.data
        db.session.add(user)
        flash(u'已更新“有严重心理或身体疾病”状态', category='success')
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：更新“有严重心理或身体疾病”状态' % user.name_alias, category=u'manage')
        return redirect(url_for('manage.edit_user', id=user.id, next=request.args.get('next')))
    edit_deformity_form.deformity.data = user.deformity
    # receptionist
    return render_template('manage/edit_user.html',
        edit_name_form=edit_name_form,
        edit_gender_form=edit_gender_form,
        edit_birthdate_form=edit_birthdate_form,
        edit_id_number_form=edit_id_number_form,
        edit_role_form=edit_role_form,
        edit_vb_course_form=edit_vb_course_form,
        edit_y_gre_course_form=edit_y_gre_course_form,
        edit_tag_form=edit_tag_form,
        edit_email_form=edit_email_form,
        edit_mobile_form=edit_mobile_form,
        edit_address_form=edit_address_form,
        edit_qq_form=edit_qq_form,
        edit_wechat_form=edit_wechat_form,
        edit_emergency_contact_name_form=edit_emergency_contact_name_form,
        edit_emergency_contact_relationship_form=edit_emergency_contact_relationship_form,
        edit_emergency_contact_mobile_form=edit_emergency_contact_mobile_form,
        new_education_record_form=new_education_record_form,
        new_employment_record_form=new_employment_record_form,
        new_score_record_form=new_score_record_form,
        edit_purpose_form=edit_purpose_form,
        edit_application_form=edit_application_form,
        edit_referrer_form=edit_referrer_form,
        new_inviter_form=new_inviter_form,
        new_purchase_form=new_purchase_form,
        edit_worked_in_same_field_form=edit_worked_in_same_field_form,
        edit_deformity_form=edit_deformity_form,
        user=user
    )


@manage.route('/user/education-record/remove/<int:id>')
@login_required
@permission_required(u'管理用户')
def remove_education_record(id):
    education_record = EducationRecord.query.get_or_404(id)
    db.session.delete(education_record)
    flash(u'已删除教育经历：%s %s' % (education_record.type.name, education_record.school), category='success')
    if user.created:
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：删除教育经历“%s %s”' % (user.name_alias, education_record.type.name, education_record.school), category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.user'))


@manage.route('/user/employment-record/remove/<int:id>')
@login_required
@permission_required(u'管理用户')
def remove_employment_record(id):
    employment_record = EmploymentRecord.query.get_or_404(id)
    db.session.delete(employment_record)
    flash(u'已删除工作经历：%s %s' % (employment_record.employer, employment_record.position), category='success')
    if user.created:
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：删除工作经历“%s %s”' % (user.name_alias, employment_record.employer, employment_record.position), category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.user'))


@manage.route('/user/score-record/remove/<int:id>')
@login_required
@permission_required(u'管理用户')
def remove_score_record(id):
    score_record = ScoreRecord.query.get_or_404(id)
    db.session.delete(score_record)
    flash(u'已删除既往成绩：%s' % score_record.type.name, category='success')
    if user.created:
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：删除既往成绩“%s”' % (user.name_alias, score_record.type.name), category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.user'))


@manage.route('/user/inviter/remove/<int:user_id>/<int:inviter_id>')
@login_required
@permission_required(u'管理用户')
def remove_inviter(user_id, inviter_id):
    user = User.query.get_or_404(user_id)
    inviter = User.query.get_or_404(inviter_id)
    inviter.uninvite_user(user=user)
    flash(u'已删除推荐人：%s' % inviter.name_alias, category='success')
    if user.created:
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：删除推荐人“%s”' % (user.name_alias, inviter.name_alias), category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.user'))


@manage.route('/user/purchase/remove/<int:id>')
@login_required
@permission_required(u'管理用户')
def remove_purchase(id):
    purchase = Purchase.query.get_or_404(id)
    db.session.delete(purchase)
    flash(u'已删除研修产品：%s' % purchase.alias, category='success')
    if user.created:
        add_feed(user=current_user._get_current_object(), event=u'编辑“%s”的资料：删除研修产品“%s”' % (user.name_alias, purchase.alias), category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.user'))


@manage.route('/user/delete/<int:id>')
@login_required
@permission_required(u'管理用户')
def delete_user(id):
    user = User.query.get_or_404(id)
    if not user.created or user.deleted:
        abort(404)
    if user.id == current_user.id or (not current_user.is_moderator and user.is_superior_than(user=current_user._get_current_object())) or (current_user.is_moderator and not current_user.is_superior_than(user=user)):
        abort(403)
    user.safe_delete()
    flash(u'已注销用户：%s' % user.name_alias, category='success')
    add_feed(user=current_user._get_current_object(), event=u'注销用户：%s' % user.name_alias, category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.user'))


@manage.route('/user/restore/<int:id>', methods=['GET', 'POST'])
@login_required
@administrator_required
def restore_user(id):
    user = User.query.get_or_404(id)
    if not user.created or not user.deleted:
        abort(404)
    if user.is_superior_than(user=current_user._get_current_object()):
        abort(403)
    form = RestoreUserForm(restorer=current_user._get_current_object())
    if form.validate_on_submit():
        role = Role.query.get(int(form.role.data))
        user.restore(email=form.email.data.lower(), role=role, reset_due_time=form.reset_due_time.data)
        flash(u'已恢复用户：%s' % user.name_alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'恢复用户：%s' % user.name_alias, category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.user'))
    form.email.data = user.email[:-len(u'_%s_deleted' % user.id)]
    form.role.data = unicode(user.role_id)
    return render_template('manage/restore_user.html', form=form, user=user)


@manage.route('/user/toggle-suspension/<int:id>')
@login_required
@permission_required(u'管理用户')
def toggle_suspension(id):
    user = User.query.get_or_404(id)
    if not user.created or user.deleted:
        abort(404)
    if (not current_user.is_moderator and user.is_superior_than(user=current_user._get_current_object())) or (current_user.is_moderator and (user.id != current_user.id or not current_user.is_superior_than(user=user))):
        abort(403)
    if user.is_suspended:
        user.end_suspension(modified_by=current_user._get_current_object())
        flash(u'已恢复用户：%s' % user.name_alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'恢复用户：%s' % user.name_alias, category=u'manage')
    else:
        user.start_suspension(modified_by=current_user._get_current_object())
        flash(u'已挂起用户：%s' % user.name_alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'挂起用户：%s' % user.name_alias, category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.user'))


@manage.route('/course', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理班级')
def course():
    form = NewCourseForm()
    if form.validate_on_submit():
        course = Course(name=form.name.data, type_id=int(form.course_type.data), show=form.show.data, modified_by_id=current_user.id)
        db.session.add(course)
        flash(u'添加班级：%s' % form.name.data, category='success')
        add_feed(user=current_user._get_current_object(), event=u'添加班级：%s' % form.name.data, category=u'manage')
        return redirect(url_for('manage.course', page=request.args.get('page', 1, type=int)))
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
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    courses = pagination.items
    return render_template('manage/course.html',
        form=form,
        show_vb_courses=show_vb_courses,
        show_y_gre_courses=show_y_gre_courses,
        pagination=pagination,
        courses=courses
    )


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
def course_user(id):
    course = Course.query.get_or_404(id)
    if course.deleted:
        abort(404)
    if course.valid_registrations.count() == 0:
        return redirect(url_for('manage.course'))
    query = User.query\
        .join(CourseRegistration, CourseRegistration.user_id == User.id)\
        .filter(CourseRegistration.course_id == course.id)\
        .filter(User.created == True)\
        .filter(User.deleted == False)
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    users = pagination.items
    return render_template('manage/course_user.html',
        course=course,
        pagination=pagination,
        users=users
    )


@manage.route('/course/toggle-show/<int:id>')
@login_required
@permission_required(u'管理班级')
def toggle_course_show(id):
    course = Course.query.get_or_404(id)
    if course.deleted:
        abort(404)
    course.toggle_show(modified_by=current_user._get_current_object())
    if course.show:
        flash(u'班级“%s”的可选状态改为：可选' % course.name, category='success')
        add_feed(user=current_user._get_current_object(), event=u'修改班级“%s”的可选状态改为：可选' % course.name, category=u'manage')
    else:
        flash(u'班级“%s”的可选状态改为：不可选' % course.name, category='success')
        add_feed(user=current_user._get_current_object(), event=u'修改班级“%s”的可选状态改为：不可选' % course.name, category=u'manage')
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
        add_feed(user=current_user._get_current_object(), event=u'更新班级：%s' % form.name.data, category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.course'))
    form.name.data = course.name
    form.course_type.data = unicode(course.type_id)
    form.show.data = course.show
    return render_template('manage/edit_course.html', form=form, course=course)


@manage.route('/course/delete/<int:id>')
@login_required
@permission_required(u'管理班级')
def delete_course(id):
    course = Course.query.get_or_404(id)
    if course.deleted:
        abort(404)
    course.safe_delete(modified_by=current_user._get_current_object())
    flash(u'已删除班级：%s' % course.name, category='success')
    add_feed(user=current_user._get_current_object(), event=u'删除班级：%s' % course.name, category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.course'))


@manage.route('/group', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理团报')
def group():
    form = NewGroupForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.organizer_email.data.lower(), created=True, activated=True, deleted=False).first()
        if user is None:
            flash(u'团报发起人邮箱不存在：%s' % form.organizer_email.data.lower(), category='error')
            return redirect(url_for('manage.group', page=request.args.get('page', 1, type=int)))
        if user.organized_groups.count():
            flash(u'%s已经发起过团报' % user.name_alias, category='error')
            return redirect(url_for('manage.group', page=request.args.get('page', 1, type=int)))
        if user.registered_groups.count():
            flash(u'%s已经参加过%s发起的团报' % (user.name_alias, user.registered_groups.first().organizer.name_alias), category='error')
            return redirect(url_for('manage.group', page=request.args.get('page', 1, type=int)))
        user.register_group(organizer=user)
        flash(u'%s已成功发起团报' % user.name_alias, category='success')
        add_feed(user=user, event=u'发起团报', category=u'group')
        add_feed(user=current_user._get_current_object(), event=u'记录%s发起团报' % user.name_alias, category=u'manage')
        return redirect(url_for('manage.group', page=request.args.get('page', 1, type=int)))
    query = GroupRegistration.query\
        .filter(GroupRegistration.organizer_id == GroupRegistration.member_id)\
        .order_by(GroupRegistration.timestamp.desc())
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    groups = pagination.items
    return render_template('manage/group.html',
        form=form,
        pagination=pagination,
        groups=groups
    )


@manage.route('/group/delete/<int:id>')
@login_required
@permission_required(u'管理团报')
def delete_group(id):
    user = User.query.get_or_404(id)
    if not user.created or user.deleted:
        abort(404)
    if user.organized_groups.count() == 0:
        flash(u'%s未曾发起过团报' % user.name_alias, category='error')
        return redirect(request.args.get('next') or url_for('manage.group'))
    for group_registration in user.organized_groups:
        group_registration.member.unregister_group(organizer=user)
    flash(u'已删除%s发起的团报' % user.name_alias, category='success')
    add_feed(user=current_user._get_current_object(), event=u'删除%s发起的团报' % user.name_alias, category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.group'))


@manage.route('/group/add/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理团报')
def add_group_member(id):
    organizer = User.query.get_or_404(id)
    if not organizer.created or organizer.deleted:
        abort(404)
    form = NewGroupMemberForm(organizer=organizer)
    if form.validate_on_submit():
        member = User.query.filter_by(email=form.member_email.data.lower(), created=True, activated=True, deleted=False).first()
        if member is None:
            flash(u'团报成员邮箱不存在：%s' % form.member_email.data.lower(), category='error')
            return redirect(url_for('manage.add_group_member', id=organizer.id, next=request.args.get('next')))
        if member.organized_groups.count():
            flash(u'%s已经发起过团报' % (member.name_alias), category='error')
            return redirect(url_for('manage.add_group_member', id=organizer.id, next=request.args.get('next')))
        if member.registered_groups.count():
            flash(u'%s已经参加过%s发起的团报' % (member.name_alias, member.registered_groups.first().organizer.name_alias), category='error')
            return redirect(url_for('manage.add_group_member', id=organizer.id, next=request.args.get('next')))
        if member.is_registering_group(organizer=organizer):
            flash(u'%s已经参加过%s发起的团报' % (member.name_alias, organizer.name_alias), category='error')
            return redirect(url_for('manage.add_group_member', id=organizer.id, next=request.args.get('next')))
        if organizer.organized_groups.count() > current_app.config['MAX_GROUP_SIZE']:
            flash(u'%s发起的团报人数已达到上限（%s人）' % (organizer.name_alias, current_app.config['MAX_GROUP_SIZE']), category='error')
            return redirect(url_for('manage.add_group_member', id=organizer.id, next=request.args.get('next')))
        member.register_group(organizer=organizer)
        flash(u'%s已成功加入%s发起的团报' % (member.name_alias, organizer.name_alias), category='success')
        add_feed(user=member, event=u'加入%s发起的团报' % organizer.name_alias, category=u'group')
        add_feed(user=organizer, event=u'%s加入您发起的团报' % member.name_alias, category=u'group')
        add_feed(user=current_user._get_current_object(), event=u'记录%s加入%s发起的团报' % (member.name_alias, organizer.name_alias), category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.group'))
    return render_template('manage/add_group_member.html', form=form, organizer=organizer)


@manage.route('/group/remove/<int:organizer_id>/<int:member_id>')
@login_required
@permission_required(u'管理团报')
def remove_group_member(organizer_id, member_id):
    organizer = User.query.get_or_404(organizer_id)
    if not organizer.created or organizer.deleted:
        abort(404)
    member = User.query.get_or_404(member_id)
    if not member.created or member.deleted:
        abort(404)
    if organizer.id == member.id:
        flash(u'需先删除%s所发起团报的其他成员' % organizer.name_alias, category='error')
        return redirect(request.args.get('next') or url_for('manage.group'))
    if not member.is_registering_group(organizer=organizer):
        flash(u'%s未曾参加过%s发起的团报' % (member.name_alias, organizer.name_alias), category='error')
        return redirect(request.args.get('next') or url_for('manage.group'))
    member.unregister_group(organizer=organizer)
    flash(u'已删除%s发起的团报成员：%s' % (organizer.name_alias, member.name_alias), category='success')
    add_feed(user=current_user._get_current_object(), event=u'删除%s发起的团报成员：%s' % (organizer.name_alias, member.name_alias), category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.group'))


@manage.route('/tag', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理用户标签')
def tag():
    form = NewTagForm()
    if form.validate_on_submit():
        if Tag.query.filter_by(name=form.name.data).first() is not None:
            flash(u'“%s”标签已存在' % form.name.data, category='error')
            return redirect(url_for('manage.tag', page=request.args.get('page', 1, type=int)))
        tag = Tag(name=form.name.data, color_id=int(form.color.data))
        db.session.add(tag)
        flash(u'已添加用户标签：%s' % form.name.data, category='success')
        add_feed(user=current_user._get_current_object(), event=u'添加用户标签：%s' % form.name.data, category=u'manage')
        return redirect(url_for('manage.tag', page=request.args.get('page', 1, type=int)))
    query = Tag.query
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    tags = pagination.items
    return render_template('manage/tag.html',
        form=form,
        pagination=pagination,
        tags=tags
    )


@manage.route('/tag/<int:id>')
@login_required
@permission_required(u'管理')
def tag_user(id):
    tag = Tag.query.get_or_404(id)
    if tag.valid_tagged_users.count() == 0:
        return redirect(url_for('manage.tag'))
    query = User.query\
        .join(UserTag, UserTag.user_id == User.id)\
        .filter(UserTag.tag_id == tag.id)\
        .filter(User.created == True)\
        .filter(User.deleted == False)
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    users = pagination.items
    return render_template('manage/tag_user.html',
        tag=tag,
        pagination=pagination,
        users=users
    )


@manage.route('/tag/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理用户标签')
def edit_tag(id):
    tag = Tag.query.get_or_404(id)
    form = EditTagForm(tag=tag)
    if form.validate_on_submit():
        if current_user.is_developer or not tag.pinned:
            tag.name = form.name.data
        tag.color_id = int(form.color.data)
        db.session.add(tag)
        flash(u'已更新标签：%s' % form.name.data, category='success')
        add_feed(user=current_user._get_current_object(), event=u'更新用户标签：%s' % form.name.data, category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.tag'))
    form.name.data = tag.name
    form.color.data = unicode(tag.color_id)
    return render_template('manage/edit_tag.html', form=form, tag=tag)


@manage.route('/tag/delete/<int:id>')
@login_required
@permission_required(u'管理用户标签')
def delete_tag(id):
    tag = Tag.query.get_or_404(id)
    if (tag.pinned and not current_user.is_developer) or tag.valid_tagged_users.count():
        abort(403)
    db.session.delete(tag)
    flash(u'已删除用户标签：%s' % tag.name, category='success')
    add_feed(user=current_user._get_current_object(), event=u'删除用户标签：%s' % tag.name, category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.tag'))


@manage.route('/ipad', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理')
def ipad():
    form = NewiPadForm()
    if form.submit.data and form.validate_on_submit() and current_user.can(u'管理iPad设备'):
        serial = form.serial.data.upper()
        room_id = int(form.room.data)
        if room_id == 0:
            room_id = None
        ipad = iPad.query.filter_by(serial=serial).first()
        if ipad:
            flash(u'序列号为%s的iPad已存在' % serial, category='error')
            return redirect(url_for('manage.ipad', page=request.args.get('page', 1, type=int)))
        ipad = iPad(
            serial=serial,
            alias=form.alias.data,
            capacity_id=int(form.capacity.data),
            room_id=room_id,
            state_id=int(form.state.data),
            video_playback=timedelta(hours=form.video_playback.data),
            modified_by_id=current_user.id
        )
        db.session.add(ipad)
        db.session.commit()
        for lesson_id in form.vb_lessons.data + form.y_gre_lessons.data:
            ipad.add_lesson(lesson=Lesson.query.get(int(lesson_id)))
        flash(u'成功添加序列号为%s的iPad' % serial, category='success')
        add_feed(user=current_user._get_current_object(), event=u'添加序列号为%s的iPad' % serial, category=u'manage')
        return redirect(url_for('manage.ipad', page=request.args.get('page', 1, type=int)))
    filter_form = FilteriPadForm(prefix='filter')
    if filter_form.submit.data and filter_form.validate_on_submit():
        lesson_ids = filter_form.vb_lessons.data + filter_form.y_gre_lessons.data
        return redirect(url_for('manage.filter_ipad_results', keyword=u'_'.join(lesson_ids)))
    show_ipad_all = True
    show_ipad_maintain = False
    show_ipad_charge = False
    show_ipad_1103 = False
    show_ipad_1707 = False
    show_ipad_others = False
    show_ipad_filter = False
    if current_user.is_authenticated:
        show_ipad_all = bool(request.cookies.get('show_ipad_all', '1'))
        show_ipad_maintain = bool(request.cookies.get('show_ipad_maintain', ''))
        show_ipad_charge = bool(request.cookies.get('show_ipad_charge', ''))
        show_ipad_1103 = bool(request.cookies.get('show_ipad_1103', ''))
        show_ipad_1707 = bool(request.cookies.get('show_ipad_1707', ''))
        show_ipad_others = bool(request.cookies.get('show_ipad_others', ''))
        show_ipad_filter = bool(request.cookies.get('show_ipad_filter', ''))
    if show_ipad_all:
        query = iPad.query\
            .filter_by(deleted=False)
    all_num = iPad.query\
        .filter(iPad.deleted == False)\
        .count()
    if show_ipad_maintain:
        query = iPad.query\
            .join(iPadState, iPadState.id == iPad.state_id)\
            .filter(iPadState.name == u'维护')\
            .filter(iPad.deleted == False)
    maintain_num = iPad.query\
        .join(iPadState, iPadState.id == iPad.state_id)\
        .filter(iPadState.name == u'维护')\
        .filter(iPad.deleted == False)\
        .count()
    if show_ipad_charge:
        query = iPad.query\
            .join(iPadState, iPadState.id == iPad.state_id)\
            .filter(iPadState.name == u'充电')\
            .filter(iPad.deleted == False)
    charge_num = iPad.query\
        .join(iPadState, iPadState.id == iPad.state_id)\
        .filter(iPadState.name == u'充电')\
        .filter(iPad.deleted == False)\
        .count()
    if show_ipad_1103:
        query = iPad.query\
            .join(Room, Room.id == iPad.room_id)\
            .filter(Room.name == u'1103')\
            .filter(iPad.deleted == False)
    room_1103_num = iPad.query\
        .join(Room, Room.id == iPad.room_id)\
        .filter(Room.name == u'1103')\
        .filter(iPad.deleted == False)\
        .count()
    if show_ipad_1707:
        query = iPad.query\
            .join(Room, Room.id == iPad.room_id)\
            .filter(Room.name == u'1707')\
            .filter(iPad.deleted == False)
    room_1707_num = iPad.query\
        .join(Room, Room.id == iPad.room_id)\
        .filter(Room.name == u'1707')\
        .filter(iPad.deleted == False)\
        .count()
    if show_ipad_others:
        query = iPad.query\
            .filter_by(room_id=None, deleted=False)
    others_num = iPad.query\
        .filter_by(room_id=None, deleted=False)\
        .count()
    if show_ipad_filter:
        ipads = []
        vb_lesson_ids = []
        y_gre_lesson_ids = []
        keyword = request.args.get('keyword')
        if keyword:
            vb_lesson_ids = [unicode(lesson_id) for lesson_id in keyword.split('_') if Lesson.query.get(lesson_id) is not None and Lesson.query.get(int(lesson_id)).type.name == u'VB']
            y_gre_lesson_ids = [unicode(lesson_id) for lesson_id in keyword.split('_') if Lesson.query.get(lesson_id) is not None and Lesson.query.get(int(lesson_id)).type.name == u'Y-GRE']
            filter_form.vb_lessons.data = vb_lesson_ids
            filter_form.y_gre_lessons.data = y_gre_lesson_ids
        lesson_ids = vb_lesson_ids + y_gre_lesson_ids
        if len(lesson_ids):
            ipad_ids = reduce(lambda x, y: x & y, [set([query.ipad_id for query in iPadContent.query.filter_by(lesson_id=int(lesson_id)).all()]) for lesson_id in lesson_ids])
            ipads = [ipad for ipad in [iPad.query.get(ipad_id) for ipad_id in ipad_ids] if ipad is not None and not ipad.deleted]
        filter_results_num = len(ipads)
        pagination = False
    if not show_ipad_filter:
        filter_results_num = 0
        page = request.args.get('page', 1, type=int)
        pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
        ipads = pagination.items
    return render_template('manage/ipad.html',
        form=form,
        filter_form=filter_form,
        show_ipad_all=show_ipad_all,
        all_num=all_num,
        show_ipad_maintain=show_ipad_maintain,
        maintain_num=maintain_num,
        show_ipad_charge=show_ipad_charge,
        charge_num=charge_num,
        show_ipad_1103=show_ipad_1103,
        room_1103_num=room_1103_num,
        show_ipad_1707=show_ipad_1707,
        room_1707_num=room_1707_num,
        show_ipad_others=show_ipad_others,
        others_num=others_num,
        show_ipad_filter=show_ipad_filter,
        filter_results_num=filter_results_num,
        pagination=pagination,
        ipads=ipads
    )


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
    resp.set_cookie('show_ipad_filter', '', max_age=30*24*60*60)
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
    resp.set_cookie('show_ipad_filter', '', max_age=30*24*60*60)
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
    resp.set_cookie('show_ipad_filter', '', max_age=30*24*60*60)
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
    resp.set_cookie('show_ipad_filter', '', max_age=30*24*60*60)
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
    resp.set_cookie('show_ipad_filter', '', max_age=30*24*60*60)
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
    resp.set_cookie('show_ipad_filter', '', max_age=30*24*60*60)
    return resp


@manage.route('/ipad/filter/results')
@login_required
@permission_required(u'管理')
def filter_ipad_results():
    resp = make_response(redirect(url_for('manage.ipad', keyword=request.args.get('keyword'), next=request.args.get('next'))))
    resp.set_cookie('show_ipad_all', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_maintain', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_charge', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_1103', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_1707', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_others', '', max_age=30*24*60*60)
    resp.set_cookie('show_ipad_filter', '1', max_age=30*24*60*60)
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
    add_feed(user=current_user._get_current_object(), event=u'修改iPad“%s”的状态为：待机' % ipad.alias, category=u'manage')
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
    add_feed(user=current_user._get_current_object(), event=u'修改iPad“%s”的状态为：候补' % ipad.alias, category=u'manage')
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
    send_emails([user.email for user in User.users_can(u'管理iPad设备').all()], u'编号为“%s”的iPad处于维护状态' % ipad.alias, 'manage/mail/maintain_ipad',
        ipad=ipad,
        time=datetime.utcnow(),
        manager=current_user._get_current_object()
    )
    flash(u'修改iPad“%s”的状态为：维护' % ipad.alias, category='success')
    add_feed(user=current_user._get_current_object(), event=u'修改iPad“%s”的状态为：维护' % ipad.alias, category=u'manage')
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
    add_feed(user=current_user._get_current_object(), event=u'修改iPad“%s”的状态为：充电' % ipad.alias, category=u'manage')
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
    add_feed(user=current_user._get_current_object(), event=u'修改iPad“%s”的状态为：退役' % ipad.alias, category=u'manage')
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
            ipad.remove_lesson(lesson=ipad_content.lesson)
        for lesson_id in form.vb_lessons.data + form.y_gre_lessons.data:
            ipad.add_lesson(lesson=Lesson.query.get(int(lesson_id)))
        flash(u'iPad信息已更新', category='success')
        add_feed(user=current_user._get_current_object(), event=u'更新iPad“%s”的信息' % ipad.alias, category=u'manage')
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


@manage.route('/ipad/delete/<int:id>')
@login_required
@permission_required(u'管理iPad设备')
def delete_ipad(id):
    ipad = iPad.query.get_or_404(id)
    if ipad.deleted:
        abort(404)
    ipad.safe_delete(modified_by=current_user._get_current_object())
    flash(u'已删除序列号为“%s”的iPad' % ipad.serial, category='success')
    add_feed(user=current_user._get_current_object(), event=u'删除序列号为“%s”的iPad' % ipad.serial, category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.ipad'))


@manage.route('/ipad/contents')
@login_required
@permission_required(u'管理')
def ipad_contents():
    ipads = iPad.query\
        .filter_by(deleted=False)\
        .order_by(iPad.alias.asc())
    lessons = Lesson.query\
        .filter(Lesson.include_video == True)\
        .filter(Lesson.advanced == False)\
        .order_by(Lesson.id.asc())
    return render_template('manage/ipad_contents.html',
        ipads=ipads,
        lessons=lessons
    )


@manage.route('/ipad/contents/data')
@login_required
@permission_required(u'管理')
def ipad_contents_data():
    ipads = iPad.query\
        .filter_by(deleted=False)\
        .order_by(iPad.alias.asc())
    ipad_contents = iPadContent.query\
        .join(iPad, iPad.id == iPadContent.ipad_id)\
        .join(Lesson, Lesson.id == iPadContent.lesson_id)\
        .filter(iPad.deleted == False)\
        .filter(Lesson.include_video == True)\
        .filter(Lesson.advanced == False)\
        .order_by(
            iPadContent.ipad_id.asc(),
            iPadContent.lesson_id.asc()
        )\
        .all()
    return jsonify({
        'ipads': [ipad.to_json() for ipad in ipads],
        'ipad_contents': [ipad_content.to_json() for ipad_content in ipad_contents],
    })


@manage.route('/study-plan/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理研修计划')
def edit_study_plan(id):
    user = User.query.get_or_404(id)
    if not user.created or user.deleted:
        abort(404)
    # retrieve aim scores
    gre_aim_score_label = ScoreLabel.query.filter_by(name=u'目标', category=u'GRE').first()
    gre_aim_score = user.gre_test_scores.filter_by(label_id=gre_aim_score_label.id).first()
    toefl_aim_score_label = ScoreLabel.query.filter_by(name=u'目标', category=u'TOEFL').first()
    toefl_aim_score = user.toefl_test_scores.filter_by(label_id=toefl_aim_score_label.id).first()
    # retrieve VB plan
    vb_intro = Lesson.query.filter_by(name=u'VB总论').first()
    vb_intro_plan = user.study_plans.filter_by(lesson_id=vb_intro.id).first()
    vb_1 = Lesson.query.filter_by(name=u'L1').first()
    vb_1_plan = user.study_plans.filter_by(lesson_id=vb_1.id).first()
    vb_2 = Lesson.query.filter_by(name=u'L2').first()
    vb_2_plan = user.study_plans.filter_by(lesson_id=vb_2.id).first()
    vb_3 = Lesson.query.filter_by(name=u'L3').first()
    vb_3_plan = user.study_plans.filter_by(lesson_id=vb_3.id).first()
    vb_4 = Lesson.query.filter_by(name=u'L4').first()
    vb_4_plan = user.study_plans.filter_by(lesson_id=vb_4.id).first()
    vb_5 = Lesson.query.filter_by(name=u'L5').first()
    vb_5_plan = user.study_plans.filter_by(lesson_id=vb_5.id).first()
    vb_6 = Lesson.query.filter_by(name=u'L6').first()
    vb_6_plan = user.study_plans.filter_by(lesson_id=vb_6.id).first()
    vb_7 = Lesson.query.filter_by(name=u'L7').first()
    vb_7_plan = user.study_plans.filter_by(lesson_id=vb_7.id).first()
    vb_8 = Lesson.query.filter_by(name=u'L8').first()
    vb_8_plan = user.study_plans.filter_by(lesson_id=vb_8.id).first()
    vb_9 = Lesson.query.filter_by(name=u'L9').first()
    vb_9_plan = user.study_plans.filter_by(lesson_id=vb_9.id).first()
    # retrieve GRE plan
    y_gre_intro = Lesson.query.filter_by(name=u'Y-GRE总论').first()
    y_gre_intro_plan = user.study_plans.filter_by(lesson_id=y_gre_intro.id).first()
    y_gre_1 = Lesson.query.filter_by(name=u'1st').first()
    y_gre_1_plan = user.study_plans.filter_by(lesson_id=y_gre_1.id).first()
    y_gre_2 = Lesson.query.filter_by(name=u'2nd').first()
    y_gre_2_plan = user.study_plans.filter_by(lesson_id=y_gre_2.id).first()
    y_gre_3 = Lesson.query.filter_by(name=u'3rd').first()
    y_gre_3_plan = user.study_plans.filter_by(lesson_id=y_gre_3.id).first()
    y_gre_4 = Lesson.query.filter_by(name=u'4th').first()
    y_gre_4_plan = user.study_plans.filter_by(lesson_id=y_gre_4.id).first()
    y_gre_5 = Lesson.query.filter_by(name=u'5th').first()
    y_gre_5_plan = user.study_plans.filter_by(lesson_id=y_gre_5.id).first()
    y_gre_6 = Lesson.query.filter_by(name=u'6th').first()
    y_gre_6_plan = user.study_plans.filter_by(lesson_id=y_gre_6.id).first()
    y_gre_7 = Lesson.query.filter_by(name=u'7th').first()
    y_gre_7_plan = user.study_plans.filter_by(lesson_id=y_gre_7.id).first()
    y_gre_8 = Lesson.query.filter_by(name=u'8th').first()
    y_gre_8_plan = user.study_plans.filter_by(lesson_id=y_gre_8.id).first()
    y_gre_9 = Lesson.query.filter_by(name=u'9th').first()
    y_gre_9_plan = user.study_plans.filter_by(lesson_id=y_gre_9.id).first()
    y_gre_prep = Lesson.query.filter_by(name=u'Y-GRE临考').first()
    y_gre_prep_plan = user.study_plans.filter_by(lesson_id=y_gre_prep.id).first()
    # retrieve GRE test dates
    gre_0_score_label = ScoreLabel.query.filter_by(name=u'G0', category=u'GRE').first()
    gre_0_score = user.gre_test_scores.filter_by(label_id=gre_0_score_label.id).first()
    gre_1_score_label = ScoreLabel.query.filter_by(name=u'G1', category=u'GRE').first()
    gre_1_score = user.gre_test_scores.filter_by(label_id=gre_1_score_label.id).first()
    gre_2_score_label = ScoreLabel.query.filter_by(name=u'G2', category=u'GRE').first()
    gre_2_score = user.gre_test_scores.filter_by(label_id=gre_2_score_label.id).first()
    gre_3_score_label = ScoreLabel.query.filter_by(name=u'G3', category=u'GRE').first()
    gre_3_score = user.gre_test_scores.filter_by(label_id=gre_3_score_label.id).first()
    form = EditStudyPlanForm()
    if form.validate_on_submit():
        # update aim scores
        if gre_aim_score is None:
            gre_aim_score = GRETestScore(
                user_id=user.id,
                label_id=ScoreLabel.query.filter_by(name=u'目标', category=u'GRE').first().id,
                v_score=form.gre_aim_v.data,
                q_score=form.gre_aim_q.data,
                aw_score_id=int(form.gre_aim_aw.data),
                modified_by_id=current_user.id
            )
        else:
            gre_aim_score.v_score = form.gre_aim_v.data
            gre_aim_score.q_score = form.gre_aim_q.data
            gre_aim_score.aw_score_id = int(form.gre_aim_aw.data)
            gre_aim_score.modified_at = datetime.utcnow()
            gre_aim_score.modified_by_id = current_user.id
        db.session.add(gre_aim_score)
        db.session.commit()
        if toefl_aim_score is None:
            toefl_aim_score = TOEFLTestScore(
                user_id=user.id,
                label_id=ScoreLabel.query.filter_by(name=u'目标', category=u'TOEFL').first().id,
                total_score=form.toefl_aim_total.data,
                reading_score=form.toefl_aim_reading.data,
                listening_score=form.toefl_aim_listening.data,
                speaking_score=form.toefl_aim_speaking.data,
                writing_score=form.toefl_aim_writing.data,
                modified_by_id=current_user.id
            )
        else:
            toefl_aim_score.total_score = form.toefl_aim_total.data
            toefl_aim_score.reading_score = form.toefl_aim_reading.data
            toefl_aim_score.listening_score = form.toefl_aim_listening.data
            toefl_aim_score.speaking_score = form.toefl_aim_speaking.data
            toefl_aim_score.writing_score = form.toefl_aim_writing.data
            toefl_aim_score.modified_at = datetime.utcnow()
            toefl_aim_score.modified_by_id = current_user.id
        db.session.add(toefl_aim_score)
        db.session.commit()
        # update time parameters
        user.deadline = form.deadline.data
        user.speed = form.speed.data
        db.session.add(user)
        db.session.commit()
        # update VB plan: intro
        vb_intro_start_date = None
        if form.vb_intro_start_date.data:
            vb_intro_start_date = form.vb_intro_start_date.data
        vb_intro_end_date = None
        if form.vb_intro_end_date.data:
            vb_intro_end_date = form.vb_intro_end_date.data
        if vb_intro_plan is None:
            vb_intro_plan = StudyPlan(
                user_id=user.id,
                lesson_id=vb_intro.id,
                start_date=vb_intro_start_date,
                end_date=vb_intro_end_date,
                remark=form.vb_intro_remark.data
            )
        else:
            vb_intro_plan.start_date = vb_intro_start_date
            vb_intro_plan.end_date = vb_intro_end_date
            vb_intro_plan.remark = form.vb_intro_remark.data
        db.session.add(vb_intro_plan)
        db.session.commit()
        for item in vb_intro_plan.notate_bene:
            vb_intro_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.vb_intro_notate_bene.data:
            vb_intro_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update VB plan: 1
        vb_1_start_date = None
        if form.vb_1_start_date.data:
            vb_1_start_date = form.vb_1_start_date.data
        vb_1_end_date = None
        if form.vb_1_end_date.data:
            vb_1_end_date = form.vb_1_end_date.data
        if vb_1_plan is None:
            vb_1_plan = StudyPlan(
                user_id=user.id,
                lesson_id=vb_1.id,
                start_date=vb_1_start_date,
                end_date=vb_1_end_date,
                remark=form.vb_1_remark.data
            )
        else:
            vb_1_plan.start_date = vb_1_start_date
            vb_1_plan.end_date = vb_1_end_date
            vb_1_plan.remark = form.vb_1_remark.data
        db.session.add(vb_1_plan)
        db.session.commit()
        for item in vb_1_plan.notate_bene:
            vb_1_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.vb_1_notate_bene.data:
            vb_1_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update VB plan: 2
        vb_2_start_date = None
        if form.vb_2_start_date.data:
            vb_2_start_date = form.vb_2_start_date.data
        vb_2_end_date = None
        if form.vb_2_end_date.data:
            vb_2_end_date = form.vb_2_end_date.data
        if vb_2_plan is None:
            vb_2_plan = StudyPlan(
                user_id=user.id,
                lesson_id=vb_2.id,
                start_date=vb_2_start_date,
                end_date=vb_2_end_date,
                remark=form.vb_2_remark.data
            )
        else:
            vb_2_plan.start_date = vb_2_start_date
            vb_2_plan.end_date = vb_2_end_date
            vb_2_plan.remark = form.vb_2_remark.data
        db.session.add(vb_2_plan)
        db.session.commit()
        for item in vb_2_plan.notate_bene:
            vb_2_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.vb_2_notate_bene.data:
            vb_2_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update VB plan: 3
        vb_3_start_date = None
        if form.vb_3_start_date.data:
            vb_3_start_date = form.vb_3_start_date.data
        vb_3_end_date = None
        if form.vb_3_end_date.data:
            vb_3_end_date = form.vb_3_end_date.data
        if vb_3_plan is None:
            vb_3_plan = StudyPlan(
                user_id=user.id,
                lesson_id=vb_3.id,
                start_date=vb_3_start_date,
                end_date=vb_3_end_date,
                remark=form.vb_3_remark.data
            )
        else:
            vb_3_plan.start_date = vb_3_start_date
            vb_3_plan.end_date = vb_3_end_date
            vb_3_plan.remark = form.vb_3_remark.data
        db.session.add(vb_3_plan)
        db.session.commit()
        for item in vb_3_plan.notate_bene:
            vb_3_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.vb_3_notate_bene.data:
            vb_3_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update VB plan: 4
        vb_4_start_date = None
        if form.vb_4_start_date.data:
            vb_4_start_date = form.vb_4_start_date.data
        vb_4_end_date = None
        if form.vb_4_end_date.data:
            vb_4_end_date = form.vb_4_end_date.data
        if vb_4_plan is None:
            vb_4_plan = StudyPlan(
                user_id=user.id,
                lesson_id=vb_4.id,
                start_date=vb_4_start_date,
                end_date=vb_4_end_date,
                remark=form.vb_4_remark.data
            )
        else:
            vb_4_plan.start_date = vb_4_start_date
            vb_4_plan.end_date = vb_4_end_date
            vb_4_plan.remark = form.vb_4_remark.data
        db.session.add(vb_4_plan)
        db.session.commit()
        for item in vb_4_plan.notate_bene:
            vb_4_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.vb_4_notate_bene.data:
            vb_4_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update VB plan: 5
        vb_5_start_date = None
        if form.vb_5_start_date.data:
            vb_5_start_date = form.vb_5_start_date.data
        vb_5_end_date = None
        if form.vb_5_end_date.data:
            vb_5_end_date = form.vb_5_end_date.data
        if vb_5_plan is None:
            vb_5_plan = StudyPlan(
                user_id=user.id,
                lesson_id=vb_5.id,
                start_date=vb_5_start_date,
                end_date=vb_5_end_date,
                remark=form.vb_5_remark.data
            )
        else:
            vb_5_plan.start_date = vb_5_start_date
            vb_5_plan.end_date = vb_5_end_date
            vb_5_plan.remark = form.vb_5_remark.data
        db.session.add(vb_5_plan)
        db.session.commit()
        for item in vb_5_plan.notate_bene:
            vb_5_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.vb_5_notate_bene.data:
            vb_5_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update VB plan: 6
        vb_6_start_date = None
        if form.vb_6_start_date.data:
            vb_6_start_date = form.vb_6_start_date.data
        vb_6_end_date = None
        if form.vb_6_end_date.data:
            vb_6_end_date = form.vb_6_end_date.data
        if vb_6_plan is None:
            vb_6_plan = StudyPlan(
                user_id=user.id,
                lesson_id=vb_6.id,
                start_date=vb_6_start_date,
                end_date=vb_6_end_date,
                remark=form.vb_6_remark.data
            )
        else:
            vb_6_plan.start_date = vb_6_start_date
            vb_6_plan.end_date = vb_6_end_date
            vb_6_plan.remark = form.vb_6_remark.data
        db.session.add(vb_6_plan)
        db.session.commit()
        for item in vb_6_plan.notate_bene:
            vb_6_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.vb_6_notate_bene.data:
            vb_6_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update VB plan: 7
        vb_7_start_date = None
        if form.vb_7_start_date.data:
            vb_7_start_date = form.vb_7_start_date.data
        vb_7_end_date = None
        if form.vb_7_end_date.data:
            vb_7_end_date = form.vb_7_end_date.data
        if vb_7_plan is None:
            vb_7_plan = StudyPlan(
                user_id=user.id,
                lesson_id=vb_7.id,
                start_date=vb_7_start_date,
                end_date=vb_7_end_date,
                remark=form.vb_7_remark.data
            )
        else:
            vb_7_plan.start_date = vb_7_start_date
            vb_7_plan.end_date = vb_7_end_date
            vb_7_plan.remark = form.vb_7_remark.data
        db.session.add(vb_7_plan)
        db.session.commit()
        for item in vb_7_plan.notate_bene:
            vb_7_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.vb_7_notate_bene.data:
            vb_7_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update VB plan: 8
        vb_8_start_date = None
        if form.vb_8_start_date.data:
            vb_8_start_date = form.vb_8_start_date.data
        vb_8_end_date = None
        if form.vb_8_end_date.data:
            vb_8_end_date = form.vb_8_end_date.data
        if vb_8_plan is None:
            vb_8_plan = StudyPlan(
                user_id=user.id,
                lesson_id=vb_8.id,
                start_date=vb_8_start_date,
                end_date=vb_8_end_date,
                remark=form.vb_8_remark.data
            )
        else:
            vb_8_plan.start_date = vb_8_start_date
            vb_8_plan.end_date = vb_8_end_date
            vb_8_plan.remark = form.vb_8_remark.data
        db.session.add(vb_8_plan)
        db.session.commit()
        for item in vb_8_plan.notate_bene:
            vb_8_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.vb_8_notate_bene.data:
            vb_8_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update VB plan: 9
        vb_9_start_date = None
        if form.vb_9_start_date.data:
            vb_9_start_date = form.vb_9_start_date.data
        vb_9_end_date = None
        if form.vb_9_end_date.data:
            vb_9_end_date = form.vb_9_end_date.data
        if vb_9_plan is None:
            vb_9_plan = StudyPlan(
                user_id=user.id,
                lesson_id=vb_9.id,
                start_date=vb_9_start_date,
                end_date=vb_9_end_date,
                remark=form.vb_9_remark.data
            )
        else:
            vb_9_plan.start_date = vb_9_start_date
            vb_9_plan.end_date = vb_9_end_date
            vb_9_plan.remark = form.vb_9_remark.data
        db.session.add(vb_9_plan)
        db.session.commit()
        for item in vb_9_plan.notate_bene:
            vb_9_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.vb_9_notate_bene.data:
            vb_9_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update Y-GRE plan: intro
        y_gre_intro_start_date = None
        if form.y_gre_intro_start_date.data:
            y_gre_intro_start_date = form.y_gre_intro_start_date.data
        y_gre_intro_end_date = None
        if form.y_gre_intro_end_date.data:
            y_gre_intro_end_date = form.y_gre_intro_end_date.data
        if y_gre_intro_plan is None:
            y_gre_intro_plan = StudyPlan(
                user_id=user.id,
                lesson_id=y_gre_intro.id,
                start_date=y_gre_intro_start_date,
                end_date=y_gre_intro_end_date,
                remark=form.y_gre_intro_remark.data
            )
        else:
            y_gre_intro_plan.start_date = y_gre_intro_start_date
            y_gre_intro_plan.end_date = y_gre_intro_end_date
            y_gre_intro_plan.remark = form.y_gre_intro_remark.data
        db.session.add(y_gre_intro_plan)
        db.session.commit()
        for item in y_gre_intro_plan.notate_bene:
            y_gre_intro_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.y_gre_intro_notate_bene.data:
            y_gre_intro_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update Y-GRE plan: 1
        y_gre_1_start_date = None
        if form.y_gre_1_start_date.data:
            y_gre_1_start_date = form.y_gre_1_start_date.data
        y_gre_1_end_date = None
        if form.y_gre_1_end_date.data:
            y_gre_1_end_date = form.y_gre_1_end_date.data
        if y_gre_1_plan is None:
            y_gre_1_plan = StudyPlan(
                user_id=user.id,
                lesson_id=y_gre_1.id,
                start_date=y_gre_1_start_date,
                end_date=y_gre_1_end_date,
                remark=form.y_gre_1_remark.data
            )
        else:
            y_gre_1_plan.start_date = y_gre_1_start_date
            y_gre_1_plan.end_date = y_gre_1_end_date
            y_gre_1_plan.remark = form.y_gre_1_remark.data
        db.session.add(y_gre_1_plan)
        db.session.commit()
        for item in y_gre_1_plan.notate_bene:
            y_gre_1_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.y_gre_1_notate_bene.data:
            y_gre_1_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update Y-GRE plan: 2
        y_gre_2_start_date = None
        if form.y_gre_2_start_date.data:
            y_gre_2_start_date = form.y_gre_2_start_date.data
        y_gre_2_end_date = None
        if form.y_gre_2_end_date.data:
            y_gre_2_end_date = form.y_gre_2_end_date.data
        if y_gre_2_plan is None:
            y_gre_2_plan = StudyPlan(
                user_id=user.id,
                lesson_id=y_gre_2.id,
                start_date=y_gre_2_start_date,
                end_date=y_gre_2_end_date,
                remark=form.y_gre_2_remark.data
            )
        else:
            y_gre_2_plan.start_date = y_gre_2_start_date
            y_gre_2_plan.end_date = y_gre_2_end_date
            y_gre_2_plan.remark = form.y_gre_2_remark.data
        db.session.add(y_gre_2_plan)
        db.session.commit()
        for item in y_gre_2_plan.notate_bene:
            y_gre_2_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.y_gre_2_notate_bene.data:
            y_gre_2_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update Y-GRE plan: 3
        y_gre_3_start_date = None
        if form.y_gre_3_start_date.data:
            y_gre_3_start_date = form.y_gre_3_start_date.data
        y_gre_3_end_date = None
        if form.y_gre_3_end_date.data:
            y_gre_3_end_date = form.y_gre_3_end_date.data
        if y_gre_3_plan is None:
            y_gre_3_plan = StudyPlan(
                user_id=user.id,
                lesson_id=y_gre_3.id,
                start_date=y_gre_3_start_date,
                end_date=y_gre_3_end_date,
                remark=form.y_gre_3_remark.data
            )
        else:
            y_gre_3_plan.start_date = y_gre_3_start_date
            y_gre_3_plan.end_date = y_gre_3_end_date
            y_gre_3_plan.remark = form.y_gre_3_remark.data
        db.session.add(y_gre_3_plan)
        db.session.commit()
        for item in y_gre_3_plan.notate_bene:
            y_gre_3_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.y_gre_3_notate_bene.data:
            y_gre_3_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update Y-GRE plan: 4
        y_gre_4_start_date = None
        if form.y_gre_4_start_date.data:
            y_gre_4_start_date = form.y_gre_4_start_date.data
        y_gre_4_end_date = None
        if form.y_gre_4_end_date.data:
            y_gre_4_end_date = form.y_gre_4_end_date.data
        if y_gre_4_plan is None:
            y_gre_4_plan = StudyPlan(
                user_id=user.id,
                lesson_id=y_gre_4.id,
                start_date=y_gre_4_start_date,
                end_date=y_gre_4_end_date,
                remark=form.y_gre_4_remark.data
            )
        else:
            y_gre_4_plan.start_date = y_gre_4_start_date
            y_gre_4_plan.end_date = y_gre_4_end_date
            y_gre_4_plan.remark = form.y_gre_4_remark.data
        db.session.add(y_gre_4_plan)
        db.session.commit()
        for item in y_gre_4_plan.notate_bene:
            y_gre_4_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.y_gre_4_notate_bene.data:
            y_gre_4_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update Y-GRE plan: 5
        y_gre_5_start_date = None
        if form.y_gre_5_start_date.data:
            y_gre_5_start_date = form.y_gre_5_start_date.data
        y_gre_5_end_date = None
        if form.y_gre_5_end_date.data:
            y_gre_5_end_date = form.y_gre_5_end_date.data
        if y_gre_5_plan is None:
            y_gre_5_plan = StudyPlan(
                user_id=user.id,
                lesson_id=y_gre_5.id,
                start_date=y_gre_5_start_date,
                end_date=y_gre_5_end_date,
                remark=form.y_gre_5_remark.data
            )
        else:
            y_gre_5_plan.start_date = y_gre_5_start_date
            y_gre_5_plan.end_date = y_gre_5_end_date
            y_gre_5_plan.remark = form.y_gre_5_remark.data
        db.session.add(y_gre_5_plan)
        db.session.commit()
        for item in y_gre_5_plan.notate_bene:
            y_gre_5_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.y_gre_5_notate_bene.data:
            y_gre_5_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update Y-GRE plan: 6
        y_gre_6_start_date = None
        if form.y_gre_6_start_date.data:
            y_gre_6_start_date = form.y_gre_6_start_date.data
        y_gre_6_end_date = None
        if form.y_gre_6_end_date.data:
            y_gre_6_end_date = form.y_gre_6_end_date.data
        if y_gre_6_plan is None:
            y_gre_6_plan = StudyPlan(
                user_id=user.id,
                lesson_id=y_gre_6.id,
                start_date=y_gre_6_start_date,
                end_date=y_gre_6_end_date,
                remark=form.y_gre_6_remark.data
            )
        else:
            y_gre_6_plan.start_date = y_gre_6_start_date
            y_gre_6_plan.end_date = y_gre_6_end_date
            y_gre_6_plan.remark = form.y_gre_6_remark.data
        db.session.add(y_gre_6_plan)
        db.session.commit()
        for item in y_gre_6_plan.notate_bene:
            y_gre_6_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.y_gre_6_notate_bene.data:
            y_gre_6_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update Y-GRE plan: 7
        y_gre_7_start_date = None
        if form.y_gre_7_start_date.data:
            y_gre_7_start_date = form.y_gre_7_start_date.data
        y_gre_7_end_date = None
        if form.y_gre_7_end_date.data:
            y_gre_7_end_date = form.y_gre_7_end_date.data
        if y_gre_7_plan is None:
            y_gre_7_plan = StudyPlan(
                user_id=user.id,
                lesson_id=y_gre_7.id,
                start_date=y_gre_7_start_date,
                end_date=y_gre_7_end_date,
                remark=form.y_gre_7_remark.data
            )
        else:
            y_gre_7_plan.start_date = y_gre_7_start_date
            y_gre_7_plan.end_date = y_gre_7_end_date
            y_gre_7_plan.remark = form.y_gre_7_remark.data
        db.session.add(y_gre_7_plan)
        db.session.commit()
        for item in y_gre_7_plan.notate_bene:
            y_gre_7_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.y_gre_7_notate_bene.data:
            y_gre_7_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update Y-GRE plan: 8
        y_gre_8_start_date = None
        if form.y_gre_8_start_date.data:
            y_gre_8_start_date = form.y_gre_8_start_date.data
        y_gre_8_end_date = None
        if form.y_gre_8_end_date.data:
            y_gre_8_end_date = form.y_gre_8_end_date.data
        if y_gre_8_plan is None:
            y_gre_8_plan = StudyPlan(
                user_id=user.id,
                lesson_id=y_gre_8.id,
                start_date=y_gre_8_start_date,
                end_date=y_gre_8_end_date,
                remark=form.y_gre_8_remark.data
            )
        else:
            y_gre_8_plan.start_date = y_gre_8_start_date
            y_gre_8_plan.end_date = y_gre_8_end_date
            y_gre_8_plan.remark = form.y_gre_8_remark.data
        db.session.add(y_gre_8_plan)
        db.session.commit()
        for item in y_gre_8_plan.notate_bene:
            y_gre_8_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.y_gre_8_notate_bene.data:
            y_gre_8_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update Y-GRE plan: 9
        y_gre_9_start_date = None
        if form.y_gre_9_start_date.data:
            y_gre_9_start_date = form.y_gre_9_start_date.data
        y_gre_9_end_date = None
        if form.y_gre_9_end_date.data:
            y_gre_9_end_date = form.y_gre_9_end_date.data
        if y_gre_9_plan is None:
            y_gre_9_plan = StudyPlan(
                user_id=user.id,
                lesson_id=y_gre_9.id,
                start_date=y_gre_9_start_date,
                end_date=y_gre_9_end_date,
                remark=form.y_gre_9_remark.data
            )
        else:
            y_gre_9_plan.start_date = y_gre_9_start_date
            y_gre_9_plan.end_date = y_gre_9_end_date
            y_gre_9_plan.remark = form.y_gre_9_remark.data
        db.session.add(y_gre_9_plan)
        db.session.commit()
        for item in y_gre_9_plan.notate_bene:
            y_gre_9_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.y_gre_9_notate_bene.data:
            y_gre_9_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update Y-GRE plan: prep
        y_gre_prep_start_date = None
        if form.y_gre_prep_start_date.data:
            y_gre_prep_start_date = form.y_gre_prep_start_date.data
        y_gre_prep_end_date = None
        if form.y_gre_prep_end_date.data:
            y_gre_prep_end_date = form.y_gre_prep_end_date.data
        if y_gre_prep_plan is None:
            y_gre_prep_plan = StudyPlan(
                user_id=user.id,
                lesson_id=y_gre_prep.id,
                start_date=y_gre_prep_start_date,
                end_date=y_gre_prep_end_date,
                remark=form.y_gre_prep_remark.data
            )
        else:
            y_gre_prep_plan.start_date = y_gre_prep_start_date
            y_gre_prep_plan.end_date = y_gre_prep_end_date
            y_gre_prep_plan.remark = form.y_gre_prep_remark.data
        db.session.add(y_gre_prep_plan)
        db.session.commit()
        for item in y_gre_prep_plan.notate_bene:
            y_gre_prep_plan.remove_nota_bene(nota_bene=item.nota_bene)
        for nota_bene_id in form.y_gre_prep_notate_bene.data:
            y_gre_prep_plan.add_nota_bene(nota_bene=NotaBene.query.get(int(nota_bene_id)))
        # update GRE test dates
        if form.gre_0_date.data:
            gre_0_test = GRETest.query.filter_by(date=form.gre_0_date.data).first()
            if gre_0_test is None:
                gre_0_test = GRETest(date=form.gre_0_date.data)
                db.session.add(gre_0_test)
                db.session.commit()
            if gre_0_score is None:
                gre_0_score = GRETestScore(
                    user_id=user.id,
                    test_id=gre_0_test.id,
                    label_id=gre_0_score_label.id,
                    modified_by_id=current_user.id
                )
            else:
                gre_0_score.test_id = gre_0_test.id
                gre_0_score.modified_by_id = current_user.id
                gre_0_score.modified_at = datetime.utcnow()
            db.session.add(gre_0_score)
            db.session.commit()
        if form.gre_1_date.data:
            gre_1_test = GRETest.query.filter_by(date=form.gre_1_date.data).first()
            if gre_1_test is None:
                gre_1_test = GRETest(date=form.gre_1_date.data)
                db.session.add(gre_1_test)
                db.session.commit()
            if gre_1_score is None:
                gre_1_score = GRETestScore(
                    user_id=user.id,
                    test_id=gre_1_test.id,
                    label_id=gre_1_score_label.id,
                    modified_by_id=current_user.id
                )
            else:
                gre_1_score.test_id = gre_1_test.id
                gre_1_score.modified_by_id = current_user.id
                gre_1_score.modified_at = datetime.utcnow()
            db.session.add(gre_1_score)
            db.session.commit()
        if form.gre_2_date.data:
            gre_2_test = GRETest.query.filter_by(date=form.gre_2_date.data).first()
            if gre_2_test is None:
                gre_2_test = GRETest(date=form.gre_2_date.data)
                db.session.add(gre_2_test)
                db.session.commit()
            if gre_2_score is None:
                gre_2_score = GRETestScore(
                    user_id=user.id,
                    test_id=gre_2_test.id,
                    label_id=gre_2_score_label.id,
                    modified_by_id=current_user.id
                )
            else:
                gre_2_score.test_id = gre_2_test.id
                gre_2_score.modified_by_id = current_user.id
                gre_2_score.modified_at = datetime.utcnow()
            db.session.add(gre_2_score)
            db.session.commit()
        if form.gre_3_date.data:
            gre_3_test = GRETest.query.filter_by(date=form.gre_3_date.data).first()
            if gre_3_test is None:
                gre_3_test = GRETest(date=form.gre_3_date.data)
                db.session.add(gre_3_test)
                db.session.commit()
            if gre_3_score is None:
                gre_3_score = GRETestScore(
                    user_id=user.id,
                    test_id=gre_3_test.id,
                    label_id=gre_3_score_label.id,
                    modified_by_id=current_user.id
                )
            else:
                gre_3_score.test_id = gre_3_test.id
                gre_3_score.modified_by_id = current_user.id
                gre_3_score.modified_at = datetime.utcnow()
            db.session.add(gre_3_score)
            db.session.commit()
        # update supervisor
        if form.supervisor_email.data:
            if user.supervised_by:
                user.supervised_by.unsupervise_user(user=user)
            supervisor = User.query.filter_by(email=form.supervisor_email.data.lower(), created=True, activated=True, deleted=False).first()
            if supervisor is None:
                flash(u'设计人邮箱不存在：%s' % form.supervisor_email.data.lower(), category='error')
                return redirect(url_for('manage.edit_study_plan', id=user.id, next=request.args.get('next')))
            supervisor.supervise_user(user=user)
        flash(u'已更新%s的研修计划' % user.name_alias, category='success')
        add_feed(user=current_user._get_current_object(), event=u'更新%s的研修计划' % user.name_alias, category=u'manage')
        return redirect(request.args.get('next') or url_for('main.profile_overview', id=user.id))
    # aim scores
    if gre_aim_score is not None:
        form.gre_aim_v.data = gre_aim_score.v_score
        form.gre_aim_q.data = gre_aim_score.q_score
        form.gre_aim_aw.data = unicode(gre_aim_score.aw_score_id)
    if toefl_aim_score is not None:
        form.toefl_aim_total.data = toefl_aim_score.total_score
        form.toefl_aim_reading.data = toefl_aim_score.reading_score
        form.toefl_aim_listening.data = toefl_aim_score.listening_score
        form.toefl_aim_speaking.data = toefl_aim_score.speaking_score
        form.toefl_aim_writing.data = toefl_aim_score.writing_score
    # time parameters
    form.start_date.data = date.today()
    form.deadline.data = user.deadline or user.due_date
    form.speed.data = user.speed
    form.intensity.data = 10.0
    # VB plan
    if vb_intro_plan is not None:
        form.start_date.data = vb_intro_plan.start_date
        form.vb_intro_start_date.data = vb_intro_plan.start_date
        form.vb_intro_end_date.data = vb_intro_plan.end_date
        form.vb_intro_notate_bene.data = [unicode(item.nota_bene_id) for item in vb_intro_plan.notate_bene]
        form.vb_intro_remark.data = vb_intro_plan.remark
    if vb_1_plan is not None:
        form.vb_1_start_date.data = vb_1_plan.start_date
        form.vb_1_end_date.data = vb_1_plan.end_date
        form.vb_1_notate_bene.data = [unicode(item.nota_bene_id) for item in vb_1_plan.notate_bene]
        form.vb_1_remark.data = vb_1_plan.remark
    if vb_2_plan is not None:
        form.vb_2_start_date.data = vb_2_plan.start_date
        form.vb_2_end_date.data = vb_2_plan.end_date
        form.vb_2_notate_bene.data = [unicode(item.nota_bene_id) for item in vb_2_plan.notate_bene]
        form.vb_2_remark.data = vb_2_plan.remark
    if vb_3_plan is not None:
        form.vb_3_start_date.data = vb_3_plan.start_date
        form.vb_3_end_date.data = vb_3_plan.end_date
        form.vb_3_notate_bene.data = [unicode(item.nota_bene_id) for item in vb_3_plan.notate_bene]
        form.vb_3_remark.data = vb_3_plan.remark
    if vb_4_plan is not None:
        form.vb_4_start_date.data = vb_4_plan.start_date
        form.vb_4_end_date.data = vb_4_plan.end_date
        form.vb_4_notate_bene.data = [unicode(item.nota_bene_id) for item in vb_4_plan.notate_bene]
        form.vb_4_remark.data = vb_4_plan.remark
    if vb_5_plan is not None:
        form.vb_5_start_date.data = vb_5_plan.start_date
        form.vb_5_end_date.data = vb_5_plan.end_date
        form.vb_5_notate_bene.data = [unicode(item.nota_bene_id) for item in vb_5_plan.notate_bene]
        form.vb_5_remark.data = vb_5_plan.remark
    if vb_6_plan is not None:
        form.vb_6_start_date.data = vb_6_plan.start_date
        form.vb_6_end_date.data = vb_6_plan.end_date
        form.vb_6_notate_bene.data = [unicode(item.nota_bene_id) for item in vb_6_plan.notate_bene]
        form.vb_6_remark.data = vb_6_plan.remark
    if vb_7_plan is not None:
        form.vb_7_start_date.data = vb_7_plan.start_date
        form.vb_7_end_date.data = vb_7_plan.end_date
        form.vb_7_notate_bene.data = [unicode(item.nota_bene_id) for item in vb_7_plan.notate_bene]
        form.vb_7_remark.data = vb_7_plan.remark
    if vb_8_plan is not None:
        form.vb_8_start_date.data = vb_8_plan.start_date
        form.vb_8_end_date.data = vb_8_plan.end_date
        form.vb_8_notate_bene.data = [unicode(item.nota_bene_id) for item in vb_8_plan.notate_bene]
        form.vb_8_remark.data = vb_8_plan.remark
    if vb_9_plan is not None:
        form.vb_9_start_date.data = vb_9_plan.start_date
        form.vb_9_end_date.data = vb_9_plan.end_date
        form.vb_9_notate_bene.data = [unicode(item.nota_bene_id) for item in vb_9_plan.notate_bene]
        form.vb_9_remark.data = vb_9_plan.remark
    # Y-GRE plan
    if y_gre_intro_plan is not None:
        form.y_gre_intro_start_date.data = y_gre_intro_plan.start_date
        form.y_gre_intro_end_date.data = y_gre_intro_plan.end_date
        form.y_gre_intro_notate_bene.data = [unicode(item.nota_bene_id) for item in y_gre_intro_plan.notate_bene]
        form.y_gre_intro_remark.data = y_gre_intro_plan.remark
    if y_gre_1_plan is not None:
        form.y_gre_1_start_date.data = y_gre_1_plan.start_date
        form.y_gre_1_end_date.data = y_gre_1_plan.end_date
        form.y_gre_1_notate_bene.data = [unicode(item.nota_bene_id) for item in y_gre_1_plan.notate_bene]
        form.y_gre_1_remark.data = y_gre_1_plan.remark
    if y_gre_2_plan is not None:
        form.y_gre_2_start_date.data = y_gre_2_plan.start_date
        form.y_gre_2_end_date.data = y_gre_2_plan.end_date
        form.y_gre_2_notate_bene.data = [unicode(item.nota_bene_id) for item in y_gre_2_plan.notate_bene]
        form.y_gre_2_remark.data = y_gre_2_plan.remark
    if y_gre_3_plan is not None:
        form.y_gre_3_start_date.data = y_gre_3_plan.start_date
        form.y_gre_3_end_date.data = y_gre_3_plan.end_date
        form.y_gre_3_notate_bene.data = [unicode(item.nota_bene_id) for item in y_gre_3_plan.notate_bene]
        form.y_gre_3_remark.data = y_gre_3_plan.remark
    if y_gre_4_plan is not None:
        form.y_gre_4_start_date.data = y_gre_4_plan.start_date
        form.y_gre_4_end_date.data = y_gre_4_plan.end_date
        form.y_gre_4_notate_bene.data = [unicode(item.nota_bene_id) for item in y_gre_4_plan.notate_bene]
        form.y_gre_4_remark.data = y_gre_4_plan.remark
    if y_gre_5_plan is not None:
        form.y_gre_5_start_date.data = y_gre_5_plan.start_date
        form.y_gre_5_end_date.data = y_gre_5_plan.end_date
        form.y_gre_5_notate_bene.data = [unicode(item.nota_bene_id) for item in y_gre_5_plan.notate_bene]
        form.y_gre_5_remark.data = y_gre_5_plan.remark
    if y_gre_6_plan is not None:
        form.y_gre_6_start_date.data = y_gre_6_plan.start_date
        form.y_gre_6_end_date.data = y_gre_6_plan.end_date
        form.y_gre_6_notate_bene.data = [unicode(item.nota_bene_id) for item in y_gre_6_plan.notate_bene]
        form.y_gre_6_remark.data = y_gre_6_plan.remark
    if y_gre_7_plan is not None:
        form.y_gre_7_start_date.data = y_gre_7_plan.start_date
        form.y_gre_7_end_date.data = y_gre_7_plan.end_date
        form.y_gre_7_notate_bene.data = [unicode(item.nota_bene_id) for item in y_gre_7_plan.notate_bene]
        form.y_gre_7_remark.data = y_gre_7_plan.remark
    if y_gre_8_plan is not None:
        form.y_gre_8_start_date.data = y_gre_8_plan.start_date
        form.y_gre_8_end_date.data = y_gre_8_plan.end_date
        form.y_gre_8_notate_bene.data = [unicode(item.nota_bene_id) for item in y_gre_8_plan.notate_bene]
        form.y_gre_8_remark.data = y_gre_8_plan.remark
    if y_gre_9_plan is not None:
        form.y_gre_9_start_date.data = y_gre_9_plan.start_date
        form.y_gre_9_end_date.data = y_gre_9_plan.end_date
        form.y_gre_9_notate_bene.data = [unicode(item.nota_bene_id) for item in y_gre_9_plan.notate_bene]
        form.y_gre_9_remark.data = y_gre_9_plan.remark
    if y_gre_prep_plan is not None:
        form.y_gre_prep_start_date.data = y_gre_prep_plan.start_date
        form.y_gre_prep_end_date.data = y_gre_prep_plan.end_date
        form.y_gre_prep_notate_bene.data = [unicode(item.nota_bene_id) for item in y_gre_prep_plan.notate_bene]
        form.y_gre_prep_remark.data = y_gre_prep_plan.remark
    # GRE test dates
    if gre_0_score is not None:
        form.gre_0_date.data = gre_0_score.test.date
    if gre_1_score is not None:
        form.gre_1_date.data = gre_1_score.test.date
    if gre_2_score is not None:
        form.gre_2_date.data = gre_2_score.test.date
    if gre_3_score is not None:
        form.gre_3_date.data = gre_3_score.test.date
    # supervisor
    if user.supervised_by is not None:
        form.supervisor_email.data = user.supervised_by.email
    return render_template('manage/edit_study_plan.html', form=form, user=user)


@manage.route('/study-plan/generate/<int:id>')
@login_required
@permission_required(u'管理研修计划')
def generate_study_plan(id):
    user = User.query.get_or_404(id)
    if not user.created or user.deleted:
        abort(404)
    start_date = request.args.get('start_date')
    deadline = request.args.get('deadline')
    speed = request.args.get('speed')
    intensity = request.args.get('intensity')
    study_plan = {
        'valid': False,
    }
    if start_date and deadline and speed and intensity:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        deadline = datetime.strptime(deadline, '%Y-%m-%d').date()
        speed = float(speed)
        intensity = float(intensity)
        tdelta = deadline - start_date
        total_days = tdelta.days + 1
        study_plan['valid'] = True
        study_plan[u'VB总论'] = u''
        study_plan[u'L1'] = u''
        study_plan[u'L2'] = u''
        study_plan[u'L3'] = u''
        study_plan[u'L4'] = u''
        study_plan[u'L5'] = u''
        study_plan[u'L6'] = u''
        study_plan[u'L7'] = u''
        study_plan[u'L8'] = u''
        study_plan[u'L9'] = u''
        if user.can(u'预约Y-GRE课程'):
            study_plan[u'Y-GRE总论'] = u''
            study_plan[u'1st'] = u''
            study_plan[u'2nd'] = u''
            study_plan[u'3rd'] = u''
            study_plan[u'4th'] = u''
            study_plan[u'5th'] = u''
            study_plan[u'6th'] = u''
            study_plan[u'7th'] = u''
            study_plan[u'8th'] = u''
            study_plan[u'9th'] = u''
            study_plan[u'Y-GRE临考'] = u''
            priority = None
            for lesson in Lesson.query\
                .filter(Lesson.priority >= 1)\
                .order_by(Lesson.priority.desc())\
                .order_by(Lesson.type_id.asc())\
                .order_by(Lesson.order.asc())\
                .all():
                if int(lesson.least_accumulated_seconds / 3600.0 / intensity / speed * 7) < total_days:
                    priority = lesson.priority
                else:
                    break
            if priority is not None:
                current_date = start_date - timedelta(days=1)
                for lesson in Lesson.query\
                    .filter(Lesson.priority >= priority)\
                    .order_by(Lesson.type_id.asc())\
                    .order_by(Lesson.order.asc())\
                    .all():
                    start_date = current_date + timedelta(days=1)
                    end_date = current_date + timedelta(days=int(lesson.hour.total_seconds() / 3600.0 / intensity / speed * 7))
                    study_plan[lesson.name] = {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                    }
                    current_date = end_date
        else:
            current_date = start_date - timedelta(days=1)
            for lesson in Lesson.query\
                .join(CourseType, CourseType.id == Lesson.type_id)\
                .filter(CourseType.name == u'VB')\
                .filter(Lesson.priority >= 1)\
                .order_by(Lesson.order.asc())\
                .all():
                start_date = current_date + timedelta(days=1)
                end_date = current_date + timedelta(days=int(lesson.hour.total_seconds() / 3600.0 / intensity / speed * 7))
                if end_date > deadline:
                    break
                study_plan[lesson.name] = {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                }
                current_date = end_date
    return jsonify(study_plan)


@manage.route('/nota-bene', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理NB')
def nota_bene():
    form = NewNotaBeneForm()
    if form.validate_on_submit():
        nota_bene = NotaBene(
            body=form.body.data,
            type_id=int(form.nota_bene_type.data),
            modified_by_id=current_user.id
        )
        db.session.add(nota_bene)
        flash(u'已添加N.B.模板：%s' % form.body.data, category='success')
        add_feed(user=current_user._get_current_object(), event=u'添加N.B.模板：%s' % form.body.data, category=u'manage')
        return redirect(url_for('manage.nota_bene', page=request.args.get('page', 1, type=int)))
    show_vb_notate_bene = True
    show_y_gre_notate_bene = False
    if current_user.is_authenticated:
        show_vb_notate_bene = bool(request.cookies.get('show_vb_notate_bene', '1'))
        show_y_gre_notate_bene = bool(request.cookies.get('show_y_gre_notate_bene', ''))
    if show_vb_notate_bene:
        query = NotaBene.query\
            .join(CourseType, CourseType.id == NotaBene.type_id)\
            .filter(CourseType.name == u'VB')\
            .filter(NotaBene.deleted == False)
    if show_y_gre_notate_bene:
        query = NotaBene.query\
            .join(CourseType, CourseType.id == NotaBene.type_id)\
            .filter(CourseType.name == u'Y-GRE')\
            .filter(NotaBene.deleted == False)
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    notate_bene = pagination.items
    return render_template('manage/nota_bene.html',
        form=form,
        show_vb_notate_bene=show_vb_notate_bene,
        show_y_gre_notate_bene=show_y_gre_notate_bene,
        pagination=pagination,
        notate_bene=notate_bene
    )


@manage.route('/nota-bene/vb')
@login_required
@permission_required(u'管理NB')
def vb_notate_bene():
    resp = make_response(redirect(url_for('manage.nota_bene')))
    resp.set_cookie('show_vb_notate_bene', '1', max_age=30*24*60*60)
    resp.set_cookie('show_y_gre_notate_bene', '', max_age=30*24*60*60)
    return resp


@manage.route('/nota-bene/y-gre')
@login_required
@permission_required(u'管理NB')
def y_gre_notate_bene():
    resp = make_response(redirect(url_for('manage.nota_bene')))
    resp.set_cookie('show_vb_notate_bene', '', max_age=30*24*60*60)
    resp.set_cookie('show_y_gre_notate_bene', '1', max_age=30*24*60*60)
    return resp


@manage.route('/nota-bene/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理NB')
def edit_nota_bene(id):
    nota_bene = NotaBene.query.get_or_404(id)
    if nota_bene.deleted:
        abort(404)
    form = EditNotaBeneForm()
    if form.validate_on_submit():
        nota_bene.body = form.body.data
        nota_bene.type_id = int(form.nota_bene_type.data)
        nota_bene.modified_at = datetime.utcnow()
        nota_bene.modified_by_id = current_user.id
        db.session.add(nota_bene)
        flash(u'已更新N.B.模板：%s' % form.body.data, category='success')
        add_feed(user=current_user._get_current_object(), event=u'更新N.B.模板：%s' % form.body.data, category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.nota_bene'))
    form.body.data = nota_bene.body
    form.nota_bene_type.data = unicode(nota_bene.type_id)
    return render_template('manage/edit_nota_bene.html', form=form, nota_bene=nota_bene)


@manage.route('/nota-bene/delete/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理NB')
def delete_nota_bene(id):
    nota_bene = NotaBene.query.get_or_404(id)
    if nota_bene.deleted:
        abort(404)
    nota_bene.safe_delete(modified_by=current_user._get_current_object())
    flash(u'已删除N.B.模板：%s' % nota_bene.body, category='success')
    add_feed(user=current_user._get_current_object(), event=u'删除N.B.模板：%s' % nota_bene.body, category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.nota_bene'))


@manage.route('/feedback', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理反馈')
def feedback():
    form = NewFeedbackForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower(), created=True, activated=True, deleted=False).first()
        if user is None:
            flash(u'用户邮箱不存在：%s' % form.email.data.lower(), category='error')
            return redirect(url_for('manage.feedback', page=request.args.get('page', 1, type=int)))
        lesson = Lesson.query.get_or_404(int(form.lesson.data))
        study_plan = StudyPlan.query.filter_by(user_id=user.id, lesson_id=lesson.id).first()
        if study_plan is None:
            flash(u'尚未创建“%s”的“%s”研修计划' % (user.name_alias, lesson.alias), category='error')
            return redirect(url_for('manage.feedback', page=request.args.get('page', 1, type=int)))
        feedback = Feedback(
            study_plan_id=study_plan.id,
            body_html=form.body.data,
            modified_by_id=current_user.id
        )
        db.session.add(feedback)
        db.session.commit()
        send_email(user.email, u'研修反馈：%s' % lesson.alias, 'manage/mail/feedback', user=user, feedback=feedback)
        flash(u'已添加“%s”的“%s”研修反馈' % (user.name_alias, lesson.alias), category='success')
        add_feed(user=current_user._get_current_object(), event=u'添加“%s”的“%s”研修反馈' % (user.name_alias, lesson.alias), category=u'manage')
        return redirect(url_for('manage.feedback', page=request.args.get('page', 1, type=int)))
    search_form = SearchForm(prefix='search')
    if search_form.validate_on_submit():
        keyword = search_form.keyword.data
        return redirect(url_for('manage.search_feedback_results', keyword=keyword))
    show_all_feedbacks = True
    show_search_feedbacks = False
    if current_user.is_authenticated:
        show_all_feedbacks = bool(request.cookies.get('show_all_feedbacks', '1'))
        show_search_feedbacks = bool(request.cookies.get('show_search_feedbacks', ''))
    if show_all_feedbacks:
        query = Feedback.query\
            .filter(Feedback.deleted == False)\
            .order_by(Feedback.modified_at.desc())
    if show_search_feedbacks:
        keyword = request.args.get('keyword')
        user = User.query.filter_by(email=keyword, created=True, activated=True, deleted=False).first()
        if user is not None:
            query = Feedback.query\
                .join(StudyPlan, StudyPlan.id == Feedback.study_plan_id)\
                .filter(StudyPlan.user_id == user.id)\
                .filter(Feedback.deleted == False)\
                .order_by(Feedback.modified_at.desc())
            search_form.keyword.data = keyword
        else:
            return redirect(url_for('manage.all_feedbacks'))
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    feedbacks = pagination.items
    return render_template('manage/feedback.html',
        form=form,
        search_form=search_form,
        pagination=pagination,
        feedbacks=feedbacks
    )


@manage.route('/feedback/all')
@login_required
@permission_required(u'管理反馈')
def all_feedbacks():
    resp = make_response(redirect(url_for('manage.feedback')))
    resp.set_cookie('show_all_feedbacks', '1', max_age=30*24*60*60)
    resp.set_cookie('show_search_feedbacks', '', max_age=30*24*60*60)
    return resp


@manage.route('/feedback/search/results')
@login_required
@permission_required(u'管理反馈')
def search_feedback_results():
    resp = make_response(redirect(url_for('manage.feedback', keyword=request.args.get('keyword'))))
    resp.set_cookie('show_all_feedbacks', '', max_age=30*24*60*60)
    resp.set_cookie('show_search_feedbacks', '1', max_age=30*24*60*60)
    return resp


@manage.route('/feedback/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理反馈')
def edit_feedback(id):
    feedback = Feedback.query.get_or_404(id)
    if feedback.deleted:
        abort(404)
    form = EditFeedbackForm()
    if form.validate_on_submit():
        lesson = Lesson.query.get_or_404(int(form.lesson.data))
        study_plan = StudyPlan.query.filter_by(user_id=feedback.study_plan.user_id, lesson_id=lesson.id).first()
        if study_plan is None:
            flash(u'尚未创建“%s”的“%s”研修计划' % (feedback.study_plan.user.name_alias, lesson.alias), category='error')
            return redirect(url_for('manage.edit_feedback', id=feedback.id, page=request.args.get('page', 1, type=int)))
        feedback.study_plan_id = study_plan.id
        feedback.body_html = form.body.data
        feedback.unread = True
        feedback.modified_at = datetime.utcnow()
        feedback.modified_by_id = current_user.id
        db.session.add(feedback)
        db.session.commit()
        send_email(feedback.study_plan.user.email, u'研修反馈：%s' % lesson.alias, 'manage/mail/feedback', user=feedback.study_plan.user, feedback=feedback)
        flash(u'已更新“%s”的“%s”研修反馈' % (feedback.study_plan.user.name_alias, lesson.alias), category='success')
        add_feed(user=current_user._get_current_object(), event=u'更新“%s”的“%s”研修反馈' % (feedback.study_plan.user.name_alias, lesson.alias), category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.feedback'))
    form.user.data = feedback.study_plan.user.name_alias
    form.lesson.data = unicode(feedback.study_plan.lesson.id)
    form.body.data = feedback.body_html
    return render_template('manage/edit_feedback.html', form=form, feedback=feedback)


@manage.route('/feedback/delete/<int:id>')
@login_required
@permission_required(u'管理反馈')
def delete_feedback(id):
    feedback = Feedback.query.get_or_404(id)
    if feedback.deleted:
        abort(404)
    feedback.safe_delete(modified_by=current_user._get_current_object())
    flash(u'已删除“%s”的“%s”研修反馈' % (feedback.study_plan.user.name_alias, feedback.study_plan.lesson.alias), category='success')
    add_feed(user=current_user._get_current_object(), event=u'删除“%s”的“%s”研修反馈' % (feedback.study_plan.user.name_alias, feedback.study_plan.lesson.alias), category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.feedback'))


@manage.route('/announcement', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理通知')
def announcement():
    form = NewAnnouncementForm()
    if form.validate_on_submit():
        announcement = Announcement(
            title=form.title.data,
            body_html=form.body.data,
            type_id=int(form.announcement_type.data),
            modified_by_id=current_user.id
        )
        db.session.add(announcement)
        db.session.commit()
        if form.show.data:
            announcement.publish(modified_by=current_user._get_current_object())
            if announcement.type.name == u'用户邮件通知':
                for user in User.users_can(u'预约').all():
                    send_email(user.email, announcement.title, 'manage/mail/announcement', user=user, announcement=announcement)
            if announcement.type.name == u'管理邮件通知':
                for user in User.users_can(u'管理').all():
                    send_email(user.email, announcement.title, 'manage/mail/announcement', user=user, announcement=announcement)
        else:
            announcement.clean_up()
        flash(u'已添加通知：“%s”' % form.title.data, category='success')
        add_feed(user=current_user._get_current_object(), event=u'添加通知：“%s”' % form.title.data, category=u'manage')
        return redirect(url_for('manage.announcement', page=request.args.get('page', 1, type=int)))
    query = Announcement.query\
        .filter(Announcement.deleted == False)\
        .order_by(Announcement.modified_at.desc())
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    announcements = pagination.items
    return render_template('manage/announcement.html',
        form=form,
        pagination=pagination,
        announcements=announcements
    )


@manage.route('/announcement/publish/<int:id>')
@login_required
@permission_required(u'管理通知')
def publish_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    if announcement.show:
        flash(u'所选通知已经发布', category='warning')
        return redirect(request.args.get('next') or url_for('manage.announcement'))
    announcement.publish(modified_by=current_user._get_current_object())
    if announcement.type.name == u'用户邮件通知':
        for user in User.users_can(u'预约').all():
            send_email(user.email, announcement.title, 'manage/mail/announcement', user=user, announcement=announcement)
    if announcement.type.name == u'管理邮件通知':
        for user in User.users_can(u'管理').all():
            send_email(user.email, announcement.title, 'manage/mail/announcement', user=user, announcement=announcement)
    flash(u'“%s”发布成功！' % announcement.title, category='success')
    add_feed(user=current_user._get_current_object(), event=u'发布通知：“%s”' % announcement.title, category=u'manage')
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
    add_feed(user=current_user._get_current_object(), event=u'撤销通知：“%s”' % announcement.title, category=u'manage')
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
        add_feed(user=current_user._get_current_object(), event=u'更新通知：“%s”' % form.title.data, category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.announcement'))
    form.title.data = announcement.title
    form.body.data = announcement.body_html
    form.announcement_type.data = unicode(announcement.type_id)
    form.show.data = announcement.show
    return render_template('manage/edit_announcement.html', form=form, announcement=announcement)


@manage.route('/announcement/delete/<int:id>')
@login_required
@permission_required(u'管理通知')
def delete_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    if announcement.deleted:
        abort(404)
    announcement.safe_delete(modified_by=current_user._get_current_object())
    flash(u'已删除通知：“%s”' % announcement.title, category='success')
    add_feed(user=current_user._get_current_object(), event=u'删除通知：“%s”' % announcement.title, category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.announcement'))


@manage.route('/product', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理产品')
def product():
    form = NewProductForm()
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            price=float(form.price.data),
            available=form.available.data,
            modified_by_id=current_user.id
        )
        db.session.add(product)
        flash(u'已添加研修产品：%s' % form.name.data, category='success')
        add_feed(user=current_user._get_current_object(), event=u'添加研修产品：%s' % form.name.data, category=u'manage')
        return redirect(url_for('manage.product', page=request.args.get('page', 1, type=int)))
    query = Product.query.filter_by(deleted=False)
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    products = pagination.items
    return render_template('manage/product.html',
        form=form,
        pagination=pagination,
        products=products
    )


@manage.route('/product/toggle-availability/<int:id>')
@login_required
@permission_required(u'管理产品')
def toggle_product_availability(id):
    product = Product.query.get_or_404(id)
    if product.deleted:
        abort(404)
    product.toggle_availability(modified_by=current_user._get_current_object())
    if product.available:
        flash(u'“%s”的可选状态改为：可选' % product.name, category='success')
        add_feed(user=current_user._get_current_object(), event=u'修改“%s”的可选状态改为：可选' % product.name, category=u'manage')
    else:
        flash(u'“%s”的可选状态改为：不可选' % product.name, category='success')
        add_feed(user=current_user._get_current_object(), event=u'修改“%s”的可选状态改为：不可选' % product.name, category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.product'))


@manage.route('/product/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(u'管理产品')
def edit_product(id):
    product = Product.query.get_or_404(id)
    if product.deleted:
        abort(404)
    form = EditProductForm()
    if form.validate_on_submit():
        if current_user.is_developer or not product.pinned:
            product.name = form.name.data
        if product.purchases.count() == 0:
            product.price = float(form.price.data)
        product.available = form.available.data
        product.modified_at = datetime.utcnow()
        product.modified_by_id = current_user.id
        db.session.add(product)
        flash(u'已更新研修产品：%s' % form.name.data, category='success')
        add_feed(user=current_user._get_current_object(), event=u'更新研修产品：%s' % form.name.data, category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.product'))
    form.name.data = product.name
    form.price.data = unicode(product.price)
    form.available.data = product.available
    return render_template('manage/edit_product.html', form=form, product=product)


@manage.route('/product/delete/<int:id>')
@login_required
@permission_required(u'管理产品')
def delete_product(id):
    product = Product.query.get_or_404(id)
    if product.deleted:
        abort(404)
    if product.pinned and not current_user.is_developer:
        abort(403)
    product.safe_delete(modified_by=current_user._get_current_object())
    flash(u'已删除研修产品：%s' % product.name, category='success')
    add_feed(user=current_user._get_current_object(), event=u'删除研修产品：%s' % product.name, category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.product'))


@manage.route('/product/purchase/<int:id>')
@login_required
@permission_required(u'管理产品')
def product_purchase(id):
    product = Product.query.get_or_404(id)
    if product.deleted:
        abort(404)
    if product.sales_volume == 0:
        return redirect(url_for('manage.product'))
    query = Purchase.query\
        .join(User, User.id == Purchase.user_id)\
        .filter(Purchase.product_id == product.id)\
        .filter(User.created == True)\
        .filter(User.activated == True)\
        .filter(User.deleted == False)\
        .order_by(Purchase.timestamp.desc())
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    purchases = pagination.items
    return render_template('manage/product_purchase.html',
        product=product,
        pagination=pagination,
        purchases=purchases
    )


@manage.route('/role', methods=['GET', 'POST'])
@login_required
@developer_required
def role():
    form = NewRoleForm()
    if form.validate_on_submit():
        if Role.query.filter_by(name=form.name.data).first() is not None:
            flash(u'“%s”角色已存在' % form.name.data, category='error')
            return redirect(url_for('manage.role', page=request.args.get('page', 1, type=int)))
        role = Role(name=form.name.data)
        db.session.add(role)
        db.session.commit()
        for permission_id in form.booking_permissions.data + form.manage_permissions.data:
            role.add_permission(permission=Permission.query.get(int(permission_id)))
        if form.is_developer.data:
            role.add_permission(permission=Permission.query.filter_by(name=u'开发权限').first())
        flash(u'已添加角色：%s' % form.name.data, category='success')
        add_feed(user=current_user._get_current_object(), event=u'添加角色：%s' % form.name.data, category=u'manage')
        return redirect(url_for('manage.role', page=request.args.get('page', 1, type=int)))
    query = Role.query
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    roles = pagination.items
    return render_template('manage/role.html',
        form=form,
        pagination=pagination,
        roles=roles
    )


@manage.route('/role/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@developer_required
def edit_role(id):
    role = Role.query.get_or_404(id)
    form = EditRoleForm(role=role)
    if form.validate_on_submit():
        role.name = form.name.data
        db.session.add(role)
        for role_permission in role.permissions:
            role.remove_permission(permission=Permission.query.get(role_permission.permission_id))
        for permission_id in form.booking_permissions.data + form.manage_permissions.data:
            role.add_permission(permission=Permission.query.get(int(permission_id)))
        if form.is_developer.data:
            role.add_permission(permission=Permission.query.filter_by(name=u'开发权限').first())
        flash(u'已更新角色：%s' % form.name.data, category='success')
        add_feed(user=current_user._get_current_object(), event=u'更新角色：%s' % form.name.data, category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.role'))
    form.name.data = role.name
    form.booking_permissions.data = [unicode(permission.id) for permission in role.permissions_alias(prefix=u'预约', formatted=False)]
    form.manage_permissions.data = [unicode(permission.id) for permission in role.permissions_alias(prefix=u'管理', formatted=False)]
    form.is_developer.data = role.has_permission(Permission.query.filter_by(name=u'开发权限').first())
    return render_template('manage/edit_role.html', form=form, role=role)


@manage.route('/role/delete/<int:id>')
@login_required
@developer_required
def delete_role(id):
    role = Role.query.get_or_404(id)
    if role.users.count():
        abort(403)
    for role_permission in role.permissions:
        role.remove_permission(permission=Permission.query.get(role_permission.permission_id))
    db.session.delete(role)
    flash(u'已删除角色：%s' % role.name, category='success')
    add_feed(user=current_user._get_current_object(), event=u'删除角色：%s' % role.name, category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.role'))


@manage.route('/permission', methods=['GET', 'POST'])
@login_required
@developer_required
def permission():
    form = NewPermissionForm()
    if form.validate_on_submit():
        if Permission.query.filter_by(name=form.name.data).first() is not None:
            flash(u'“%s”权限已存在' % form.name.data, category='error')
            return redirect(url_for('manage.permission', page=request.args.get('page', 1, type=int)))
        permission = Permission(name=form.name.data, check_overdue=form.check_overdue.data)
        db.session.add(permission)
        flash(u'已添加权限：%s' % form.name.data, category='success')
        add_feed(user=current_user._get_current_object(), event=u'添加权限：%s' % form.name.data, category=u'manage')
        return redirect(url_for('manage.permission', page=request.args.get('page', 1, type=int)))
    show_booking_permissions = True
    show_manage_permissions = False
    show_develop_permissions = False
    show_other_permissions = False
    if current_user.is_authenticated:
        show_booking_permissions = bool(request.cookies.get('show_booking_permissions', '1'))
        show_manage_permissions = bool(request.cookies.get('show_manage_permissions', ''))
        show_develop_permissions = bool(request.cookies.get('show_develop_permissions', ''))
        show_other_permissions = bool(request.cookies.get('show_other_permissions', ''))
    if show_booking_permissions:
        query = Permission.query\
            .filter(Permission.name.like(u'预约%'))\
            .order_by(Permission.id.asc())
    if show_manage_permissions:
        query = Permission.query\
            .filter(Permission.name.like(u'管理%'))\
            .order_by(Permission.id.asc())
    if show_develop_permissions:
        query = Permission.query\
            .filter(Permission.name.like(u'开发%'))\
            .order_by(Permission.id.asc())
    if show_other_permissions:
        query = Permission.query\
            .filter(and_(
                Permission.name.notlike(u'预约%'),
                Permission.name.notlike(u'管理%'),
                Permission.name.notlike(u'开发%'),
            ))\
            .order_by(Permission.id.asc())
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    permissions = pagination.items
    return render_template('manage/permission.html',
        form=form,
        show_booking_permissions=show_booking_permissions,
        show_manage_permissions=show_manage_permissions,
        show_develop_permissions=show_develop_permissions,
        show_other_permissions=show_other_permissions,
        pagination=pagination,
        permissions=permissions
    )


@manage.route('/permission/book')
@login_required
@developer_required
def booking_permissions():
    resp = make_response(redirect(url_for('manage.permission')))
    resp.set_cookie('show_booking_permissions', '1', max_age=30*24*60*60)
    resp.set_cookie('show_manage_permissions', '', max_age=30*24*60*60)
    resp.set_cookie('show_develop_permissions', '', max_age=30*24*60*60)
    resp.set_cookie('show_other_permissions', '', max_age=30*24*60*60)
    return resp


@manage.route('/permission/manage')
@login_required
@developer_required
def manage_permissions():
    resp = make_response(redirect(url_for('manage.permission')))
    resp.set_cookie('show_booking_permissions', '', max_age=30*24*60*60)
    resp.set_cookie('show_manage_permissions', '1', max_age=30*24*60*60)
    resp.set_cookie('show_develop_permissions', '', max_age=30*24*60*60)
    resp.set_cookie('show_other_permissions', '', max_age=30*24*60*60)
    return resp


@manage.route('/permission/develop')
@login_required
@developer_required
def develop_permissions():
    resp = make_response(redirect(url_for('manage.permission')))
    resp.set_cookie('show_booking_permissions', '', max_age=30*24*60*60)
    resp.set_cookie('show_manage_permissions', '', max_age=30*24*60*60)
    resp.set_cookie('show_develop_permissions', '1', max_age=30*24*60*60)
    resp.set_cookie('show_other_permissions', '', max_age=30*24*60*60)
    return resp


@manage.route('/permission/other')
@login_required
@developer_required
def other_permissions():
    resp = make_response(redirect(url_for('manage.permission')))
    resp.set_cookie('show_booking_permissions', '', max_age=30*24*60*60)
    resp.set_cookie('show_manage_permissions', '', max_age=30*24*60*60)
    resp.set_cookie('show_develop_permissions', '', max_age=30*24*60*60)
    resp.set_cookie('show_other_permissions', '1', max_age=30*24*60*60)
    return resp


@manage.route('/permission/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@developer_required
def edit_permission(id):
    permission = Permission.query.get_or_404(id)
    form = EditPermissionForm(permission=permission)
    if form.validate_on_submit():
        permission.name = form.name.data
        permission.check_overdue = form.check_overdue.data
        db.session.add(permission)
        flash(u'已更新权限：%s' % form.name.data, category='success')
        add_feed(user=current_user._get_current_object(), event=u'更新权限：%s' % form.name.data, category=u'manage')
        return redirect(request.args.get('next') or url_for('manage.permission'))
    form.name.data = permission.name
    form.check_overdue.data = permission.check_overdue
    return render_template('manage/edit_permission.html', form=form, permission=permission)


@manage.route('/permission/delete/<int:id>')
@login_required
@developer_required
def delete_permission(id):
    permission = Permission.query.get_or_404(id)
    if permission.roles.count():
        abort(403)
    db.session.delete(permission)
    flash(u'已删除权限：%s' % permission.name, category='success')
    add_feed(user=current_user._get_current_object(), event=u'删除权限：%s' % permission.name, category=u'manage')
    return redirect(request.args.get('next') or url_for('manage.permission'))


@manage.route('/analytics')
@login_required
@permission_required(u'管理')
def analytics():
    return render_template('manage/analytics.html', analytics_token=current_app.config['ANALYTICS_TOKEN'])


@manage.route('/feed')
@login_required
@developer_required
def feed():
    show_all_feeds = True
    show_auth_feeds = False
    show_booking_feeds = False
    show_rental_feeds = False
    show_punch_feeds = False
    show_group_feeds = False
    show_manage_feeds = False
    show_access_feeds = False
    show_email_feeds = False
    if current_user.is_authenticated:
        show_all_feeds = bool(request.cookies.get('show_all_feeds', '1'))
        show_auth_feeds = bool(request.cookies.get('show_auth_feeds', ''))
        show_booking_feeds = bool(request.cookies.get('show_booking_feeds', ''))
        show_rental_feeds = bool(request.cookies.get('show_rental_feeds', ''))
        show_punch_feeds = bool(request.cookies.get('show_punch_feeds', ''))
        show_group_feeds = bool(request.cookies.get('show_group_feeds', ''))
        show_manage_feeds = bool(request.cookies.get('show_manage_feeds', ''))
        show_access_feeds = bool(request.cookies.get('show_access_feeds', ''))
        show_email_feeds = bool(request.cookies.get('show_email_feeds', ''))
    if show_all_feeds:
        query = Feed.query\
            .order_by(Feed.timestamp.desc())
    if show_auth_feeds:
        query = Feed.query\
            .filter(Feed.category == u'auth')\
            .order_by(Feed.timestamp.desc())
    if show_booking_feeds:
        query = Feed.query\
            .filter(Feed.category == u'book')\
            .order_by(Feed.timestamp.desc())
    if show_rental_feeds:
        query = Feed.query\
            .filter(Feed.category == u'rental')\
            .order_by(Feed.timestamp.desc())
    if show_punch_feeds:
        query = Feed.query\
            .filter(Feed.category == u'punch')\
            .order_by(Feed.timestamp.desc())
    if show_group_feeds:
        query = Feed.query\
            .filter(Feed.category == u'group')\
            .order_by(Feed.timestamp.desc())
    if show_manage_feeds:
        query = Feed.query\
            .filter(Feed.category == u'manage')\
            .order_by(Feed.timestamp.desc())
    if show_access_feeds:
        query = Feed.query\
            .filter(Feed.category == u'access')\
            .order_by(Feed.timestamp.desc())
    if show_email_feeds:
        query = Feed.query\
            .filter(Feed.category == u'email')\
            .order_by(Feed.timestamp.desc())
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=current_app.config['RECORD_PER_PAGE'], error_out=False)
    feeds = pagination.items
    return render_template('manage/feed.html',
        show_all_feeds=show_all_feeds,
        show_auth_feeds=show_auth_feeds,
        show_booking_feeds=show_booking_feeds,
        show_rental_feeds=show_rental_feeds,
        show_punch_feeds=show_punch_feeds,
        show_group_feeds=show_group_feeds,
        show_manage_feeds=show_manage_feeds,
        show_access_feeds=show_access_feeds,
        show_email_feeds=show_email_feeds,
        pagination=pagination,
        feeds=feeds
    )


@manage.route('/feed/all')
@login_required
@developer_required
def all_feeds():
    resp = make_response(redirect(url_for('manage.feed')))
    resp.set_cookie('show_all_feeds', '1', max_age=30*24*60*60)
    resp.set_cookie('show_auth_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_booking_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_rental_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_punch_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_group_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_manage_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_access_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_email_feeds', '', max_age=30*24*60*60)
    return resp


@manage.route('/feed/auth')
@login_required
@developer_required
def auth_feeds():
    resp = make_response(redirect(url_for('manage.feed')))
    resp.set_cookie('show_all_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_auth_feeds', '1', max_age=30*24*60*60)
    resp.set_cookie('show_booking_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_rental_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_punch_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_group_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_manage_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_access_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_email_feeds', '', max_age=30*24*60*60)
    return resp


@manage.route('/feed/book')
@login_required
@developer_required
def booking_feeds():
    resp = make_response(redirect(url_for('manage.feed')))
    resp.set_cookie('show_all_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_auth_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_booking_feeds', '1', max_age=30*24*60*60)
    resp.set_cookie('show_rental_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_punch_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_group_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_manage_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_access_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_email_feeds', '', max_age=30*24*60*60)
    return resp


@manage.route('/feed/rental')
@login_required
@developer_required
def rental_feeds():
    resp = make_response(redirect(url_for('manage.feed')))
    resp.set_cookie('show_all_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_auth_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_booking_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_rental_feeds', '1', max_age=30*24*60*60)
    resp.set_cookie('show_punch_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_group_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_manage_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_access_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_email_feeds', '', max_age=30*24*60*60)
    return resp


@manage.route('/feed/punch')
@login_required
@developer_required
def punch_feeds():
    resp = make_response(redirect(url_for('manage.feed')))
    resp.set_cookie('show_all_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_auth_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_booking_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_rental_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_punch_feeds', '1', max_age=30*24*60*60)
    resp.set_cookie('show_group_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_manage_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_access_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_email_feeds', '', max_age=30*24*60*60)
    return resp


@manage.route('/feed/group')
@login_required
@developer_required
def group_feeds():
    resp = make_response(redirect(url_for('manage.feed')))
    resp.set_cookie('show_all_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_auth_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_booking_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_rental_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_punch_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_group_feeds', '1', max_age=30*24*60*60)
    resp.set_cookie('show_manage_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_access_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_email_feeds', '', max_age=30*24*60*60)
    return resp


@manage.route('/feed/manage')
@login_required
@developer_required
def manage_feeds():
    resp = make_response(redirect(url_for('manage.feed')))
    resp.set_cookie('show_all_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_auth_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_booking_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_rental_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_punch_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_group_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_manage_feeds', '1', max_age=30*24*60*60)
    resp.set_cookie('show_access_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_email_feeds', '', max_age=30*24*60*60)
    return resp


@manage.route('/feed/access')
@login_required
@developer_required
def access_feeds():
    resp = make_response(redirect(url_for('manage.feed')))
    resp.set_cookie('show_all_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_auth_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_booking_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_rental_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_punch_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_group_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_manage_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_access_feeds', '1', max_age=30*24*60*60)
    resp.set_cookie('show_email_feeds', '', max_age=30*24*60*60)
    return resp


@manage.route('/feed/email')
@login_required
@developer_required
def email_feeds():
    resp = make_response(redirect(url_for('manage.feed')))
    resp.set_cookie('show_all_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_auth_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_booking_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_rental_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_punch_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_group_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_manage_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_access_feeds', '', max_age=30*24*60*60)
    resp.set_cookie('show_email_feeds', '1', max_age=30*24*60*60)
    return resp


@manage.route('/suggest/user/')
@login_required
@permission_required(u'管理')
def suggest_user():
    users = []
    name_or_email = request.args.get('keyword')
    if name_or_email:
        users = User.query\
            .filter(User.created == True)\
            .filter(User.deleted == False)\
            .filter(or_(
                User.name.like('%' + name_or_email + '%'),
                User.email.like('%' + name_or_email + '%')
            ))\
            .order_by(User.last_seen_at.desc())\
            .limit(current_app.config['RECORD_PER_QUERY'])\
            .all()
    return jsonify({'results': [user.to_json_suggestion() for user in users if not user.is_superior_than(user=current_user._get_current_object())]})


@manage.route('/suggest/email')
@login_required
@permission_required(u'管理')
def suggest_email():
    users = []
    name_or_email = request.args.get('keyword')
    if name_or_email:
        users = User.query\
            .filter(User.created == True)\
            .filter(User.activated == True)\
            .filter(User.deleted == False)\
            .filter(or_(
                User.name.like('%' + name_or_email + '%'),
                User.email.like('%' + name_or_email + '%')
            ))\
            .order_by(User.last_seen_at.desc())\
            .limit(current_app.config['RECORD_PER_QUERY'])\
            .all()
    return jsonify({'results': [user.to_json_suggestion(suggest_email=True) for user in users if user.role.name != u'开发人员']})


@manage.route('/suggest/email/dev')
@login_required
@permission_required(u'管理')
def suggest_email_dev():
    users = []
    name_or_email = request.args.get('keyword')
    if name_or_email:
        users = User.query\
            .filter(User.created == True)\
            .filter(User.deleted == False)\
            .filter(or_(
                User.name.like('%' + name_or_email + '%'),
                User.email.like('%' + name_or_email + '%')
            ))\
            .order_by(User.last_seen_at.desc())\
            .limit(current_app.config['RECORD_PER_QUERY'])\
            .all()
    return jsonify({'results': [user.to_json_suggestion(suggest_email=True) for user in users if not user.is_superior_than(user=current_user._get_current_object())]})


@manage.route('/search/user')
@login_required
@permission_required(u'管理')
def search_user():
    users = []
    name_or_email = request.args.get('keyword')
    if name_or_email:
        users = User.query\
            .filter(User.created == True)\
            .filter(User.deleted == False)\
            .filter(or_(
                User.name.like('%' + name_or_email + '%'),
                User.email.like('%' + name_or_email + '%')
            ))\
            .order_by(User.last_seen_at.desc())\
            .limit(current_app.config['RECORD_PER_QUERY'])\
            .all()
    return jsonify({'results': [user.to_json_suggestion(include_url=True) for user in users if not user.is_superior_than(user=current_user._get_current_object())]})