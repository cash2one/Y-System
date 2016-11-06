# -*- coding: utf-8 -*-

from os import urandom
from datetime import datetime, date, time, timedelta
from sqlalchemy import or_
from base64 import urlsafe_b64encode
import hashlib
import json
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from app.exceptions import ValidationError
from . import db, login_manager


class Permission:
    FORBIDDEN       = 0b0000000000000000000000000000000
    BOOK            = 0b0000000000000000000000000000001
    BOOK_VB         = 0b0000000000000000000000000000010
    BOOK_Y_GRE      = 0b0000000000000000000000000000100
    BOOK_VB_2       = 0b0000000000000000000000000001000
    BOOK_ANY        = 0b0000000000000000000000000010000
    MANAGE          = 0b0000000000000000000000000100000
    # MANAGE_MESSAGE  = 0b0000000000000000000000000000000
    MANAGE_BOOKING  = 0b0000000000000000000000001000000
    MANAGE_RENTAL   = 0b0000000000000000000000010000000
    MANAGE_SCHEDULE = 0b0000000000000000000000100000000
    MANAGE_IPAD     = 0b0000000000000000000001000000000
    MANAGE_USER     = 0b0000000000000000000010000000000
    MANAGE_AUTH     = 0b0000000000000000000100000000000
    ADMINISTER      = 0b1000000000000000000000000000000


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')
    activations = db.relationship('Activation', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = [
            (u'禁止预约', Permission.FORBIDDEN, ),
            (u'单VB', Permission.BOOK | Permission.BOOK_VB, ),
            (u'Y-GRE 普通', Permission.BOOK | Permission.BOOK_VB | Permission.BOOK_Y_GRE, ),
            (u'Y-GRE VBx2', Permission.BOOK | Permission.BOOK_VB | Permission.BOOK_Y_GRE | Permission.BOOK_VB_2, ),
            (u'Y-GRE A权限', Permission.BOOK | Permission.BOOK_VB | Permission.BOOK_Y_GRE | Permission.BOOK_ANY, ),
            (u'协管员', Permission.MANAGE | Permission.MANAGE_BOOKING | Permission.MANAGE_RENTAL | Permission.MANAGE_SCHEDULE | Permission.MANAGE_IPAD | Permission.MANAGE_USER, ),
            (u'管理员', Permission.MANAGE | Permission.MANAGE_BOOKING | Permission.MANAGE_RENTAL | Permission.MANAGE_SCHEDULE | Permission.MANAGE_IPAD | Permission.MANAGE_USER | Permission.MANAGE_AUTH, ),
            (u'开发人员', 0xffffffff, ),
        ]
        for R in roles:
            role = Role.query.filter_by(name=R[0]).first()
            if role is None:
                role = Role(name=R[0], permissions=R[1])
                db.session.add(role)
                print u'导入用户角色信息', R[0]
        db.session.commit()

    def __repr__(self):
        return '<Role %s>' % self.name


class Registration(db.Model):
    __tablename__ = 'registrations'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), primary_key=True)


class CourseType(db.Model):
    __tablename__ = 'course_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    lessons = db.relationship('Lesson', backref='type', lazy='dynamic')
    courses = db.relationship('Course', backref='type', lazy='dynamic')
    periods = db.relationship('Period', backref='type', lazy='dynamic')

    @staticmethod
    def insert_course_types():
        course_types = [
            (u'VB', ),
            (u'Y-GRE', ),
        ]
        for CT in course_types:
            course_type = CourseType.query.filter_by(name=CT[0]).first()
            if course_type is None:
                course_type = CourseType(name=CT[0])
                db.session.add(course_type)
                print u'导入课程类型信息', CT[0]
        db.session.commit()

    def __repr__(self):
        return '<Course Type %s>' % self.name


class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    type_id = db.Column(db.Integer, db.ForeignKey('course_types.id'))
    registered_users = db.relationship(
        'Registration',
        foreign_keys=[Registration.course_id],
        backref=db.backref('course', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @staticmethod
    def insert_courses():
        import xlrd
        data = xlrd.open_workbook('initial-courses.xlsx')
        table = data.sheet_by_index(0)
        courses = [table.row_values(row) for row in range(table.nrows) if row >= 1]
        for C in courses:
            course = Course.query.filter_by(name=C[0]).first()
            if course is None:
                course = Course(
                    name=C[0],
                    type_id=CourseType.query.filter_by(name=C[1]).first().id
                )
                db.session.add(course)
                print u'导入课程信息', C[0], C[1]
        db.session.commit()

    def __repr__(self):
        return '<Course %s>' % self.name


class UserActivation(db.Model):
    __tablename__ = 'user_activations'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    activation_id = db.Column(db.Integer, db.ForeignKey('activations.id'), primary_key=True)


class Activation(db.Model):
    __tablename__ = 'activations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), index=True)
    activation_code_hash = db.Column(db.String(128))
    activated = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    vb_course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    y_gre_course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    inviter_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    initial_lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), default=1)
    initial_section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), default=1)
    deleted = db.Column(db.Boolean, default=False)
    activated_users = db.relationship(
        'UserActivation',
        foreign_keys=[UserActivation.activation_id],
        backref=db.backref('activation', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @property
    def activation_code(self):
        raise AttributeError('activation_code is not a readable attribute')

    @activation_code.setter
    def activation_code(self, activation_code):
        self.activation_code_hash = generate_password_hash(activation_code)

    def verify_activation_code(self, activation_code):
        return check_password_hash(self.activation_code_hash, activation_code)

    @property
    def vb_course(self):
        if self.vb_course_id:
            return Course.query.get(self.vb_course_id)

    @property
    def y_gre_course(self):
        if self.y_gre_course_id:
            return Course.query.get(self.y_gre_course_id)

    @property
    def activated_user(self):
        return self.activated_users.first()

    def safe_delete(self):
        self.deleted = True
        db.session.add(self)

    @staticmethod
    def insert_activations():
        import xlrd
        data = xlrd.open_workbook('initial-activations.xlsx')
        table = data.sheet_by_index(0)
        activations = [table.row_values(row) for row in range(table.nrows) if row >= 1]
        for A in activations:
            if isinstance(A[1], float):
                A[1] = int(A[1])
            if isinstance(A[6], float):
                A[6] = unicode(A[6])
            activation = Activation.query.filter_by(name=A[0]).first()
            if activation is None:
                if Course.query.filter_by(name=A[3]).first():
                    vb_course_id = Course.query.filter_by(name=A[3]).first().id
                else:
                    vb_course_id = None
                if Course.query.filter_by(name=A[4]).first():
                    y_gre_course_id = Course.query.filter_by(name=A[4]).first().id
                else:
                    y_gre_course_id = None
                activation = Activation(
                    name=A[0],
                    activation_code=str(A[1]),
                    role_id=Role.query.filter_by(name=A[2]).first().id,
                    vb_course_id=vb_course_id,
                    y_gre_course_id=y_gre_course_id,
                    inviter_id=User.query.get(1).id
                )
                if Section.query.filter_by(name=A[6]).first():
                    initial_section = Section.query.filter_by(name=A[6]).first()
                    activation.initial_lesson_id = initial_section.lesson.id
                    activation.initial_section_id = initial_section.id
                elif Lesson.query.filter_by(name=A[5]).first():
                    initial_lesson = Lesson.query.filter_by(name=A[5]).first()
                    activation.initial_lesson_id = initial_lesson.id
                    activation.initial_section_id = initial_lesson.first_section.id
                db.session.add(activation)
                print u'导入激活信息', A[0], A[2], A[3], A[4], A[5], A[6]
        db.session.commit()

    def __repr__(self):
        return '<Activation %s>' % self.name


class BookingState(db.Model):
    __tablename__ = 'booking_states'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    bookings = db.relationship('Booking', backref='state', lazy='dynamic')

    @staticmethod
    def insert_booking_states():
        booking_states = [
            (u'预约', ),
            (u'排队', ),
            (u'失效', ),
            (u'赴约', ),
            (u'迟到', ),
            (u'爽约', ),
            (u'取消', ),
        ]
        for BS in booking_states:
            booking_state = BookingState.query.filter_by(name=BS[0]).first()
            if booking_state is None:
                booking_state = BookingState(name=BS[0])
                db.session.add(booking_state)
                print u'导入预约状态信息', BS[0]
        db.session.commit()

    def __repr__(self):
        return '<Booking State %s>' % self.name


class Booking(db.Model):
    __tablename__ = 'bookings'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), primary_key=True)
    state_id = db.Column(db.Integer, db.ForeignKey('booking_states.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    booking_code = db.Column(db.String(128), unique=True, index=True)

    def __init__(self, **kwargs):
        super(Booking, self).__init__(**kwargs)
        booking_hash = generate_password_hash(str(datetime.utcnow()))
        self.booking_code = urlsafe_b64encode(booking_hash[-40:] + urandom(56))

    def ping(self):
        self.timestamp = datetime.utcnow()
        db.session.add(self)

    def set_state(self, state_name):
        self.state_id = BookingState.query.filter_by(name=state_name).first().id
        self.ping()
        db.session.add(self)
        if state_name == u'取消' and self.schedule.unstarted:
            wb = Booking.query\
                .join(BookingState, BookingState.id == Booking.state_id)\
                .join(Schedule, Schedule.id == Booking.schedule_id)\
                .filter(Schedule.id == self.schedule_id)\
                .filter(BookingState.name == u'排队')\
                .order_by(Booking.timestamp.desc())\
                .first()
            if wb:
                wb.state_id = BookingState.query.filter_by(name=u'预约').first().id
                wb.ping()
                db.session.add(wb)
                return User.query.get(wb.user_id)

    @property
    def valid(self):
        return self.state.name == u'预约'

    @property
    def waited(self):
        return self.state.name == u'排队'

    @property
    def queue_position(self):
        if not self.waited:
            return 0
        return Booking.query\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .filter(Schedule.id == self.schedule_id)\
            .filter(BookingState.name == u'排队')\
            .filter(Booking.timestamp < self.timestamp)\
            .count() + 1

    @property
    def invalid(self):
        return self.state.name == u'失效'

    @property
    def kept(self):
        return self.state.name == u'赴约'

    @property
    def late(self):
        return self.state.name == u'迟到'

    @property
    def missed(self):
        return self.state.name == u'爽约'

    @property
    def canceled(self):
        return self.state.name == u'取消'

    def to_json(self):
        booking_json = {
            'user': self.user.to_json(),
            'schedule': self.schedule.to_json(),
            'code': self.booking_code,
        }
        return booking_json


class Rental(db.Model):
    __tablename__ = 'rentals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ipad_id = db.Column(db.Integer, db.ForeignKey('ipads.id'))
    date = db.Column(db.Date, default=date.today())
    returned = db.Column(db.Boolean, default=False)
    rent_time = db.Column(db.DateTime, default=datetime.utcnow)
    rent_agent_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    return_time = db.Column(db.DateTime)
    return_agent_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def set_returned(self, return_agent_id, ipad_state=u'待机'):
        self.returned = True
        self.return_time = datetime.utcnow()
        self.return_agent_id = return_agent_id
        db.session.add(self)
        ipad = iPad.query.get(self.ipad_id)
        ipad.set_state(ipad_state)

    def __repr__(self):
        return '<Rental %r, %r, %r>' % (self.user.name, self.ipad.alias, self.ipad.serial)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Unicode(64), unique=True, index=True)
    name = db.Column(db.Unicode(64), index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    registered = db.relationship(
        'Registration',
        foreign_keys=[Registration.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    booked_schedules = db.relationship(
        'Booking',
        foreign_keys=[Booking.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    rented_ipads = db.relationship(
        'Rental',
        foreign_keys=[Rental.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    manage_ipads_rent = db.relationship(
        'Rental',
        foreign_keys=[Rental.user_id],
        backref=db.backref('rent_agent', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    manage_ipads_return = db.relationship(
        'Rental',
        foreign_keys=[Rental.user_id],
        backref=db.backref('return_agent', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    modified_schedules = db.relationship('Schedule', backref='modified_by', lazy='dynamic')
    modified_periods = db.relationship('Period', backref='modified_by', lazy='dynamic')
    modified_ipads = db.relationship('iPad', backref='modified_by', lazy='dynamic')
    punches = db.relationship('Punch', backref='user', lazy='dynamic')
    invitations = db.relationship('Activation', backref='inviter', lazy='dynamic')
    activation = db.relationship(
        'UserActivation',
        foreign_keys=[UserActivation.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def register(self, course):
        if not self.is_registering(course):
            r = Registration(user=self, course=course)
            db.session.add(r)

    def unregister(self, course):
        r = self.registered.filter_by(course_id=course.id).first()
        if r:
            db.session.delete(r)

    def is_registering(self, course):
        return self.registered.filter_by(course_id=course.id).first() is not None

    def add_user_activation(self, activation):
        ua = UserActivation(user_id=self.id, activation_id=activation.id)
        db.session.add(ua)

    def add_initial_punch(self, activation):
        initial_punch = Punch(user_id=self.id, lesson_id=activation.initial_lesson_id, section_id=activation.initial_section_id)
        db.session.add(initial_punch)

    @property
    def vb_course(self):
        return Course.query\
            .join(Registration, Registration.course_id == Course.id)\
            .join(CourseType, CourseType.id == Course.type_id)\
            .filter(Registration.user_id == self.id)\
            .filter(CourseType.name == u'VB')\
            .first()

    @property
    def y_gre_course(self):
        return Course.query\
            .join(Registration, Registration.course_id == Course.id)\
            .join(CourseType, CourseType.id == Course.type_id)\
            .filter(Registration.user_id == self.id)\
            .filter(CourseType.name == u'Y-GRE')\
            .first()

    def book(self, schedule, state_name):
        if schedule.available and not self.booked(schedule):
            b = Booking.query.filter_by(user_id=self.id, schedule_id=schedule.id).first()
            if b:
                b.state_id = BookingState.query.filter_by(name=state_name).first().id
                b.ping()
            else:
                b = Booking(user=self, schedule=schedule, state=BookingState.query.filter_by(name=state_name).first())
            db.session.add(b)

    def unbook(self, schedule):
        # mark booking state as canceled
        b =self.booked_schedules.filter_by(schedule_id=schedule.id).first()
        if b:
            b.state_id = BookingState.query.filter_by(name=u'取消').first().id
            db.session.add(b)
        # transfer to candidate if exist
        wb = Booking.query\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .filter(Schedule.id == schedule.id)\
            .filter(BookingState.name == u'排队')\
            .order_by(Booking.timestamp.desc())\
            .first()
        if wb:
            wb.state_id = BookingState.query.filter_by(name=u'预约').first().id
            wb.ping()
            db.session.add(wb)
            return User.query.get(wb.user_id)

    def miss(self, schedule):
        b =self.booked_schedules.filter_by(schedule_id=schedule.id).first()
        if b:
            b.state_id = BookingState.query.filter_by(name=u'爽约').first().id
            db.session.add(b)

    def booked(self, schedule):
        return (self.booked_schedules.filter_by(schedule_id=schedule.id).first() is not None) and\
            (Booking.query.filter_by(user_id=self.id, schedule_id=schedule.id).first().canceled is False)

    def booking(self, schedule):
        return Booking.query.filter_by(user_id=self.id, schedule_id=schedule.id).first()

    def booking_state(self, schedule):
        return BookingState.query\
            .join(Booking, Booking.state_id == BookingState.id)\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .filter(Schedule.id == schedule.id)\
            .filter(Booking.user_id == self.id)\
            .first()

    def booking_success(self, schedule):
        return BookingState.query\
            .join(Booking, Booking.state_id == BookingState.id)\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .filter(Schedule.id == schedule.id)\
            .filter(Booking.user_id == self.id)\
            .filter(BookingState.name == u'预约')\
            .first() is not None

    def booking_vb_same_day(self, schedule):
        valid_bookings = Booking.query\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .join(Period, Period.id == Schedule.period_id)\
            .join(CourseType, CourseType.id == Period.type_id)\
            .filter(Schedule.date == schedule.date)\
            .filter(Booking.user_id == self.id)\
            .filter(BookingState.name == u'预约')\
            .filter(CourseType.name == u'VB')\
            .count()
        waited_bookings = Booking.query\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .join(Period, Period.id == Schedule.period_id)\
            .join(CourseType, CourseType.id == Period.type_id)\
            .filter(Schedule.date == schedule.date)\
            .filter(Booking.user_id == self.id)\
            .filter(BookingState.name == u'排队')\
            .filter(CourseType.name == u'VB')\
            .count()
        return valid_bookings + waited_bookings

    def booking_y_gre_same_day(self, schedule):
        valid_bookings = Booking.query\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .join(Period, Period.id == Schedule.period_id)\
            .join(CourseType, CourseType.id == Period.type_id)\
            .filter(Schedule.date == schedule.date)\
            .filter(Booking.user_id == self.id)\
            .filter(BookingState.name == u'预约')\
            .filter(CourseType.name == u'Y-GRE')\
            .count()
        waited_bookings = Booking.query\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .join(Period, Period.id == Schedule.period_id)\
            .join(CourseType, CourseType.id == Period.type_id)\
            .filter(Schedule.date == schedule.date)\
            .filter(Booking.user_id == self.id)\
            .filter(BookingState.name == u'排队')\
            .filter(CourseType.name == u'Y-GRE')\
            .count()
        return valid_bookings + waited_bookings

    @property
    def valid_bookings(self):
        return Booking.query\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .filter(Booking.user_id == self.id)\
            .filter(BookingState.name == u'预约')

    @property
    def wait_bookings(self):
        return Booking.query\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .filter(Booking.user_id == self.id)\
            .filter(BookingState.name == u'排队')

    @property
    def invalid_bookings(self):
        return Booking.query\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .filter(Booking.user_id == self.id)\
            .filter(BookingState.name == u'失效')

    @property
    def keep_bookings(self):
        return Booking.query\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .filter(Booking.user_id == self.id)\
            .filter(BookingState.name == u'赴约')

    @property
    def late_bookings(self):
        return Booking.query\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .filter(Booking.user_id == self.id)\
            .filter(BookingState.name == u'迟到')

    @property
    def miss_bookings(self):
        return Booking.query\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .filter(Booking.user_id == self.id)\
            .filter(BookingState.name == u'爽约')

    @property
    def cancel_bookings(self):
        return Booking.query\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .filter(Booking.user_id == self.id)\
            .filter(BookingState.name == u'取消')

    @property
    def fitted_ipads(self):
        return iPad.query\
            .join(iPadState, iPadState.id == iPad.state_id)\
            .join(iPadContent, iPadContent.ipad_id == iPad.id)\
            .join(Punch, Punch.lesson_id == iPadContent.lesson_id)\
            .filter(Punch.user_id == self.id)\
            .filter(Punch.timestamp == self.last_punch.timestamp)\
            .filter(or_(
                iPadState.name == u'待机',
                iPadState.name == u'候补',
            ))\
            .filter(iPad.deleted == False)\
            .order_by(iPad.id.asc())

    @property
    def has_unreturned_ipads(self):
        return Rental.query.filter_by(user_id=self.id, returned=False).count() > 0

    @property
    def last_punch(self):
        return Punch.query\
            .filter_by(user_id=self.id)\
            .order_by(Punch.timestamp.desc())\
            .first()

    @property
    def invited_by(self):
        return Activation.query\
            .join(UserActivation, UserActivation.activation_id == Activation.id)\
            .join(User, User.id == UserActivation.user_id)\
            .filter(User.id == self.id)\
            .first()\
            .inviter

    def to_json(self):
        user_json = {
            'name': self.name,
            'email': self.email,
            'role': self.role.name,
            'last_punch': self.last_punch.to_json(),
            'last_seen': self.last_seen.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'url': url_for('main.profile_user', user_id=self.id),
        }
        return user_json

    def to_json_suggestion(self, suggest_email=False, include_url=False):
        if suggest_email:
            user_json_suggestion = {
                'title': self.email,
                'description': '%s[%s]' % (self.name, self.role.name),
            }
        else:
            user_json_suggestion = {
                'title': self.name,
                'description': self.email,
            }
        if include_url:
            user_json_suggestion['url'] = url_for('main.profile_user', user_id=self.id)
        return user_json_suggestion

    @staticmethod
    def insert_admin():
        admin = User.query.filter_by(email=current_app.config['YSYS_ADMIN']).first()
        if admin is None:
            admin = User(
                email=current_app.config['YSYS_ADMIN'],
                name=u'系统管理员',
                role_id=Role.query.filter_by(name=u'开发人员').first().id,
                password=current_app.config['YSYS_ADMIN_PASSWORD']
            )
            db.session.add(admin)
            db.session.commit()
            initial_punch = Punch(user_id=admin.id, lesson_id=1, section_id=1)
            db.session.add(initial_punch)
            print u'初始化系统管理员信息'

    def __repr__(self):
        return '<User %s, %r>' % (self.name, self.email)


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Period(db.Model):
    __tablename__ = 'periods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    type_id = db.Column(db.Integer, db.ForeignKey('course_types.id'))
    show = db.Column(db.Boolean, default=False)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    deleted = db.Column(db.Boolean, default=False)
    schedules = db.relationship('Schedule', backref='period', lazy='dynamic')

    def safe_delete(self, modified_by):
        self.last_modified = datetime.utcnow()
        self.last_modified_by = modified_by.id
        self.deleted = True
        db.session.add(self)

    @property
    def start_time_utc(self):
        hour = self.start_time.hour - current_app.config['UTC_OFFSET']
        while hour < 0:
            hour += 24
        while hour > 24:
            hour -= 24
        return time(hour, self.start_time.minute, self.start_time.second)

    @property
    def end_time_utc(self):
        hour = self.end_time.hour - current_app.config['UTC_OFFSET']
        while hour < 0:
            hour += 24
        while hour > 24:
            hour -= 24
        return time(hour, self.end_time.minute, self.end_time.second)

    @property
    def start_time_str(self):
        return self.start_time.strftime('%H:%M')

    @property
    def end_time_str(self):
        return self.end_time.strftime('%H:%M')

    @property
    def alias(self):
        return u'%s时段：%s - %s' % (self.type.name, self.start_time_str, self.end_time_str)

    @property
    def alias2(self):
        return u'%s - %s' % (self.start_time_str, self.end_time_str)

    @property
    def alias3(self):
        return u'%s：%s - %s' % (self.name, self.start_time_str, self.end_time_str)

    def to_json(self):
        period_json = {
            'name': self.name,
            'start_time': self.start_time_str,
            'end_time': self.end_time_str,
            'alias': self.alias,
            'alias2': self.alias2,
            'alias3': self.alias3,
            'type': self.type.show,
            'show': self.show,
            'last_modified_at': self.last_modified.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'last_modified_by': self.modified_by.name,
        }
        return period_json

    @staticmethod
    def insert_periods():
        periods = [
            (u'（淡季）VB上午', time(9, 0), time(15, 0), u'VB', ),
            (u'（淡季）VB下午', time(15, 0), time(21, 0), u'VB', ),
            (u'（旺季）VB时段1', time(8, 0), time(11, 30), u'VB', ),
            (u'（旺季）VB时段2', time(11, 30), time(15, 0), u'VB', ),
            (u'（旺季）VB时段3', time(15, 0), time(18, 30), u'VB', ),
            (u'（旺季）VB时段4', time(18, 30), time(22, 0), u'VB', ),
            (u'（淡季）Y-GRE上午', time(9, 0), time(15, 0), u'Y-GRE', ),
            (u'（淡季）Y-GRE下午', time(15, 0), time(21, 0), u'Y-GRE', ),
            (u'（旺季）Y-GRE上午', time(8, 0), time(15, 0), u'Y-GRE', ),
            (u'（旺季）Y-GRE下午', time(15, 0), time(22, 0), u'Y-GRE', ),
        ]
        for P in periods:
            period = Period.query.filter_by(name=P[0]).first()
            if period is None:
                period = Period(
                    name=P[0],
                    start_time=P[1],
                    end_time=P[2],
                    type_id=CourseType.query.filter_by(name=P[3]).first().id,
                    last_modified_by=User.query.get(1).id
                )
                db.session.add(period)
                print u'导入时段信息', P[0], P[1], P[2], P[3]
        db.session.commit()

    def __repr__(self):
        return '<Period %r>' % self.name


class Schedule(db.Model):
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, index=True)
    period_id = db.Column(db.Integer, db.ForeignKey('periods.id'))
    quota = db.Column(db.Integer, default=0)
    available = db.Column(db.Boolean, default=False)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    booked_users = db.relationship(
        'Booking',
        foreign_keys=[Booking.schedule_id],
        backref=db.backref('schedule', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def publish(self, modified_by):
        self.available = True
        self.last_modified = datetime.utcnow()
        self.last_modified_by = modified_by.id
        db.session.add(self)

    def retract(self, modified_by):
        self.available = False
        self.last_modified = datetime.utcnow()
        self.last_modified_by = modified_by.id
        db.session.add(self)

    def increase_quota(self, modified_by):
        self.quota += 1
        self.last_modified = datetime.utcnow()
        self.last_modified_by = modified_by.id
        db.session.add(self)
        wb = Booking.query\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .filter(Schedule.id == self.id)\
            .filter(BookingState.name == u'排队')\
            .order_by(Booking.timestamp.desc())\
            .first()
        if wb:
            wb.state_id = BookingState.query.filter_by(name=u'预约').first().id
            wb.ping()
            db.session.add(wb)
            return User.query.get(wb.user_id)

    def decrease_quota(self, modified_by):
        if self.quota > 0:
            self.quota += -1
            self.last_modified = datetime.utcnow()
            self.last_modified_by = modified_by.id
            db.session.add(self)

    @property
    def today(self):
        return self.date == date.today()

    @property
    def out_of_date(self):
        return self.date < date.today()

    @property
    def time_state(self):
        start_time = datetime(self.date.year, self.date.month, self.date.day, self.period.start_time.hour, self.period.start_time.minute)
        end_time = datetime(self.date.year, self.date.month, self.date.day, self.period.end_time.hour, self.period.end_time.minute)
        if datetime.now() < start_time:
            return u'未开始'
        if start_time <= datetime.now() and datetime.now() <= end_time:
            return u'进行中'
        if end_time < datetime.now():
            return u'已结束'

    @property
    def unstarted(self):
        return datetime.now() < datetime(self.date.year, self.date.month, self.date.day, self.period.start_time.hour, self.period.start_time.minute)

    def unstarted_n_min(self, n_min):
        return datetime.now() < datetime(self.date.year, self.date.month, self.date.day, self.period.start_time.hour, self.period.start_time.minute) + timedelta(minutes=n_min)

    @property
    def started(self):
        return datetime(self.date.year, self.date.month, self.date.day, self.period.start_time.hour, self.period.start_time.minute) <= datetime.now() and datetime.now() <= datetime(self.date.year, self.date.month, self.date.day, self.period.end_time.hour, self.period.end_time.minute)

    def started_n_min(self, n_min):
        return datetime(self.date.year, self.date.month, self.date.day, self.period.start_time.hour, self.period.start_time.minute) + timedelta(minutes=n_min) <= datetime.now() and datetime.now() <= datetime(self.date.year, self.date.month, self.date.day, self.period.end_time.hour, self.period.end_time.minute)

    @property
    def ended(self):
        return datetime(self.date.year, self.date.month, self.date.day, self.period.end_time.hour, self.period.end_time.minute) < datetime.now()

    def is_booked_by(self, user):
        return (self.booked_users.filter_by(user_id=user.id).first() is not None) and\
            (Booking.query.filter_by(user_id=user.id, schedule_id=self.id).first().canceled == False)

    @property
    def occupied_quota(self):
        return Booking.query\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .filter(Schedule.id == self.id)\
            .filter(or_(
                BookingState.name == u'预约',
                BookingState.name == u'排队',
                BookingState.name == u'赴约',
                BookingState.name == u'迟到'
            ))\
            .count()

    @property
    def full(self):
        return self.occupied_quota >= self.quota

    def to_json(self):
        schedule_json = {
            'date': self.date,
            'period': self.period.to_json(),
            'quota': self.quota,
            'available': self.available,
            'last_modified_at': self.last_modified.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'last_modified_by': self.modified_by.name,
        }
        return schedule_json

    def __repr__(self):
        return '<Schedule %r>' % self.date


class iPadCapacity(db.Model):
    __tablename__ = 'ipad_capacities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    ipads = db.relationship('iPad', backref='capacity', lazy='dynamic')

    @staticmethod
    def insert_ipad_capacities():
        ipad_capacities = [
            (u'16GB', ),
            (u'32GB', ),
            (u'64GB', ),
            (u'128GB', ),
        ]
        for PC in ipad_capacities:
            ipad_capacity = iPadCapacity.query.filter_by(name=PC[0]).first()
            if ipad_capacity is None:
                ipad_capacity = iPadCapacity(name=PC[0])
                db.session.add(ipad_capacity)
                print u'导入iPad容量信息', PC[0]
        db.session.commit()

    def __repr__(self):
        return '<iPad Capacity %s>' % self.name


class iPadState(db.Model):
    __tablename__ = 'ipad_states'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    ipads = db.relationship('iPad', backref='state', lazy='dynamic')

    @staticmethod
    def insert_ipad_states():
        ipad_states = [
            (u'待机', ),
            (u'借出', ),
            (u'候补', ),
            (u'维护', ),
            (u'充电', ),
            (u'退役', ),
        ]
        for PS in ipad_states:
            ipad_state = iPadState.query.filter_by(name=PS[0]).first()
            if ipad_state is None:
                ipad_state = iPadState(name=PS[0])
                db.session.add(ipad_state)
                print u'导入iPad状态信息', PS[0]
        db.session.commit()

    def __repr__(self):
        return '<iPad State %s>' % self.name


class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    ipads = db.relationship('iPad', backref='room', lazy='dynamic')

    @staticmethod
    def insert_rooms():
        rooms = [
            (u'1103', ),
            (u'1707', ),
        ]
        for R in rooms:
            room = Room.query.filter_by(name=R[0]).first()
            if room is None:
                room = Room(name=R[0])
                db.session.add(room)
                print u'导入房间信息', R[0]
        db.session.commit()

    def __repr__(self):
        return '<Room %s>' % self.name


class iPadContent(db.Model):
    __tablename__ = 'ipad_contents'
    ipad_id = db.Column(db.Integer, db.ForeignKey('ipads.id'), primary_key=True, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), primary_key=True, index=True)

    @staticmethod
    def insert_ipad_contents():
        import xlrd
        data = xlrd.open_workbook('initial-ipad-contents.xlsx')
        table = data.sheet_by_index(0)
        lesson_ids = [Lesson.query.filter_by(name=value).first().id for value in table.row_values(0) if Lesson.query.filter_by(name=value).first()]
        ipad_contents = [table.row_values(row) for row in range(table.nrows) if row >= 1]
        for PC in ipad_contents:
            P_id = iPad.query.filter_by(alias=PC[0]).first().id
            for L_exist, L_id in zip(PC[1:], lesson_ids):
                if L_exist:
                    if iPadContent.query.filter_by(ipad_id=P_id, lesson_id=L_id).first() is None:
                        ipad_content = iPadContent(
                            ipad_id=P_id,
                            lesson_id=L_id,
                        )
                        db.session.add(ipad_content)
                        print u'导入iPad内容信息', PC[0], Lesson.query.get(L_id).name
        db.session.commit()
        ipad_contents = iPadContentJSON.query.get(1)
        if ipad_contents is not None:
            if ipad_contents.out_of_date:
                iPadContentJSON.update()
                db.session.commit()
        else:
            iPadContentJSON.update()
            db.session.commit()
        print u'将iPad内容信息转换成JSON格式'


class iPadContentJSON(db.Model):
    __tablename__ = 'ipad_contents_json'
    id = db.Column(db.Integer, primary_key=True)
    json_string = db.Column(db.UnicodeText)
    out_of_date = db.Column(db.Boolean, default=True)

    @staticmethod
    def update():
        json_string = unicode(json.dumps([{'alias': ipad.alias, 'lessons': [(iPadContent.query.filter_by(ipad_id=ipad.id, lesson_id=lesson.id).first() is not None) for lesson in Lesson.query.order_by(Lesson.id.asc()).all()]} for ipad in iPad.query.filter_by(deleted=False).order_by(iPad.alias.asc()).all()]))
        pc_json = iPadContentJSON.query.get(1)
        if pc_json is not None:
            pc_json.json_string = json_string
            pc_json.out_of_date = False
        else:
            pc_json = iPadContentJSON(json_string=json_string, out_of_date=False)
        db.session.add(pc_json)

    @staticmethod
    def mark_out_of_date():
        pc_json = iPadContentJSON.query.get(1)
        if pc_json is not None:
            pc_json.out_of_date = True
        else:
            pc_json = iPadContentJSON(out_of_date=True)
        db.session.add(pc_json)

    def __repr__(self):
        return '<iPadContentJSON %s>' % self.json_string


class iPad(db.Model):
    __tablename__ = 'ipads'
    id = db.Column(db.Integer, primary_key=True)
    serial = db.Column(db.Unicode(12), unique=True, index=True)
    alias = db.Column(db.Unicode(64), index=True)
    capacity_id = db.Column(db.Integer, db.ForeignKey('ipad_capacities.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    state_id = db.Column(db.Integer, db.ForeignKey('ipad_states.id'))
    last_modified = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    deleted = db.Column(db.Boolean, default=False)
    lessons_included = db.relationship(
        'iPadContent',
        foreign_keys=[iPadContent.ipad_id],
        backref=db.backref('ipad', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    rentals = db.relationship('Rental', backref='ipad', lazy='dynamic')

    def safe_delete(self, modified_by):
        self.last_modified = datetime.utcnow()
        self.last_modified_by = modified_by.id
        self.deleted = True
        db.session.add(self)

    def set_state(self, state_name):
        self.state_id = iPadState.query.filter_by(name=state_name).first().id
        db.session.add(self)

    def add_lesson(self, lesson_id):
        if not self.has_lesson(lesson_id):
            pc = iPadContent(ipad_id=self.id, lesson_id=lesson_id)
            db.session.add(pc)

    def remove_lesson(self, lesson_id):
        if self.has_lesson(lesson_id):
            pc = iPadContent.query.filter_by(ipad_id=self.id, lesson_id=lesson_id).first()
            db.session.delete(pc)

    def has_lesson(self, lesson_id):
        return iPadContent.query.filter_by(ipad_id=self.id, lesson_id=lesson_id).first() is not None

    @property
    def has_lessons(self):
        return Lesson.query\
            .join(iPadContent, iPadContent.lesson_id == Lesson.id)\
            .filter(iPadContent.ipad_id == self.id)\
            .order_by(Lesson.id.asc())

    @property
    def has_vb_lessons(self):
        return Lesson.query\
            .join(iPadContent, iPadContent.lesson_id == Lesson.id)\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(iPadContent.ipad_id == self.id)\
            .filter(CourseType.name == u'VB')\
            .order_by(Lesson.id.asc())

    @property
    def has_y_gre_lessons(self):
        return Lesson.query\
            .join(iPadContent, iPadContent.lesson_id == Lesson.id)\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(iPadContent.ipad_id == self.id)\
            .filter(CourseType.name == u'Y-GRE')\
            .order_by(Lesson.id.asc())

    @property
    def vb_lesson_ids_included(self):
        vb_lessons = self.has_vb_lessons
        return [vb_lesson.id for vb_lesson in vb_lessons]

    @property
    def y_gre_lesson_ids_included(self):
        y_gre_lessons = self.has_y_gre_lessons
        return [y_gre_lesson.id for y_gre_lesson in y_gre_lessons]

    @property
    def now_rented_by(self):
        return User.query\
            .join(Rental, Rental.user_id == User.id)\
            .join(iPad, iPad.id == Rental.ipad_id)\
            .filter(Rental.returned == False)\
            .filter(iPad.id == self.id)\
            .first()

    def to_json(self):
        ipad_json = {
            'serial': self.serial,
            'alias': self.alias,
            'capacity': self.capacity.name,
            'state': self.state.name,
            'last_modified_at': self.last_modified.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'last_modified_by': self.modified_by.name,
        }
        if self.state.name == u'借出':
            ipad_json['now_rented_by'] = self.now_rented_by.to_json()
        return ipad_json

    @staticmethod
    def insert_ipads():
        import xlrd
        data = xlrd.open_workbook('initial-ipads.xlsx')
        table = data.sheet_by_index(0)
        ipads = [table.row_values(row) for row in range(table.nrows) if row >= 1]
        for P in ipads:
            if isinstance(P[3], float):
                P[3] = int(P[3])
            ipad = iPad.query.filter_by(serial=P[1]).first()
            if ipad is None:
                ipad = iPad(
                    serial=P[1].upper(),
                    alias=P[0],
                    capacity_id=iPadCapacity.query.filter_by(name=P[2]).first().id,
                    room_id=Room.query.filter_by(name=unicode(str(P[3]))).first().id,
                    state_id=iPadState.query.filter_by(name=P[4]).first().id,
                    last_modified_by=User.query.get(1).id
                )
                print u'导入iPad信息', P[1], P[0], P[2], P[3], P[4]
                db.session.add(ipad)
        db.session.commit()

    def __repr__(self):
        return '<iPad %s, %s>' % (self.alias, self.serial)


class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    type_id = db.Column(db.Integer, db.ForeignKey('course_types.id'))
    sections = db.relationship('Section', backref='lesson', lazy='dynamic')
    punches = db.relationship('Punch', backref='lesson', lazy='dynamic')
    activations = db.relationship('Activation', backref='initial_lesson', lazy='dynamic')
    occupied_ipads = db.relationship(
        'iPadContent',
        foreign_keys=[iPadContent.lesson_id],
        backref=db.backref('lesson', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @property
    def first_section(self):
        return Section.query\
            .join(Lesson, Lesson.id == Section.lesson_id)\
            .filter(Section.id == self.id)\
            .order_by(Section.id.asc())\
            .first()

    @staticmethod
    def insert_lessons():
        lessons = [
            (u'总论', u'VB', ),
            (u'L1', u'VB', ),
            (u'L2', u'VB', ),
            (u'L3', u'VB', ),
            (u'L4', u'VB', ),
            (u'L5', u'VB', ),
            (u'L6', u'VB', ),
            (u'L7', u'VB', ),
            (u'L8', u'VB', ),
            (u'L9', u'VB', ),
            (u'GRE总论', u'Y-GRE', ),
            (u'1st', u'Y-GRE', ),
            (u'2nd', u'Y-GRE', ),
            (u'3rd', u'Y-GRE', ),
            (u'4th', u'Y-GRE', ),
            (u'5th', u'Y-GRE', ),
            (u'6th', u'Y-GRE', ),
            (u'7th', u'Y-GRE', ),
            (u'8th', u'Y-GRE', ),
            (u'9th', u'Y-GRE', ),
            (u'Test', u'Y-GRE', ),
            (u'AW总论', u'Y-GRE', ),
        ]
        for L in lessons:
            lesson = Lesson.query.filter_by(name=L[0]).first()
            if lesson is None:
                lesson = Lesson(
                    name=L[0],
                    type_id=CourseType.query.filter_by(name=L[1]).first().id
                )
                db.session.add(lesson)
                print u'导入课程信息', L[0], L[1]
        db.session.commit()

    def __repr__(self):
        return '<Lesson %s>' % self.name


class Section(db.Model):
    __tablename__ = 'sections'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'))
    punches = db.relationship('Punch', backref='section', lazy='dynamic')
    activations = db.relationship('Activation', backref='initial_section', lazy='dynamic')

    @staticmethod
    def insert_sections():
        sections = [
            (u'0.11', u'总论', ),
            (u'0.12', u'总论', ),
            (u'0.13', u'总论', ),
            (u'0.14', u'总论', ),
            (u'0.21', u'总论', ),
            (u'0.22', u'总论', ),
            (u'0.23', u'总论', ),
            (u'0.24', u'总论', ),
            (u'0.31', u'总论', ),
            (u'0.32', u'总论', ),
            (u'0.33', u'总论', ),
            (u'0.34', u'总论', ),
            (u'0.41', u'总论', ),
            (u'0.42', u'总论', ),
            (u'0.43', u'总论', ),
            (u'0.44', u'总论', ),
            (u'1.1', u'L1', ),
            (u'1.2', u'L1', ),
            (u'1.3', u'L1', ),
            (u'1.4', u'L1', ),
            (u'1.5', u'L1', ),
            (u'1.6', u'L1', ),
            (u'1.7', u'L1', ),
            (u'1.8', u'L1', ),
            (u'2.1', u'L2', ),
            (u'2.2', u'L2', ),
            (u'2.3', u'L2', ),
            (u'2.4', u'L2', ),
            (u'2.5', u'L2', ),
            (u'2.6', u'L2', ),
            (u'2.7', u'L2', ),
            (u'2.8', u'L2', ),
            (u'3.1', u'L3', ),
            (u'3.2', u'L3', ),
            (u'3.3', u'L3', ),
            (u'3.4', u'L3', ),
            (u'3.5', u'L3', ),
            (u'3.6', u'L3', ),
            (u'3.7', u'L3', ),
            (u'3.8', u'L3', ),
            (u'4.1', u'L4', ),
            (u'4.2', u'L4', ),
            (u'4.3', u'L4', ),
            (u'4.4', u'L4', ),
            (u'4.5', u'L4', ),
            (u'4.6', u'L4', ),
            (u'4.7', u'L4', ),
            (u'4.8', u'L4', ),
            (u'5.1', u'L5', ),
            (u'5.2', u'L5', ),
            (u'5.3', u'L5', ),
            (u'5.4', u'L5', ),
            (u'5.5', u'L5', ),
            (u'5.6', u'L5', ),
            (u'5.7', u'L5', ),
            (u'5.8', u'L5', ),
            (u'6.1', u'L6', ),
            (u'6.2', u'L6', ),
            (u'6.3', u'L6', ),
            (u'6.4', u'L6', ),
            (u'6.5', u'L6', ),
            (u'6.6', u'L6', ),
            (u'6.7', u'L6', ),
            (u'6.8', u'L6', ),
            (u'7.1', u'L7', ),
            (u'7.2', u'L7', ),
            (u'7.3', u'L7', ),
            (u'7.4', u'L7', ),
            (u'7.5', u'L7', ),
            (u'7.6', u'L7', ),
            (u'7.7', u'L7', ),
            (u'7.8', u'L7', ),
            (u'8.1', u'L8', ),
            (u'8.2', u'L8', ),
            (u'8.3', u'L8', ),
            (u'8.4', u'L8', ),
            (u'8.5', u'L8', ),
            (u'8.6', u'L8', ),
            (u'8.7', u'L8', ),
            (u'8.8', u'L8', ),
            (u'8.9', u'L8', ),
            (u'9.1', u'L9', ),
            (u'9.2', u'L9', ),
            (u'9.3', u'L9', ),
            (u'9.4', u'L9', ),
            (u'9.5', u'L9', ),
            (u'9.6', u'L9', ),
            (u'9.7', u'L9', ),
            (u'9.8', u'L9', ),
            (u'9.9', u'L9', ),
            (u'GRE总论', u'GRE总论', ),
            (u'1st', u'1st', ),
            (u'2nd', u'2nd', ),
            (u'3rd', u'3rd', ),
            (u'4th', u'4th', ),
            (u'5th', u'5th', ),
            (u'6th', u'6th', ),
            (u'7th', u'7th', ),
            (u'8th', u'8th', ),
            (u'9th', u'9th', ),
            (u'Test', u'Test', ),
            (u'AW总论', u'AW总论', ),
        ]
        for S in sections:
            section = Section.query.filter_by(name=S[0]).first()
            if section is None:
                section = Section(
                    name=S[0],
                    lesson_id=Lesson.query.filter_by(name=S[1]).first().id
                )
                db.session.add(section)
                print u'导入节信息', S[0], S[1]
        db.session.commit()

    def __repr__(self):
        return '<Section %s>' % self.name


class Punch(db.Model):
    __tablename__ = 'punches'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def alias(self):
        return u'%s - %s' % (self.lesson.name, self.section.name)

    @property
    def alias2(self):
        return u'%s - %s - %s' % (self.lesson.type.name, self.lesson.name, self.section.name)

    def to_json(self):
        punch_json = {
            'user': self.user.name,
            'course_type': self.lesson.type.name,
            'lesson': self.lesson.name,
            'section': self.section.name,
            'alias': self.alias,
            'alias2': self.alias2,
            'punched_at': self.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
        return punch_json

    def __repr__(self):
        return '<Punch %r, %r>' % (self.user.name, self.section.name)

