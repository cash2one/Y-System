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
    LOGIN            = 0b00000000000000000000000000000001
    BOOK_VB_1        = 0b00000000000000000000000000000010
    BOOK_VB_2        = 0b00000000000000000000000000000100
    BOOK_VB_A        = 0b00000000000000000000000000001000
    BOOK_Y_GRE_1     = 0b00000000000000000000000000010000
    BOOK_Y_GRE_A     = 0b00000000000000000000000000100000
    MODERATE_BOOKING = 0b00000000000000000000000001000000
    MODERATE_RENTAL  = 0b00000000000000000000000010000000
    MODERATE_PERIOD  = 0b00000000000000000000000100000000
    MODERATE_IPAD    = 0b00000000000000000000001000000000
    MODERATE_USER    = 0b00000000000000000000010000000000
    MODERATE_AUTH    = 0b00000000000000000000100000000000
    ADMINISTER       = 0b10000000000000000000000000000000


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = [
            (u'用户', Permission.LOGIN, ),
            (u'VB学员', Permission.LOGIN | Permission.BOOK_VB_1, ),
            (u'联报学员1类', Permission.LOGIN | Permission.BOOK_VB_1 | Permission.BOOK_Y_GRE_1, ),
            (u'联报学员2类', Permission.LOGIN | Permission.BOOK_VB_2 | Permission.BOOK_Y_GRE_1, ),
            (u'联报学员A类', Permission.LOGIN | Permission.BOOK_VB_A | Permission.BOOK_Y_GRE_A, ),
            (u'预约协管员', Permission.LOGIN | Permission.MODERATE_BOOKING, ),
            (u'iPad借阅协管员', Permission.LOGIN | Permission.MODERATE_RENTAL, ),
            (u'时段协管员', Permission.LOGIN | Permission.MODERATE_PERIOD, ),
            (u'iPad内容协管员', Permission.LOGIN | Permission.MODERATE_IPAD, ),
            (u'用户协管员', Permission.LOGIN | Permission.MODERATE_USER, ),
            (u'志愿者', Permission.LOGIN | Permission.MODERATE_BOOKING | Permission.MODERATE_RENTAL | Permission.MODERATE_PERIOD | Permission.MODERATE_USER, ),
            (u'管理员', Permission.LOGIN | Permission.MODERATE_BOOKING | Permission.MODERATE_RENTAL | Permission.MODERATE_PERIOD | Permission.MODERATE_IPAD | Permission.MODERATE_USER | Permission.MODERATE_AUTH, ),
            (u'开发人员', 0xffffffff, ),
        ]
        for r in roles:
            role = Role.query.filter_by(name=r[0]).first()
            if role is None:
                role = Role(name=r[0], permissions=r[1])
                db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class Activation(db.Model):
    __tablename__ = 'activations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    activation_code_hash = db.Column(db.String(128))
    activated = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    vb_class = db.Column(db.String(64))
    y_gre_class = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))

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
            activation = Activation.query.filter_by(name=a[0]).first()
            if activation is None:
                activation = Activation(name=a[0], activation_code=str(a[1]), role_id=Role.query.filter_by(name=a[2]).first().id, vb_class=a[3], y_gre_class=a[4], operator_id=u'1')
                db.session.add(activation)
        db.session.commit()

    def __repr__(self):
        return '<Activation %r>' % self.name


class Registration(db.Model):
    __tablename__ = 'registrations'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Registration %r, %r>' % (self.user_id, self.class_id)


class BookingState(db.Model):
    __tablename__ = 'booking_states'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    bookings = db.relationship('Booking', backref='booking_state', lazy='dynamic')

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
        return '<Booking State %r>' % self.name


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey('periods.id'), primary_key=True)
    booking_state_id = db.Column(db.Integer, db.ForeignKey('booking_states.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    cancel_timestamp = db.Column(db.DateTime)
    cancel_operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Booking %r, %r>' % (self.user_id, self.period_id)


class RentalType(db.Model):
    __tablename__ = 'rental_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    rentals = db.relationship('Rental', backref='rental_type', lazy='dynamic')

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
        return '<Rental Type %r>' % self.name


class Rental(db.Model):
    __tablename__ = 'rentals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    ipad_id = db.Column(db.Integer, db.ForeignKey('ipads.id'), primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    rental_type_id = db.Column(db.Integer, db.ForeignKey('rental_types.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Rental %r, %r>' % (self.user_id, self.ipad_id)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(64), index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    registered_classes = db.relationship('Registration', foreign_keys=[Registration.user_id], backref=db.backref('user', lazy='joined'), lazy='dynamic', cascade='all, delete-orphan')
    booked_periods = db.relationship('Booking', foreign_keys=[Booking.user_id], backref=db.backref('user', lazy='joined'), lazy='dynamic', cascade='all, delete-orphan')
    rented_ipads = db.relationship('Rental', foreign_keys=[Rental.user_id], backref=db.backref('user', lazy='joined'), lazy='dynamic', cascade='all, delete-orphan')
    punches = db.relationship('Punch', backref='punch', lazy='dynamic')

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
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    @staticmethod
    def insert_admin():
        admin = User.query.filter_by(email=current_app.config['YSYS_ADMIN']).first()
        if admin is None:
            admin = User(email=current_app.config['YSYS_ADMIN'], name=u'超级管理员', role_id=Role.query.filter_by(name=u'开发人员').first().id, password=current_app.config['YSYS_ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()

    def __repr__(self):
        return '<User %r, %r>' % (self.name, self.email)


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class ClassType(db.Model):
    __tablename__ = 'class_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    classes = db.relationship('Class', backref='class_type', lazy='dynamic')

    @staticmethod
    def insert_rental_types():
        class_types = [
            (u'VB', ),
            (u'Y-GRE', ),
        ]
        for ct in class_types:
            class_type = ClassType.query.filter_by(name=ct[0]).first()
            if class_type is None:
                class_type = ClassType(name=ct[0])
                db.session.add(class_type)
        db.session.commit()

    def __repr__(self):
        return '<Class Type %r>' % self.name


class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    class_type_id = db.Column(db.Integer, db.ForeignKey('class_types.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    registered_users = db.relationship('Registration', foreign_keys=[Registration.class_id], backref=db.backref('class', lazy='joined'), lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return '<Class %r>' % self.name


class Period(db.Model):
    __tablename__ = 'periods'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    date = db.Column(db.Date, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    booked_users = db.relationship('Booking', foreign_keys=[Booking.period_id], backref=db.backref('period', lazy='joined'), lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return '<Period %r, %r>' % (self.start_time, self.end_time)


class iPadCapacity(db.Model):
    __tablename__ = 'ipad_capacities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    ipads = db.relationship('iPad', backref='ipad_capacity', lazy='dynamic')

    @staticmethod
    def insert_ipad_capacities():
        ipad_capacities = [
            ('16GB', ),
            ('64GB', ),
        ]
        for ic in ipad_capacities:
            ipad_capacity = iPadCapacity.query.filter_by(name=ic[0]).first()
            if ipad_capacity is None:
                ipad_capacity = iPadCapacity(name=ic[0])
                db.session.add(ipad_capacity)
        db.session.commit()

    def __repr__(self):
        return '<iPad Capacity %r>' % self.name


class iPadContent(db.Model):
    __tablename__ = 'ipad_contents'
    ipad_id = db.Column(db.Integer, db.ForeignKey('ipads.id'), primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<iPad Content %r, %r>' % (self.ipad_id, self.lesson_id)


class iPad(db.Model):
    __tablename__ = 'ipads'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    serial = db.Column(db.String(12), unique=True)
    ipad_capacity_id = db.Column(db.Integer, db.ForeignKey('ipad_capacities.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    lessons_included = db.relationship('iPadContent', foreign_keys=[iPadContent.ipad_id], backref=db.backref('ipad', lazy='joined'), lazy='dynamic', cascade='all, delete-orphan')
    rented_users = db.relationship('Rental', foreign_keys=[Rental.ipad_id], backref=db.backref('ipad', lazy='joined'), lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return '<iPad %r, %r>' % (self.name, self.serial)


class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    videos = db.relationship('Video', backref='lesson', lazy='dynamic')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    occupied_ipads = db.relationship('iPadContent', foreign_keys=[iPadContent.lesson_id], backref=db.backref('lesson', lazy='joined'), lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return '<Lesson %r>' % self.name


class NextLesson(db.Model):
    __tablename__ = 'next_lessons'
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), unique=True, index=True)
    next_lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Next Video %r, %r>' % (self.video_id, self.next_video_id)


class Video(db.Model):
    __tablename__ = 'videos'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Video %r>' % self.name


class NextVideo(db.Model):
    __tablename__ = 'next_videos'
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), unique=True, index=True)
    next_video_id = db.Column(db.Integer, db.ForeignKey('videos.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Next Video %r, %r>' % (self.video_id, self.next_video_id)


class Punch(db.Model):
    __tablename__ = 'punches'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    rental_id = db.Column(db.Integer, db.ForeignKey('rentals.id'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'))
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Punch %r, %r>' % (self.user_id, self.video_id)

