# -*- coding: utf-8 -*-

from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from app.exceptions import ValidationError
from . import db, login_manager


class Activation(db.Model):
    __tablename__ = 'activations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    activation_code_hash = db.Column(db.String(128))
    activated = db.Column(db.Boolean, default=False)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @property
    def activation_code(self):
        raise AttributeError('activation_code is not a readable attribute')

    @activation_code.setter
    def activation_code(self, activation_code):
        self.activation_code_hash = generate_password_hash(activation_code)

    def verify_activation_code(self, activation_code):
        return check_password_hash(self.activation_code_hash, activation_code)

    def __repr__(self):
        return '<Activation %r>' % self.name


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
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.LOGIN, True),
            'VB User': (Permission.LOGIN |
                        Permission.BOOK_VB_1, False),
            '1st Class User': (Permission.LOGIN |
                               Permission.BOOK_VB_1 |
                               Permission.BOOK_Y_GRE_1, False),
            '2nd Class User': (Permission.LOGIN |
                               Permission.BOOK_VB_2 |
                               Permission.BOOK_Y_GRE_1, False),
            'A Class User': (Permission.LOGIN |
                             Permission.BOOK_VB_A |
                             Permission.BOOK_Y_GRE_A, False),
            'Booking Moderator': (Permission.LOGIN |
                                  Permission.MODERATE_BOOKING, False),
            'iPad Rental Moderator': (Permission.LOGIN |
                                      Permission.MODERATE_RENTAL, False),
            'Period Moderator': (Permission.LOGIN |
                                 Permission.MODERATE_PERIOD, False),
            'iPad Contents Moderator': (Permission.LOGIN |
                                        Permission.MODERATE_IPAD, False),
            'User Moderator': (Permission.LOGIN |
                               Permission.MODERATE_USER, False),
            'Volunteer': (Permission.LOGIN |
                          Permission.MODERATE_BOOKING |
                          Permission.MODERATE_RENTAL |
                          Permission.MODERATE_PERIOD |
                          Permission.MODERATE_USER, False),
            'Operator': (Permission.LOGIN |
                         Permission.MODERATE_BOOKING |
                         Permission.MODERATE_RENTAL |
                         Permission.MODERATE_PERIOD |
                         Permission.MODERATE_IPAD |
                         Permission.MODERATE_USER, False),
            'Manager': (Permission.LOGIN |
                        Permission.MODERATE_BOOKING |
                        Permission.MODERATE_RENTAL |
                        Permission.MODERATE_PERIOD |
                        Permission.MODERATE_IPAD |
                        Permission.MODERATE_USER |
                        Permission.MODERATE_AUTH, False),
            'Administrator': (0xffffffff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class VBClass(db.Model):
    __tablename__ = 'vb_classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='vb_class', lazy='dynamic')

    def __repr__(self):
        return '<VB Class %r>' % self.name


class YGREClass(db.Model):
    __tablename__ = 'y_gre_classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='y_gre_class', lazy='dynamic')

    def __repr__(self):
        return '<Y-GRE Class %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(64), index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    vb_class_id = db.Column(db.Integer, db.ForeignKey('vb_classes.id'))
    y_gre_class_id = db.Column(db.Integer, db.ForeignKey('y_gre_classes.id'))
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    bookings = db.relationship('Booking', backref='user', lazy='dynamic')

    def __repr__(self):
        return '<User %r, %r>' % (self.name, self.email)


class Period(db.Model):
    __tablename__ = 'periods'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    bookings = db.relationship('Booking', backref='period', lazy='dynamic')

    def __repr__(self):
        return '<Period %r, %r>' % (self.start_time, self.end_time)


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    period_id = db.Column(db.Integer, db.ForeignKey('periods.id'))
    # timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    canceled = db.Column(db.Boolean, default=False)
    finished = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Booking %r, %r>' % (self.user_id, self.period_id)
