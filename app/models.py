# -*- coding: utf-8 -*-

from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from app.exceptions import ValidationError
from . import db, login_manager


class Permission:
    FORBIDDEN        = 0b00000000000000000000000000000000
    BOOK_VB_1        = 0b00000000000000000000000000000001
    BOOK_VB_2        = 0b00000000000000000000000000000010
    BOOK_VB_A        = 0b00000000000000000000000000000100
    BOOK_Y_GRE_1     = 0b00000000000000000000000000001000
    BOOK_Y_GRE_A     = 0b00000000000000000000000000010000
    MODERATE_BOOKING = 0b00000000000000000000000000100000
    MODERATE_RENTAL  = 0b00000000000000000000000001000000
    MODERATE_PERIOD  = 0b00000000000000000000000010000000
    MODERATE_IPAD    = 0b00000000000000000000000100000000
    MODERATE_USER    = 0b00000000000000000000001000000000
    MODERATE_AUTH    = 0b00000000000000000000010000000000
    ADMINISTER       = 0b10000000000000000000000000000000


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
            (u'单VB', Permission.FORBIDDEN | Permission.BOOK_VB_1, ),
            (u'Y-GRE 普通', Permission.FORBIDDEN | Permission.BOOK_VB_1 | Permission.BOOK_Y_GRE_1, ),
            (u'Y-GRE VB2', Permission.FORBIDDEN | Permission.BOOK_VB_2 | Permission.BOOK_Y_GRE_1, ),
            (u'Y-GRE A权限', Permission.FORBIDDEN | Permission.BOOK_VB_A | Permission.BOOK_Y_GRE_A, ),
            (u'预约协管员', Permission.FORBIDDEN | Permission.MODERATE_BOOKING, ),
            (u'iPad借阅协管员', Permission.FORBIDDEN | Permission.MODERATE_RENTAL, ),
            (u'时段协管员', Permission.FORBIDDEN | Permission.MODERATE_PERIOD, ),
            (u'iPad内容协管员', Permission.FORBIDDEN | Permission.MODERATE_IPAD, ),
            (u'用户协管员', Permission.FORBIDDEN | Permission.MODERATE_USER, ),
            (u'志愿者', Permission.FORBIDDEN | Permission.MODERATE_BOOKING | Permission.MODERATE_RENTAL | Permission.MODERATE_PERIOD | Permission.MODERATE_USER, ),
            (u'管理员', Permission.FORBIDDEN | Permission.MODERATE_BOOKING | Permission.MODERATE_RENTAL | Permission.MODERATE_PERIOD | Permission.MODERATE_IPAD | Permission.MODERATE_USER | Permission.MODERATE_AUTH, ),
            (u'开发人员', 0xffffffff, ),
        ]
        for r in roles:
            role = Role.query.filter_by(name=r[0]).first()
            if role is None:
                role = Role(name=r[0], permissions=r[1])
                db.session.add(role)
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
        for ct in course_types:
            course_type = CourseType.query.filter_by(name=ct[0]).first()
            if course_type is None:
                course_type = CourseType(name=ct[0])
                db.session.add(course_type)
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
        for c in courses:
            course = Course.query.filter_by(name=c[0]).first()
            if course is None:
                course = Course(
                    name=c[0],
                    type_id=CourseType.query.filter_by(name=c[1]).first().id
                )
                print u'导入班级信息', c[0], c[1]
                db.session.add(course)
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
        for a in activations:
            if isinstance(a[1], float):
                a[1] = int(a[1])
            activation = Activation.query.filter_by(name=a[0]).first()
            if activation is None:
                if Course.query.filter_by(name=a[3]).first():
                    vb_course_id = Course.query.filter_by(name=a[3]).first().id
                else:
                    vb_course_id = None
                if Course.query.filter_by(name=a[4]).first():
                    y_gre_course_id = Course.query.filter_by(name=a[4]).first().id
                else:
                    y_gre_course_id = None
                activation = Activation(
                    name=a[0],
                    activation_code=str(a[1]),
                    role_id=Role.query.filter_by(name=a[2]).first().id,
                    vb_course_id=vb_course_id,
                    y_gre_course_id=y_gre_course_id
                )
                print u'导入激活信息', a[0], a[2], a[3], a[4]
                db.session.add(activation)
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
            (u'赴约', ),
            (u'迟到', ),
            (u'爽约', ),
            (u'取消', ),
        ]
        for bs in booking_states:
            booking_state = BookingState.query.filter_by(name=bs[0]).first()
            if booking_state is None:
                booking_state = BookingState(name=bs[0])
                db.session.add(booking_state)
        db.session.commit()

    def __repr__(self):
        return '<Booking State %s>' % self.name


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey('periods.id'), primary_key=True)
    booking_state_id = db.Column(db.Integer, db.ForeignKey('booking_states.id'))

    def __repr__(self):
        return '<Booking %r, %r>' % (self.user_id, self.period_id)


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
        for rt in rental_types:
            rental_type = RentalType.query.filter_by(name=rt[0]).first()
            if rental_type is None:
                rental_type = RentalType(name=rt[0])
                db.session.add(rental_type)
        db.session.commit()

    def __repr__(self):
        return '<Rental Type %s>' % self.name


class Rental(db.Model):
    __tablename__ = 'rentals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    ipad_id = db.Column(db.Integer, db.ForeignKey('ipads.id'), primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    rental_type_id = db.Column(db.Integer, db.ForeignKey('rental_types.id'))
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
    booked_periods = db.relationship(
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
        return Course.query.join(Registration, Registration.course_id == Course.id)\
            .filter(Registration.user_id == self.id)\
            .join(CourseType, CourseType.id == Course.type_id)\
            .filter(CourseType.name == u'VB').first()

    @property
    def y_gre_course(self):
        return Course.query.join(Registration, Registration.course_id == Course.id)\
            .filter(Registration.user_id == self.id)\
            .join(CourseType, CourseType.id == Course.type_id)\
            .filter(CourseType.name == u'Y-GRE').first()


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
    date = db.Column(db.Date, index=True)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    availabe = db.Column(db.Boolean, default=False)
    type_id = db.Column(db.Integer, db.ForeignKey('course_types.id'))
    booked_users = db.relationship(
        'Booking',
        foreign_keys=[Booking.period_id],
        backref=db.backref('period', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return '<Period %r, %r>' % (self.start_time, self.end_time)


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
        for ic in ipad_capacities:
            ipad_capacity = iPadCapacity.query.filter_by(name=ic[0]).first()
            if ipad_capacity is None:
                ipad_capacity = iPadCapacity(name=ic[0])
                db.session.add(ipad_capacity)
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
            (u'维护', ),
            (u'退役', ),
        ]
        for s in ipad_states:
            ipad_state = iPadState.query.filter_by(name=s[0]).first()
            if ipad_state is None:
                ipad_state = iPadState(name=s[0])
                db.session.add(ipad_state)
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
        for r in rooms:
            room = Room.query.filter_by(name=r[0]).first()
            if room is None:
                room = Room(name=r[0])
                db.session.add(room)
        db.session.commit()

    def __repr__(self):
        return '<Room %s>' % self.name


class iPadContent(db.Model):
    __tablename__ = 'ipad_contents'
    ipad_id = db.Column(db.Integer, db.ForeignKey('ipads.id'), primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), primary_key=True)


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
        for p in ipads:
            if isinstance(p[3], float):
                p[3] = int(p[3])
            ipad = iPad.query.filter_by(name=p[0]).first()
            if ipad is None:
                ipad = iPad(
                    name=p[0],
                    serial=p[1],
                    capacity_id=iPadCapacity.query.filter_by(name=p[2]).first().id,
                    room_id=Room.query.filter_by(name=str(p[3])).first().id,
                    state_id=iPadState.query.filter_by(name=u'待机').first().id
                )
                print u'导入iPad信息', p[0], p[1], p[2], p[3]
                db.session.add(ipad)
        db.session.commit()

    def __repr__(self):
        return '<iPad %s, %s>' % (self.name, self.serial)


class AdjacentLesson(db.Model):
    __tablename__ = 'adjacent_lessons'
    previous_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), unique=True, primary_key=True)
    next_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), unique=True, primary_key=True)


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
        for l in lessons:
            lesson = Lesson.query.filter_by(name=l[0]).first()
            if lesson is None:
                lesson = Lesson(name=l[0], type_id=CourseType.query.filter_by(name=l[1]).first().id)
                db.session.add(lesson)
        db.session.commit()

    def __repr__(self):
        return '<Lesson %s>' % self.name


class AdjacentSection(db.Model):
    __tablename__ = 'adjacent_sections'
    previous_id = db.Column(db.Integer, db.ForeignKey('sections.id'), unique=True, primary_key=True)
    next_id = db.Column(db.Integer, db.ForeignKey('sections.id'), unique=True, primary_key=True)


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
        for s in sections:
            section = Section.query.filter_by(name=s[0]).first()
            if section is None:
                section = Section(name=s[0], lesson_id=Lesson.query.filter_by(name=s[1]).first().id)
                db.session.add(section)
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
        for ot in operation_types:
            operation_type = OperationType.query.filter_by(name=ot[0]).first()
            if operation_type is None:
                operation_type = OperationType(name=ot[0])
                db.session.add(operation_type)
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
