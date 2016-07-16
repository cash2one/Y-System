# -*- coding: utf-8 -*-

from . import db


class Permission:
    LOGIN            = 0b00000000000000000000000000000001
    BOOK_VB_1        = 0b00000000000000000000000000000010
    BOOK_VB_2        = 0b00000000000000000000000000000100
    BOOK_VB_A        = 0b00000000000000000000000000001000
    BOOK_Y_GRE_1     = 0b00000000000000000000000000010000
    BOOK_Y_GRE_A     = 0b00000000000000000000000000100000
    MODERATE_BOOKING = 0b00000000000000000000000001000000
    MODERATE_RENTAL  = 0b00000000000000000000000010000000
    MODERATE_SESSION = 0b00000000000000000000000100000000
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
            'Session Moderator': (Permission.LOGIN |
                                  Permission.MODERATE_SESSION, False),
            'iPad Contents Moderator': (Permission.LOGIN |
                                        Permission.MODERATE_IPAD, False),
            'User Moderator': (Permission.LOGIN |
                               Permission.MODERATE_USER, False),
            'Agent': (Permission.LOGIN |
                      Permission.MODERATE_BOOKING |
                      Permission.MODERATE_RENTAL, False),
            'Manager': (Permission.LOGIN |
                        Permission.MODERATE_BOOKING |
                        Permission.MODERATE_RENTAL |
                        Permission.MODERATE_SESSION |
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


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username
