# -*- coding: utf-8 -*-

from datetime import datetime, date, time
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from app.exceptions import ValidationError
from . import db, login_manager


class Permission:
    FORBIDDEN       = 0b00000000000000000000000000000000
    BOOK            = 0b00000000000000000000000000000001
    BOOK_VB         = 0b00000000000000000000000000000010
    BOOK_Y_GRE      = 0b00000000000000000000000000000100
    BOOK_VB_2       = 0b00000000000000000000000000001000
    BOOK_ANY        = 0b00000000000000000000000000010000
    MANAGE          = 0b00000000000000000000000000100000
    MANAGE_BOOKING  = 0b00000000000000000000000001000000
    MANAGE_RENTAL   = 0b00000000000000000000000010000000
    MANAGE_SCHEDULE = 0b00000000000000000000000100000000
    MANAGE_IPAD     = 0b00000000000000000000001000000000
    MANAGE_USER     = 0b00000000000000000000010000000000
    MANAGE_AUTH     = 0b00000000000000000000100000000000
    ADMINISTER      = 0b10000000000000000000000000000000


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = [
            (u'禁止预约', Permission.FORBIDDEN, ),
            (u'单VB', Permission.BOOK | Permission.BOOK_VB, ),
            (u'Y-GRE 普通', Permission.BOOK | Permission.BOOK_VB | Permission.BOOK_Y_GRE, ),
            (u'Y-GRE VB2', Permission.BOOK | Permission.BOOK_VB | Permission.BOOK_Y_GRE | Permission.BOOK_VB_2, ),
            (u'Y-GRE A权限', Permission.BOOK | Permission.BOOK_VB | Permission.BOOK_Y_GRE | Permission.BOOK_ANY, ),
            (u'预约协管员', Permission.MANAGE | Permission.MANAGE_BOOKING, ),
            (u'iPad借阅协管员', Permission.MANAGE | Permission.MANAGE_RENTAL, ),
            (u'时段协管员', Permission.MANAGE | Permission.MANAGE_SCHEDULE, ),
            (u'iPad内容协管员', Permission.MANAGE | Permission.MANAGE_IPAD, ),
            (u'用户协管员', Permission.MANAGE | Permission.MANAGE_USER, ),
            (u'志愿者', Permission.MANAGE | Permission.MANAGE_BOOKING | Permission.MANAGE_RENTAL | Permission.MANAGE_SCHEDULE | Permission.MANAGE_USER, ),
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


class Activation(db.Model):
    __tablename__ = 'activations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), index=True)
    activation_code_hash = db.Column(db.String(128))
    activated = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    vb_course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    y_gre_course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))

    @property
    def activation_code(self):
        raise AttributeError('activation_code is not a readable attribute')

    @activation_code.setter
    def activation_code(self, activation_code):
        self.activation_code_hash = generate_password_hash(activation_code)

    def verify_activation_code(self, activation_code):
        return check_password_hash(self.activation_code_hash, activation_code)

    @staticmethod
    def insert_activations():
        import xlrd
        data = xlrd.open_workbook('initial-activations.xlsx')
        table = data.sheet_by_index(0)
        activations = [table.row_values(row) for row in range(table.nrows) if row >= 1]
        for A in activations:
            if isinstance(A[1], float):
                A[1] = int(A[1])
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
                    y_gre_course_id=y_gre_course_id
                )
                db.session.add(activation)
                print u'导入激活信息', A[0], A[2], A[3], A[4]
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
                return User.query.filter_by(id=wb.user_id).first()

    @property
    def valid(self):
        return self.state.name == u'预约'

    @property
    def waited(self):
        return self.state.name == u'排队'

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


class RentalType(db.Model):
    __tablename__ = 'rental_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    rentals = db.relationship('Rental', backref='type', lazy='dynamic')

    @staticmethod
    def insert_rental_types():
        rental_types = [
            (u'借出', ),
            (u'回收', ),
        ]
        for RT in rental_types:
            rental_type = RentalType.query.filter_by(name=RT[0]).first()
            if rental_type is None:
                rental_type = RentalType(name=RT[0])
                db.session.add(rental_type)
                print u'导入借阅类型信息', RT[0]
        db.session.commit()

    def __repr__(self):
        return '<Rental Type %s>' % self.name


class Rental(db.Model):
    __tablename__ = 'rentals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    ipad_id = db.Column(db.Integer, db.ForeignKey('ipads.id'), primary_key=True)
    # booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('rental_types.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    agent_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Rental %r, %r>' % (self.user_id, self.ipad_id)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
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
    punches = db.relationship('Punch', backref='user', lazy='dynamic')

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
            return User.query.filter_by(id=wb.user_id).first()

    def booked(self, schedule):
        return (self.booked_schedules.filter_by(schedule_id=schedule.id).first() is not None) and\
            (Booking.query.filter_by(user_id=self.id, schedule_id=schedule.id).first().canceled is False)

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

    @staticmethod
    def insert_admin():
        admin = User.query.filter_by(email=current_app.config['YSYS_ADMIN']).first()
        if admin is None:
            admin = User(
                email=current_app.config['YSYS_ADMIN'],
                name=u'超级管理员',
                role_id=Role.query.filter_by(name=u'开发人员').first().id,
                password=current_app.config['YSYS_ADMIN_PASSWORD']
            )
            db.session.add(admin)
            db.session.commit()
            print u'初始化开发人员信息'

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
    schedules = db.relationship('Schedule', backref='period', lazy='dynamic')

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
                    type_id=CourseType.query.filter_by(name=P[3]).first().id
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
    booked_users = db.relationship(
        'Booking',
        foreign_keys=[Booking.schedule_id],
        backref=db.backref('schedule', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def publish(self):
        self.available = True
        db.session.add(self)

    def retract(self):
        self.available = False
        db.session.add(self)

    def increase_quota(self):
        self.quota += 1
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
            return User.query.filter_by(id=wb.user_id).first()

    def decrease_quota(self):
        if self.quota > 0:
            self.quota += -1
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
        start_time = datetime(self.date.year, self.date.month, self.date.day, self.period.start_time.hour, self.period.start_time.minute)
        end_time = datetime(self.date.year, self.date.month, self.date.day, self.period.end_time.hour, self.period.end_time.minute)
        return datetime.now() < start_time

    @property
    def started(self):
        start_time = datetime(self.date.year, self.date.month, self.date.day, self.period.start_time.hour, self.period.start_time.minute)
        end_time = datetime(self.date.year, self.date.month, self.date.day, self.period.end_time.hour, self.period.end_time.minute)
        return start_time <= datetime.now() and datetime.now() <= end_time

    @property
    def ended(self):
        start_time = datetime(self.date.year, self.date.month, self.date.day, self.period.start_time.hour, self.period.start_time.minute)
        end_time = datetime(self.date.year, self.date.month, self.date.day, self.period.end_time.hour, self.period.end_time.minute)
        return end_time < datetime.now()

    def is_booked_by(self, user):
        return (self.booked_users.filter_by(user_id=user.id).first() is not None) and\
            (Booking.query.filter_by(user_id=user.id, schedule_id=self.id).first().canceled == False)

    @property
    def valid_bookings(self):
        return Booking.query\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .filter(Schedule.id == self.id)\
            .filter(BookingState.name != u'取消')

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
            (u'64GB', ),
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
    ipad_id = db.Column(db.Integer, db.ForeignKey('ipads.id'), primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), primary_key=True)

    @staticmethod
    def insert_ipad_contents():
        import xlrd
        data = xlrd.open_workbook('initial-ipad-contents.xlsx')
        table = data.sheet_by_index(0)
        lesson_ids = [Lesson.query.filter_by(name=value).first().id for value in table.row_values(0) if Lesson.query.filter_by(name=value).first()]
        ipad_contents = [table.row_values(row) for row in range(table.nrows) if row >= 1]
        for PC in ipad_contents:
            P_id = iPad.query.filter_by(name=PC[0]).first().id
            for L_exist, L_id in zip(PC[1:], lesson_ids):
                if L_exist:
                    if iPadContent.query.filter_by(ipad_id=P_id, lesson_id=L_id).first() is None:
                        ipad_content = iPadContent(
                            ipad_id=P_id,
                            lesson_id=L_id,
                        )
                        db.session.add(ipad_content)
                        print u'导入iPad内容信息', PC[0], Lesson.query.filter_by(id=L_id).first().name
        db.session.commit()


class iPad(db.Model):
    __tablename__ = 'ipads'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    serial = db.Column(db.Unicode(12), unique=True, index=True)
    capacity_id = db.Column(db.Integer, db.ForeignKey('ipad_capacities.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    state_id = db.Column(db.Integer, db.ForeignKey('ipad_states.id'))
    lessons_included = db.relationship(
        'iPadContent',
        foreign_keys=[iPadContent.ipad_id],
        backref=db.backref('ipad', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    rented_users = db.relationship(
        'Rental',
        foreign_keys=[Rental.ipad_id],
        backref=db.backref('ipad', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @staticmethod
    def insert_ipads():
        import xlrd
        data = xlrd.open_workbook('initial-ipads.xlsx')
        table = data.sheet_by_index(0)
        ipads = [table.row_values(row) for row in range(table.nrows) if row >= 1]
        for P in ipads:
            if isinstance(P[3], float):
                P[3] = int(P[3])
            ipad = iPad.query.filter_by(name=P[0]).first()
            if ipad is None:
                ipad = iPad(
                    name=P[0],
                    serial=P[1],
                    capacity_id=iPadCapacity.query.filter_by(name=P[2]).first().id,
                    room_id=Room.query.filter_by(name=str(P[3])).first().id,
                    state_id=iPadState.query.filter_by(name=P[4]).first().id
                )
                print u'导入iPad信息', P[0], P[1], P[2], P[3], P[4]
                db.session.add(ipad)
        db.session.commit()

    def __repr__(self):
        return '<iPad %s, %s>' % (self.name, self.serial)


class AdjacentLesson(db.Model):
    __tablename__ = 'adjacent_lessons'
    previous_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), unique=True, primary_key=True)
    next_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), unique=True, primary_key=True)

    @staticmethod
    def insert_adjacent_lessons():
        adjacent_lessons = [
            (u'VB总论', u'L1', ),
            (u'L1', u'L2', ),
            (u'L2', u'L3', ),
            (u'L3', u'L4', ),
            (u'L4', u'L5', ),
            (u'L5', u'L6', ),
            (u'L6', u'L7', ),
            (u'L7', u'L8', ),
            (u'L8', u'L9', ),
            (u'GRE总论', u'1st', ),
            (u'1st', u'2nd', ),
            (u'2nd', u'3rd', ),
            (u'3rd', u'4th', ),
            (u'4th', u'5th', ),
            (u'5th', u'6th', ),
            (u'6th', u'7th', ),
            (u'7th', u'8th', ),
            (u'8th', u'9th', ),
            (u'9th', u'Test', ),
            (u'Test', u'AW总论', ),
        ]
        for AL in adjacent_lessons:
            adjacent_lesson = AdjacentLesson.query.filter_by(previous_id=Lesson.query.filter_by(name=AL[0]).first().id).first()
            if adjacent_lesson is None:
                adjacent_lesson = AdjacentLesson(
                    previous_id=Lesson.query.filter_by(name=AL[0]).first().id,
                    next_id=Lesson.query.filter_by(name=AL[1]).first().id
                )
                db.session.add(adjacent_lesson)
                print u'导入课程关联信息', AL[0], AL[1]
        db.session.commit()


class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    type_id = db.Column(db.Integer, db.ForeignKey('course_types.id'))
    sections = db.relationship('Section', backref='lesson', lazy='dynamic')
    punches = db.relationship('Punch', backref='lesson', lazy='dynamic')
    occupied_ipads = db.relationship(
        'iPadContent',
        foreign_keys=[iPadContent.lesson_id],
        backref=db.backref('lesson', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    previous = db.relationship(
        'AdjacentLesson',
        foreign_keys=[AdjacentLesson.next_id],
        backref=db.backref('next', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    next = db.relationship(
        'AdjacentLesson',
        foreign_keys=[AdjacentLesson.previous_id],
        backref=db.backref('previous', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @staticmethod
    def insert_lessons():
        lessons = [
            (u'VB总论', u'VB', ),
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


class AdjacentSection(db.Model):
    __tablename__ = 'adjacent_sections'
    previous_id = db.Column(db.Integer, db.ForeignKey('sections.id'), unique=True, primary_key=True)
    next_id = db.Column(db.Integer, db.ForeignKey('sections.id'), unique=True, primary_key=True)

    @staticmethod
    def insert_adjacent_sections():
        adjacent_sections = [
            (u'0.11', u'0.12', ),
            (u'0.12', u'0.13', ),
            (u'0.13', u'0.14', ),
            (u'0.14', u'0.21', ),
            (u'0.21', u'0.22', ),
            (u'0.22', u'0.23', ),
            (u'0.23', u'0.24', ),
            (u'0.24', u'0.31', ),
            (u'0.31', u'0.32', ),
            (u'0.32', u'0.33', ),
            (u'0.33', u'0.34', ),
            (u'0.34', u'0.41', ),
            (u'0.41', u'0.42', ),
            (u'0.42', u'0.43', ),
            (u'0.43', u'0.44', ),
            (u'0.44', u'1.1', ),
            (u'1.1', u'1.2', ),
            (u'1.2', u'1.3', ),
            (u'1.3', u'1.4', ),
            (u'1.4', u'1.5', ),
            (u'1.5', u'1.6', ),
            (u'1.6', u'1.7', ),
            (u'1.7', u'1.8', ),
            (u'1.8', u'2.1', ),
            (u'2.1', u'2.2', ),
            (u'2.2', u'2.3', ),
            (u'2.3', u'2.4', ),
            (u'2.4', u'2.5', ),
            (u'2.5', u'2.6', ),
            (u'2.6', u'2.7', ),
            (u'2.7', u'2.8', ),
            (u'2.8', u'3.1', ),
            (u'3.1', u'3.2', ),
            (u'3.2', u'3.3', ),
            (u'3.3', u'3.4', ),
            (u'3.4', u'3.5', ),
            (u'3.5', u'3.6', ),
            (u'3.6', u'3.7', ),
            (u'3.7', u'3.8', ),
            (u'3.8', u'4.1', ),
            (u'4.1', u'4.2', ),
            (u'4.2', u'4.3', ),
            (u'4.3', u'4.4', ),
            (u'4.4', u'4.5', ),
            (u'4.5', u'4.6', ),
            (u'4.6', u'4.7', ),
            (u'4.7', u'4.8', ),
            (u'4.8', u'5.1', ),
            (u'5.1', u'5.2', ),
            (u'5.2', u'5.3', ),
            (u'5.3', u'5.4', ),
            (u'5.4', u'5.5', ),
            (u'5.5', u'5.6', ),
            (u'5.6', u'5.7', ),
            (u'5.7', u'5.8', ),
            (u'5.8', u'6.1', ),
            (u'6.1', u'6.2', ),
            (u'6.2', u'6.3', ),
            (u'6.3', u'6.4', ),
            (u'6.4', u'6.5', ),
            (u'6.5', u'6.6', ),
            (u'6.6', u'6.7', ),
            (u'6.7', u'6.8', ),
            (u'6.8', u'7.1', ),
            (u'7.1', u'7.2', ),
            (u'7.2', u'7.3', ),
            (u'7.3', u'7.4', ),
            (u'7.4', u'7.5', ),
            (u'7.5', u'7.6', ),
            (u'7.6', u'7.7', ),
            (u'7.7', u'7.8', ),
            (u'7.8', u'8.1', ),
            (u'8.1', u'8.2', ),
            (u'8.2', u'8.3', ),
            (u'8.3', u'8.4', ),
            (u'8.4', u'8.5', ),
            (u'8.5', u'8.6', ),
            (u'8.6', u'8.7', ),
            (u'8.7', u'8.8', ),
            (u'8.8', u'8.9', ),
            (u'8.9', u'9.1', ),
            (u'9.1', u'9.2', ),
            (u'9.2', u'9.3', ),
            (u'9.3', u'9.4', ),
            (u'9.4', u'9.5', ),
            (u'9.5', u'9.6', ),
            (u'9.6', u'9.7', ),
            (u'9.7', u'9.8', ),
            (u'9.8', u'9.9', ),
            (u'GRE总论', u'1st', ),
            (u'1st', u'2nd', ),
            (u'2nd', u'3rd', ),
            (u'3rd', u'4th', ),
            (u'4th', u'5th', ),
            (u'5th', u'6th', ),
            (u'6th', u'7th', ),
            (u'7th', u'8th', ),
            (u'8th', u'9th', ),
            (u'9th', u'Test', ),
            (u'Test', u'AW总论', ),
        ]
        for AS in adjacent_sections:
            adjacent_section = AdjacentSection.query.filter_by(previous_id=Section.query.filter_by(name=AS[0]).first().id).first()
            if adjacent_section is None:
                adjacent_section = AdjacentSection(
                    previous_id=Section.query.filter_by(name=AS[0]).first().id,
                    next_id=Section.query.filter_by(name=AS[1]).first().id
                )
                db.session.add(adjacent_section)
                print u'导入节关联信息', AS[0], AS[1]
        db.session.commit()


class Section(db.Model):
    __tablename__ = 'sections'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'))
    punches = db.relationship('Punch', backref='section', lazy='dynamic')
    previous = db.relationship(
        'AdjacentSection',
        foreign_keys=[AdjacentSection.next_id],
        backref=db.backref('next', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    next = db.relationship(
        'AdjacentSection',
        foreign_keys=[AdjacentSection.previous_id],
        backref=db.backref('previous', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @staticmethod
    def insert_sections():
        sections = [
            (u'0.11', u'VB总论', ),
            (u'0.12', u'VB总论', ),
            (u'0.13', u'VB总论', ),
            (u'0.14', u'VB总论', ),
            (u'0.21', u'VB总论', ),
            (u'0.22', u'VB总论', ),
            (u'0.23', u'VB总论', ),
            (u'0.24', u'VB总论', ),
            (u'0.31', u'VB总论', ),
            (u'0.32', u'VB总论', ),
            (u'0.33', u'VB总论', ),
            (u'0.34', u'VB总论', ),
            (u'0.41', u'VB总论', ),
            (u'0.42', u'VB总论', ),
            (u'0.43', u'VB总论', ),
            (u'0.44', u'VB总论', ),
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
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    rental_id = db.Column(db.Integer, db.ForeignKey('rentals.id'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'))
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Punch %r, %r>' % (self.user.name, self.section.name)


class OperationType(db.Model):
    __tablename__ = 'operation_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    operations = db.relationship('Operation', backref='type', lazy='dynamic')

    @staticmethod
    def insert_operation_types():
        operation_types = [
            (u'增加', ),
            (u'修改', ),
            (u'删除', ),
        ]
        for OT in operation_types:
            operation_type = OperationType.query.filter_by(name=OT[0]).first()
            if operation_type is None:
                operation_type = OperationType(name=OT[0])
                db.session.add(operation_type)
                print u'导入操作类型信息', OT[0]
        db.session.commit()

    def __repr__(self):
        return '<Operation Type %s>' % self.name


class Operation(db.Model):
    __tablename__ = 'operations'
    id = db.Column(db.Integer, primary_key=True)
    log = db.Column(db.UnicodeText)
    operation_type_id = db.Column(db.Integer, db.ForeignKey('operation_types.id'))
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Operation Log %s>' % self.log
