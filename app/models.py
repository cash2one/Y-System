# -*- coding: utf-8 -*-

import os
import requests
from datetime import datetime, date, time, timedelta
from random import choice
from string import ascii_letters, digits
from base64 import b64encode
from hashlib import sha512, md5
from json import loads, dumps
from bs4 import BeautifulSoup
from sqlalchemy import or_, and_
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from app.exceptions import ValidationError
from . import db, login_manager
from .email import send_emails


class Version:
    Application = 'v1.0.0-dev'
    jQuery = '3.1.1'
    SemanticUI = '2.2.7'
    SemanticUICalendar = '0.0.6'
    FontAwesome = '4.7.0'
    MomentJS = '2.17.1'
    CountUp = '1.8.1'
    ECharts = '3.4.0'


class Analytics:
    PiwikSiteID = os.getenv('PIWIK_SITE_ID')
    GATrackID = os.getenv('GA_TRACK_ID')


class Color(db.Model):
    __tablename__ = 'colors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    css_class = db.Column(db.Unicode(64))
    tags = db.relationship('Tag', backref='color', lazy='dynamic')

    @staticmethod
    def insert_colors():
        colors = [
            (u'Default', u'', ),
            (u'Red', u'red', ),
            (u'Orange', u'orange', ),
            (u'Yellow', u'yellow', ),
            (u'Olive', u'olive', ),
            (u'Green', u'green', ),
            (u'Teal', u'teal', ),
            (u'Blue', u'blue', ),
            (u'Violet', u'violet', ),
            (u'Purple', u'purple', ),
            (u'Pink', u'pink', ),
            (u'Brown', u'brown', ),
            (u'Grey', u'grey', ),
            (u'Black', u'black', ),
        ]
        for entry in colors:
            color = Color.query.filter_by(name=entry[0]).first()
            if color is None:
                color = Color(
                    name=entry[0],
                    css_class=entry[1]
                )
                db.session.add(color)
                print u'导入颜色信息', entry[0]
        db.session.commit()

    def __repr__(self):
        return '<Color %r>' % self.name


class RolePermission(db.Model):
    __tablename__ = 'role_permissions'
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), primary_key=True)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), primary_key=True)


class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    overdue_check = db.Column(db.Boolean, default=False)
    roles = db.relationship(
        'RolePermission',
        foreign_keys=[RolePermission.permission_id],
        backref=db.backref('permission', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @staticmethod
    def insert_permissions():
        permissions = [
            (u'预约', True, ),
            (u'预约VB课程', True, ),
            (u'预约Y-GRE课程', True, ),
            (u'预约VB课程×2', True, ),
            (u'预约任意课程', True, ),
            (u'管理', False, ),
            (u'管理课程预约', False, ),
            (u'管理学习进度', False, ),
            (u'管理iPad借阅', False, ),
            (u'管理预约时段', False, ),
            (u'管理课程', False, ),
            (u'管理作业', False, ),
            (u'管理考试', False, ),
            (u'管理用户', False, ),
            (u'管理团报', False, ),
            (u'管理班级', False, ),
            (u'管理用户标签', False, ),
            (u'管理iPad设备', False, ),
            (u'管理通知', False, ),
            (u'管理站内信', False, ),
            (u'管理反馈', False, ),
            (u'管理进站', False, ),
            (u'管理产品', False, ),
            (u'管理权限', False, ),
            (u'开发权限', False, ),
        ]
        for entry in permissions:
            permission = Permission.query.filter_by(name=entry[0]).first()
            if permission is None:
                permission = Permission(
                    name=entry[0],
                    overdue_check=entry[1]
                )
                db.session.add(permission)
                print u'导入用户权限信息', entry[0]
        db.session.commit()

    def __repr__(self):
        return '<Permission %r>' % self.name


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    permissions = db.relationship(
        'RolePermission',
        foreign_keys=[RolePermission.role_id],
        backref=db.backref('role', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    users = db.relationship('User', backref='role', lazy='dynamic')
    suspension_records = db.relationship('SuspensionRecord', backref='original_role', lazy='dynamic')

    def add_permission(self, permission):
        if not self.has_permission(permission):
            role_permission = RolePermission(role_id=self.id, permission_id=permission.id)
            db.session.add(role_permission)

    def remove_permission(self, permission):
        role_permission = self.permissions.filter_by(permission_id=permission.id).first()
        if role_permission:
            db.session.delete(role_permission)

    def has_permission(self, permission):
        return self.permissions.filter_by(permission_id=permission.id).first() is not None

    def permissions_alias(self, prefix=None, formatted=False):
        if prefix is not None:
            permissions = Permission.query\
                .join(RolePermission, RolePermission.permission_id == Permission.id)\
                .filter(RolePermission.role_id == self.id)\
                .filter(Permission.name.like(prefix + '%'))\
                .order_by(Permission.id.asc())
        else:
            permissions = Permission.query\
                .join(RolePermission, RolePermission.permission_id == Permission.id)\
                .filter(RolePermission.role_id == self.id)\
                .order_by(Permission.id.asc())
        if formatted:
            if permissions.count() == 0:
                return u'无'
            if permissions.count() == 1:
                return permissions.first().name
            return u' · '.join([permission.name for permission in permissions.all()])
        return permissions

    def permissions_num(self, prefix=None):
        if prefix is not None:
            return Permission.query\
                .join(RolePermission, RolePermission.permission_id == Permission.id)\
                .filter(RolePermission.role_id == self.id)\
                .filter(Permission.name.like(prefix + '%'))\
                .count()
        return len(self.permissions)

    @staticmethod
    def insert_roles():
        roles = [
            (u'挂起', [], ),
            (u'单VB', [u'预约', u'预约VB课程'], ),
            (u'Y-GRE 普通', [u'预约', u'预约VB课程', u'预约Y-GRE课程'], ),
            (u'Y-GRE VB×2', [u'预约', u'预约VB课程', u'预约Y-GRE课程', u'预约VB课程×2'], ),
            (u'Y-GRE A权限', [u'预约', u'预约VB课程', u'预约Y-GRE课程', u'预约任意课程'], ),
            (u'志愿者', [u'预约', u'预约VB课程', u'预约Y-GRE课程', u'预约任意课程'] + [u'管理', u'管理课程预约', u'管理学习进度', u'管理iPad借阅'], ),
            (u'协管员', [u'预约', u'预约VB课程', u'预约Y-GRE课程', u'预约任意课程'] + [u'管理', u'管理课程预约', u'管理学习进度', u'管理iPad借阅', u'管理预约时段', u'管理课程', u'管理作业', u'管理考试', u'管理用户', u'管理团报', u'管理班级', u'管理用户标签', u'管理iPad设备', u'管理通知', u'管理站内信', u'管理反馈', u'管理进站', u'管理产品'], ),
            (u'管理员', [u'预约', u'预约VB课程', u'预约Y-GRE课程', u'预约任意课程'] + [u'管理', u'管理课程预约', u'管理学习进度', u'管理iPad借阅', u'管理预约时段', u'管理课程', u'管理作业', u'管理考试', u'管理用户', u'管理团报', u'管理班级', u'管理用户标签', u'管理iPad设备', u'管理通知', u'管理站内信', u'管理反馈', u'管理进站', u'管理产品', u'管理权限'], ),
            (u'开发人员', [permission.name for permission in Permission.query.all()], ),
        ]
        for entry in roles:
            role = Role.query.filter_by(name=entry[0]).first()
            if role is None:
                role = Role(name=entry[0])
                db.session.add(role)
                db.session.commit()
                print u'导入用户角色信息', entry[0]
            for sub_entry in entry[1]:
                permission = Permission.query.filter_by(name=sub_entry).first()
                if not role.has_permission(permission=permission):
                    role.add_permission(permission=permission)
                    print u'赋予权限', entry[0], sub_entry
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class Gender(db.Model):
    __tablename__ = 'genders'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    users = db.relationship('User', backref='gender', lazy='dynamic')

    @staticmethod
    def insert_genders():
        genders = [
            (u'男', ),
            (u'女', ),
        ]
        for entry in genders:
            gender = Gender.query.filter_by(name=entry[0]).first()
            if gender is None:
                gender = Gender(name=entry[0])
                db.session.add(gender)
                print u'导入性别类型信息', entry[0]
        db.session.commit()

    def __repr__(self):
        return '<Gender %r>' % self.name


class Relationship(db.Model):
    __tablename__ = 'relationships'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    users = db.relationship('User', backref='relationship', lazy='dynamic')

    @staticmethod
    def insert_relationships():
        relationships = [
            (u'父母', ),
            (u'配偶', ),
            (u'子女', ),
            (u'兄弟', ),
            (u'兄妹', ),
            (u'姊妹', ),
            (u'姊弟', ),
            (u'朋友', ),
            (u'恋人', ),
            (u'同学', ),
            (u'同事', ),
        ]
        for entry in relationships:
            relationship = Relationship.query.filter_by(name=entry[0]).first()
            if relationship is None:
                relationship = Relationship(name=entry[0])
                db.session.add(relationship)
                print u'导入关系类型信息', entry[0]
        db.session.commit()

    def __repr__(self):
        return '<Relationship %r>' % self.name


class Purpose(db.Model):
    __tablename__ = 'purposes'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey('purpose_types.id'), primary_key=True)
    remark = db.Column(db.UnicodeText)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class PurposeType(db.Model):
    __tablename__ = 'purpose_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    purposes = db.relationship(
        'Purpose',
        foreign_keys=[Purpose.type_id],
        backref=db.backref('type', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @staticmethod
    def insert_purpose_types():
        purpose_types = [
            (u'词源爱好者', ),
            (u'GRE', ),
            (u'TOEFL', ),
            (u'GMAT', ),
            (u'IELTS', ),
            (u'考研', ),
            (u'四六级', ),
            (u'其它', ),
        ]
        for entry in purpose_types:
            purpose_type = PurposeType.query.filter_by(name=entry[0]).first()
            if purpose_type is None:
                purpose_type = PurposeType(name=entry[0])
                db.session.add(purpose_type)
                print u'导入研修目的类型信息', entry[0]
        db.session.commit()

    def __repr__(self):
        return '<Purpose Type %r>' % self.name


class Referrer(db.Model):
    __tablename__ = 'referrers'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey('referrer_types.id'), primary_key=True)
    remark = db.Column(db.UnicodeText)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class ReferrerType(db.Model):
    __tablename__ = 'referrer_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    referrers = db.relationship(
        'Referrer',
        foreign_keys=[Referrer.type_id],
        backref=db.backref('type', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @staticmethod
    def insert_referrer_types():
        referrer_types = [
            (u'讲座', ),
            (u'博客', ),
            (u'微博', ),
            (u'微信', ),
            (u'人人', ),
            (u'传单', ),
            (u'其它', ),
        ]
        for entry in referrer_types:
            referrer_type = ReferrerType.query.filter_by(name=entry[0]).first()
            if referrer_type is None:
                referrer_type = ReferrerType(name=entry[0])
                db.session.add(referrer_type)
                print u'导入来源类型信息', entry[0]
        db.session.commit()

    def __repr__(self):
        return '<Purpose Type %r>' % self.name


class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer, default=1)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def alias(self):
        return u'%s ×%s' % (self.product.alias, self.quantity)

    @property
    def total(self):
        return self.product.price * self.quantity

    @property
    def total_alias(self):
        return u'%g' % self.total

    def __repr__(self):
        return '<Purchase %r, %r>' % (self.user.name, self.alias)


class SuspensionRecord(db.Model):
    __tablename__ = 'suspension_records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    original_role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    start_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    end_datetime = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def ping(self, modified_by):
        self.modified_at = datetime.utcnow()
        self.modified_by_id = modified_by.id
        db.session.add(self)

    def __repr__(self):
        return '<Suspension Record %r, %r, %r>' % (self.user.name, self.start_datetime, self.end_datetime)


class CourseRegistration(db.Model):
    __tablename__ = 'course_registrations'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


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
        for entry in booking_states:
            booking_state = BookingState.query.filter_by(name=entry[0]).first()
            if booking_state is None:
                booking_state = BookingState(name=entry[0])
                db.session.add(booking_state)
                print u'导入预约状态信息', entry[0]
        db.session.commit()

    def __repr__(self):
        return '<Booking State %r>' % self.name


class Booking(db.Model):
    __tablename__ = 'bookings'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), primary_key=True)
    state_id = db.Column(db.Integer, db.ForeignKey('booking_states.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    token = db.Column(db.String(128), unique=True, index=True)

    def __init__(self, **kwargs):
        super(Booking, self).__init__(**kwargs)
        self.token = self.create_token()

    def ping(self):
        self.timestamp = datetime.utcnow()
        db.session.add(self)

    def create_token(self):
        nonce_str = ''.join(choice(ascii_letters + digits) for _ in range(24))
        string = 'user_id=%s&schedule_id=%s&timestamp=%s&nonce_str=%s' % (self.user_id, self.schedule_id, self.timestamp, nonce_str)
        return sha512(string).hexdigest()

    def update_token(self):
        self.token = self.create_token()
        db.session.add(self)

    def set_state(self, state_name):
        self.state_id = BookingState.query.filter_by(name=state_name).first().id
        self.ping()
        db.session.add(self)
        if state_name == u'预约':
            db.session.commit()
            self.update_token()
        if state_name == u'取消' and self.schedule.unstarted:
            waited_booking = Booking.query\
                .join(BookingState, BookingState.id == Booking.state_id)\
                .join(Schedule, Schedule.id == Booking.schedule_id)\
                .filter(Schedule.id == self.schedule_id)\
                .filter(BookingState.name == u'排队')\
                .order_by(Booking.timestamp.desc())\
                .first()
            if waited_booking:
                waited_booking.state_id = BookingState.query.filter_by(name=u'预约').first().id
                waited_booking.ping()
                db.session.add(waited_booking)
                return User.query.get(waited_booking.user_id)

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

    @staticmethod
    def show_ups(lessons):
        return sum([rental.user.last_punch.section.lesson.name in lessons for rental in Rental.query.filter(Rental.returned == False).filter(Rental.walk_in == False).all()])

    @staticmethod
    def of_current_vb_schedule(lessons):
        for schedule in Schedule.query\
            .join(Period, Period.id == Schedule.period_id)\
            .join(CourseType, CourseType.id == Period.type_id)\
            .filter(or_(
                Schedule.date == date.today() - timedelta(days=1),
                Schedule.date == date.today(),
                Schedule.date == date.today() + timedelta(days=1),
            ))\
            .filter(CourseType.name == u'VB')\
            .all():
            if schedule.started:
                return sum([booking.user.last_punch.section.lesson.name in lessons for booking in Booking.query.filter_by(schedule_id=schedule.id).all() if booking.state.name in [u'预约', u'排队', u'赴约', u'迟到']])
        return 0

    @staticmethod
    def of_current_y_gre_schedule(lessons):
        for schedule in Schedule.query\
            .join(Period, Period.id == Schedule.period_id)\
            .join(CourseType, CourseType.id == Period.type_id)\
            .filter(or_(
                Schedule.date == date.today() - timedelta(days=1),
                Schedule.date == date.today(),
                Schedule.date == date.today() + timedelta(days=1),
            ))\
            .filter(CourseType.name == u'Y-GRE')\
            .all():
            if schedule.started:
                return sum([booking.user.last_punch.section.lesson.name in lessons for booking in Booking.query.filter_by(schedule_id=schedule.id).all() if booking.state.name in [u'预约', u'排队', u'赴约', u'迟到']])
        return 0

    def to_json(self):
        booking_json = {
            'user': self.user.to_json(),
            'schedule': self.schedule.to_json(),
            'state': self.state.name,
            'timestamp': self.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'token': self.token,
        }
        return booking_json


class Rental(db.Model):
    __tablename__ = 'rentals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ipad_id = db.Column(db.Integer, db.ForeignKey('ipads.id'))
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'))
    walk_in = db.Column(db.Boolean, default=False)
    rent_time = db.Column(db.DateTime, default=datetime.utcnow)
    rent_agent_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    returned = db.Column(db.Boolean, default=False)
    return_time = db.Column(db.DateTime)
    return_agent_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def set_returned(self, return_agent_id, ipad_state=u'待机'):
        self.returned = True
        self.return_time = datetime.utcnow()
        self.return_agent_id = return_agent_id
        db.session.add(self)
        ipad = iPad.query.get(self.ipad_id)
        modified_by = User.query.get(return_agent_id)
        ipad.set_state(ipad_state, modified_by=modified_by)

    @property
    def is_overtime(self):
        if (not self.returned) and self.schedule.ended:
            return True
        return False

    @staticmethod
    def unreturned_walk_ins_in_room(room_name):
        return Rental.query\
            .join(iPad, iPad.id == Rental.ipad_id)\
            .join(Room, Room.id == iPad.room_id)\
            .filter(Room.name == room_name)\
            .filter(Rental.returned == False)\
            .filter(Rental.walk_in == True)\
            .count()

    @staticmethod
    def current_overtimes_in_room(room_name):
        return sum([rental.is_overtime for rental in Rental.query.join(iPad, iPad.id == Rental.ipad_id).join(Room, Room.id == iPad.room_id).filter(Room.name == room_name).filter(Rental.returned == False).all()])

    def __repr__(self):
        return '<Rental %r, %r, %r>' % (self.user.name, self.ipad.alias, self.ipad.serial)


class Punch(db.Model):
    __tablename__ = 'punches'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), primary_key=True)
    milestone = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_json(self):
        punch_json = {
            'user': self.user.name,
            'section': self.section.to_json(),
            'milestone': self.milestone,
            'punched_at': self.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
        return punch_json

    def __repr__(self):
        return '<Punch %r, %r>' % (self.user.name, self.section.alias)


class AssignmentScoreGrade(db.Model):
    __tablename__ = 'assignment_score_grades'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    assignment_scores = db.relationship('AssignmentScore', backref='grade', lazy='dynamic')

    @staticmethod
    def insert_assignment_score_grades():
        assignment_score_grades = [
            (u'完成', ),
            (u'A+', ),
            (u'A', ),
            (u'A-', ),
            (u'B+', ),
            (u'B', ),
            (u'B-', ),
            (u'C+', ),
            (u'C', ),
            (u'C-', ),
            (u'D+', ),
            (u'D', ),
            (u'D-', ),
            (u'F', ),
        ]
        for entry in assignment_score_grades:
            assignment_score_grade = AssignmentScoreGrade.query.filter_by(name=entry[0]).first()
            if assignment_score_grade is None:
                assignment_score_grade = AssignmentScoreGrade(name=entry[0])
                db.session.add(assignment_score_grade)
                print u'导入作业成绩类型信息', entry[0]
        db.session.commit()

    def __repr__(self):
        return '<Assignment Score Grade %r>' % self.name


class AssignmentScore(db.Model):
    __tablename__ = 'assignment_scores'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'))
    grade_id = db.Column(db.Integer, db.ForeignKey('assignment_score_grades.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def ping(self, modified_by):
        self.modified_at = datetime.utcnow()
        self.modified_by_id = modified_by.id
        db.session.add(self)

    @property
    def alias(self):
        return u'%s %s %s' % (self.user.name_alias, self.assignment.name, self.grade.name)

    def to_json(self):
        assignment_score_json = {
            'user': self.user.name,
            'assignment': self.assignment.to_json(),
            'grade': self.grade.name,
            'alias': self.alias,
            'created_at': self.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'modified_at': self.modified_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'modified_by': self.modified_by.name,
        }
        return assignment_score_json

    def __repr__(self):
        return '<Assignment Score %r>' % self.alias


class VBTestScore(db.Model):
    __tablename__ = 'vb_test_scores'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'))
    score = db.Column(db.Float)
    retrieved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def ping(self, modified_by):
        self.modified_at = datetime.utcnow()
        self.modified_by_id = modified_by.id
        db.session.add(self)

    @property
    def alias(self):
        return u'%s %s %g' % (self.user.name_alias, self.test.name, self.score)

    @property
    def score_alias(self):
        return u'%g' % self.score

    def toggle_retrieve(self, modified_by):
        self.retrieved = not self.retrieved
        self.ping(modified_by=modified_by)
        db.session.add(self)

    def to_json(self):
        vb_test_score_json = {
            'user': self.user.name,
            'test': self.test.to_json(),
            'score': self.score,
            'retrieved': self.retrieved,
            'alias': self.alias,
            'score_alias': self.score_alias,
            'created_at': self.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'modified_at': self.modified_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'modified_by': self.modified_by.name,
        }
        return vb_test_score_json

    def __repr__(self):
        return '<VB Test Score %r>' % self.alias


class GREAWScore(db.Model):
    __tablename__ = 'gre_aw_scores'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    value = db.Column(db.Float)
    y_gre_test_scores = db.relationship('YGRETestScore', backref='aw_score', lazy='dynamic')
    gre_test_scores = db.relationship('GRETestScore', backref='aw_score', lazy='dynamic')

    @staticmethod
    def insert_gre_aw_scores():
        gre_aw_scores = [(unicode(x/2.0), x/2.0, ) for x in range(0, 13)]
        for entry in gre_aw_scores:
            gre_aw_score = GREAWScore.query.filter_by(name=entry[0]).first()
            if gre_aw_score is None:
                gre_aw_score = GREAWScore(name=entry[0], value=entry[1])
                db.session.add(gre_aw_score)
                print u'导入GRE AW成绩类型信息', entry[0]
        db.session.commit()

    def __repr__(self):
        return '<GRE Analytical Writing Score %r>' % self.name


class YGRETestScore(db.Model):
    __tablename__ = 'y_gre_test_scores'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'))
    v_score = db.Column(db.Integer)
    q_score = db.Column(db.Integer)
    aw_score_id = db.Column(db.Integer, db.ForeignKey('gre_aw_scores.id'))
    retrieved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def ping(self, modified_by):
        self.modified_at = datetime.utcnow()
        self.modified_by_id = modified_by.id
        db.session.add(self)

    @property
    def alias(self):
        if self.q_score is None:
            q_score = '-'
        if self.aw_score is None:
            aw_score = '-'
        else:
            aw_score = self.aw_score.name
        return u'%s %s V%s Q%s AW%s' % (self.user.name_alias, self.test.name, self.v_score, q_score, aw_score)

    @property
    def score_alias(self):
        if self.q_score is None:
            q_score = '-'
        if self.aw_score is None:
            aw_score = '-'
        else:
            aw_score = self.aw_score.name
        return u'V%s Q%s AW%s' % (self.v_score, q_score, aw_score)

    @property
    def v_score_alias(self):
        return u'V%s' % self.v_score

    @property
    def aw_score_alias(self):
        if self.aw_score:
            return self.aw_score.name
        return u''

    def toggle_retrieve(self, modified_by):
        self.retrieved = not self.retrieved
        self.ping(modified_by=modified_by)
        db.session.add(self)

    def to_json(self):
        y_gre_test_score_json = {
            'user': self.user.name,
            'test': self.test.to_json(),
            'v_score': self.v_score,
            'q_score': self.q_score,
            'aw_score': self.aw_score_alias,
            'retrieved': self.retrieved,
            'alias': self.alias,
            'score_alias': self.score_alias,
            'v_score_alias': self.v_score_alias,
            'created_at': self.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'modified_at': self.modified_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'modified_by': self.modified_by.name,
        }
        return y_gre_test_score_json

    def __repr__(self):
        return '<Y-GRE Test Score %r>' % self.alias


class GRETest(db.Model):
    __tablename__ = 'gre_tests'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, index=True)
    scores = db.relationship('GRETestScore', backref='test', lazy='dynamic')

    @property
    def alias(self):
        return u'GRE %s' % self.date

    @property
    def finished_by_alias(self):
        return GRETestScore.query\
            .join(User, User.id == GRETestScore.user_id)\
            .filter(GRETestScore.test_id == self.id)\
            .filter(User.created == True)\
            .filter(User.activated == True)\
            .filter(User.deleted == False)

    def __repr__(self):
        return '<GRE Test %r>' % self.date


class GRETestScore(db.Model):
    __tablename__ = 'gre_test_scores'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    test_id = db.Column(db.Integer, db.ForeignKey('gre_tests.id'))
    v_score = db.Column(db.Integer)
    q_score = db.Column(db.Integer)
    aw_score_id = db.Column(db.Integer, db.ForeignKey('gre_aw_scores.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def ping(self, modified_by):
        self.modified_at = datetime.utcnow()
        self.modified_by_id = modified_by.id
        db.session.add(self)

    @property
    def alias(self):
        return u'%s %s V%g Q%g AW%s' % (self.user.name_alias, self.test.date, self.v_score, self.q_score, self.aw_score.name)

    @property
    def alias2(self):
        return u'Verbal Reasoning：%g · Quantitative Reasoning：%g · Analytical Writing：%s' % (self.v_score, self.q_score, self.aw_score.name)

    def __repr__(self):
        return '<GRE Test Score %r>' % self.alias


class TOEFLTest(db.Model):
    __tablename__ = 'toefl_tests'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, index=True)
    scores = db.relationship('TOEFLTestScore', backref='test', lazy='dynamic')

    @property
    def alias(self):
        return u'TOEFL %s' % self.date

    @property
    def finished_by_alias(self):
        return TOEFLTestScore.query\
            .join(User, User.id == TOEFLTestScore.user_id)\
            .filter(TOEFLTestScore.test_id == self.id)\
            .filter(User.created == True)\
            .filter(User.activated == True)\
            .filter(User.deleted == False)

    def __repr__(self):
        return '<TOEFL Test %r>' % self.date


class TOEFLTestScore(db.Model):
    __tablename__ = 'toefl_test_score'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    test_id = db.Column(db.Integer, db.ForeignKey('toefl_tests.id'))
    total_score = db.Column(db.Integer)
    reading_score = db.Column(db.Integer)
    listening_score = db.Column(db.Integer)
    speaking_score = db.Column(db.Integer)
    writing_score = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def ping(self, modified_by):
        self.modified_at = datetime.utcnow()
        self.modified_by_id = modified_by.id
        db.session.add(self)

    @property
    def alias(self):
        return u'%s %s %g R%g L%g S%g W%g' % (self.user.name_alias, self.test.date, self.total_score, self.reading_score, self.listening_score, self.speaking_score, self.writing_score)

    @property
    def alias2(self):
        return u'总分：%g分（阅读：%g分 · 听力：%g分 · 口语：%g分 · 写作：%g分）' % (self.total_score, self.reading_score, self.listening_score, self.speaking_score, self.writing_score)

    def __repr__(self):
        return '<TOEFL Test Score %r>' % self.alias


class UserAnnouncement(db.Model):
    __tablename__ = 'user_announcements'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcements.id'), primary_key=True)


class InvitationType(db.Model):
    __tablename__ = 'invitation_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    invitations = db.relationship('Invitation', backref='type', lazy='dynamic')

    @staticmethod
    def insert_invitation_types():
        invitation_types = [
            (u'积分', ),
            (u'提成', ),
        ]
        for entry in invitation_types:
            invitation_type = InvitationType.query.filter_by(name=entry[0]).first()
            if invitation_type is None:
                invitation_type = InvitationType(name=entry[0])
                db.session.add(invitation_type)
                print u'导入邀请类型信息', entry[0]
        db.session.commit()

    def __repr__(self):
        return '<Invitation Type %r>' % self.name


class Invitation(db.Model):
    __tablename__ = 'invitations'
    inviter_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey('invitation_types.id'))
    paid_off = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Reception(db.Model):
    __tablename__ = 'receptions'
    receptionist_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class UserCreation(db.Model):
    __tablename__ = 'user_creations'
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class GroupRegistration(db.Model):
    __tablename__ = 'group_registrations'
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class UserTag(db.Model):
    __tablename__ = 'user_tags'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    # basic properties
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Unicode(64), unique=True, index=True)
    confirmed = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    created = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime)
    activated = db.Column(db.Boolean, default=False)
    activated_at = db.Column(db.DateTime)
    last_seen_at = db.Column(db.DateTime)
    deleted = db.Column(db.Boolean, default=False)
    # profile properties
    name = db.Column(db.Unicode(64), index=True)
    id_number = db.Column(db.Unicode(64), index=True)
    gender_id = db.Column(db.Integer, db.ForeignKey('genders.id'))
    birthdate = db.Column(db.Date)
    mobile = db.Column(db.Unicode(64))
    wechat = db.Column(db.Unicode(64))
    qq = db.Column(db.Unicode(64))
    address = db.Column(db.Unicode(128))
    emergency_contact_name = db.Column(db.Unicode(64))
    emergency_contact_mobile = db.Column(db.Unicode(64))
    emergency_contact_relationship_id = db.Column(db.Integer, db.ForeignKey('relationships.id'))
    education_records = db.relationship('EducationRecord', backref='user', lazy='dynamic')
    employment_records = db.relationship('EmploymentRecord', backref='user', lazy='dynamic')
    score_records = db.relationship('ScoreRecord', backref='user', lazy='dynamic')
    worked_in_same_field = db.Column(db.Boolean, default=False)
    deformity = db.Column(db.Boolean, default=False)
    # application properties
    application_aim = db.Column(db.Unicode(64))
    # tags
    has_tags = db.relationship(
        'UserTag',
        foreign_keys=[UserTag.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    # study properties
    purposes = db.relationship(
        'Purpose',
        foreign_keys=[Purpose.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    referrers = db.relationship(
        'Referrer',
        foreign_keys=[Referrer.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    purchases = db.relationship(
        'Purchase',
        foreign_keys=[Purchase.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    suspension_records = db.relationship(
        'SuspensionRecord',
        foreign_keys=[SuspensionRecord.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    course_registrations = db.relationship(
        'CourseRegistration',
        foreign_keys=[CourseRegistration.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    bookings = db.relationship(
        'Booking',
        foreign_keys=[Booking.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    rentals = db.relationship(
        'Rental',
        foreign_keys=[Rental.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    punches = db.relationship(
        'Punch',
        foreign_keys=[Punch.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    assignment_scores = db.relationship(
        'AssignmentScore',
        foreign_keys=[AssignmentScore.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    vb_test_scores = db.relationship(
        'VBTestScore',
        foreign_keys=[VBTestScore.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    y_gre_test_scores = db.relationship(
        'YGRETestScore',
        foreign_keys=[YGRETestScore.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    gre_test_scores = db.relationship(
        'GRETestScore',
        foreign_keys=[GRETestScore.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    toefl_test_scores = db.relationship(
        'TOEFLTestScore',
        foreign_keys=[TOEFLTestScore.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    read_announcements = db.relationship(
        'UserAnnouncement',
        foreign_keys=[UserAnnouncement.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    # management properties
    modified_products = db.relationship('Product', backref='modified_by', lazy='dynamic')
    modified_suspension_records = db.relationship(
        'SuspensionRecord',
        foreign_keys=[SuspensionRecord.modified_by_id],
        backref=db.backref('modified_by', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    modified_courses = db.relationship('Course', backref='modified_by', lazy='dynamic')
    modified_periods = db.relationship('Period', backref='modified_by', lazy='dynamic')
    modified_schedules = db.relationship('Schedule', backref='modified_by', lazy='dynamic')
    modified_ipads = db.relationship('iPad', backref='modified_by', lazy='dynamic')
    managed_rentals_rent = db.relationship(
        'Rental',
        foreign_keys=[Rental.rent_agent_id],
        backref=db.backref('rent_agent', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    managed_rentals_return = db.relationship(
        'Rental',
        foreign_keys=[Rental.return_agent_id],
        backref=db.backref('return_agent', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    modified_assignment_scores = db.relationship(
        'AssignmentScore',
        foreign_keys=[AssignmentScore.modified_by_id],
        backref=db.backref('modified_by', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    modified_vb_test_scores = db.relationship(
        'VBTestScore',
        foreign_keys=[VBTestScore.modified_by_id],
        backref=db.backref('modified_by', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    modified_y_gre_test_scores = db.relationship(
        'YGRETestScore',
        foreign_keys=[YGRETestScore.modified_by_id],
        backref=db.backref('modified_by', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    modified_gre_test_scores = db.relationship(
        'GRETestScore',
        foreign_keys=[GRETestScore.modified_by_id],
        backref=db.backref('modified_by', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    modified_toefl_test_scores = db.relationship(
        'TOEFLTestScore',
        foreign_keys=[TOEFLTestScore.modified_by_id],
        backref=db.backref('modified_by', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    modified_announcements = db.relationship('Announcement', backref='modified_by', lazy='dynamic')
    # user relationship properties
    sent_invitations = db.relationship(
        'Invitation',
        foreign_keys=[Invitation.inviter_id],
        backref=db.backref('inviter', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    accepted_invitations = db.relationship(
        'Invitation',
        foreign_keys=[Invitation.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    made_receptions = db.relationship(
        'Reception',
        foreign_keys=[Reception.receptionist_id],
        backref=db.backref('receptionist', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    received_receptions = db.relationship(
        'Reception',
        foreign_keys=[Reception.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    made_user_creations = db.relationship(
        'UserCreation',
        foreign_keys=[UserCreation.creator_id],
        backref=db.backref('creator', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    received_user_creations = db.relationship(
        'UserCreation',
        foreign_keys=[UserCreation.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    organized_groups = db.relationship(
        'GroupRegistration',
        foreign_keys=[GroupRegistration.organizer_id],
        backref=db.backref('organizer', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    registered_groups = db.relationship(
        'GroupRegistration',
        foreign_keys=[GroupRegistration.member_id],
        backref=db.backref('member', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def delete(self):
        for tag in self.has_tags:
            self.remove_tag(tag=tag.tag)
        for purpose in self.purposes:
            self.remove_purpose(purpose_type=purpose.type)
        for referrer in self.referrers:
            self.remove_referrer(referrer_type=referrer.type)
        for education_record in self.education_records:
            db.session.delete(education_record)
        for employment_record in self.employment_records:
            db.session.delete(employment_record)
        for score_record in self.score_records:
            db.session.delete(score_record)
        for gre_test_score in self.gre_test_scores:
            db.session.delete(gre_test_score)
        for toefl_test_score in self.toefl_test_scores:
            db.session.delete(toefl_test_score)
        for purchase in self.purchases:
            db.session.delete(purchase)
        for course_registration in self.course_registrations:
            self.unregister_course(course=course_registration.course)
        for invitation in self.accepted_invitations:
            invitation.inviter.uninvite_user(user=self)
        for reception in self.received_receptions:
            reception.receptionist.unreceive_user(user=self)
        for user_creation in self.received_user_creations:
            user_creation.creator.uncreate_user(user=self)
        db.session.delete(self)

    def safe_delete(self):
        self.email = u'%s_%s_deleted' % (self.email, self.id)
        self.role_id = Role.query.filter_by(name=u'挂起').first().id
        self.deleted = True
        db.session.add(self)

    def restore(self, email, role):
        self.email = email
        self.role_id = role.id
        self.deleted = False
        db.session.add(self)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        serial = Serializer(current_app.config['SECRET_KEY'], expiration)
        return serial.dumps({'confirm': self.id})

    def confirm(self, token):
        serial = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = serial.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        serial = Serializer(current_app.config['SECRET_KEY'], expiration)
        return serial.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        serial = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = serial.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        serial = Serializer(current_app.config['SECRET_KEY'], expiration)
        return serial.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        serial = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = serial.loads(token)
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

    def can(self, permission_name):
        permission = Permission.query.filter_by(name=permission_name).first()
        return permission is not None and \
            not (permission.overdue_check and self.overdue) and \
            self.role is not None and \
            self.role.has_permission(permission=permission)

    @staticmethod
    def users_can(permission_name):
        return User.query\
            .join(Role, Role.id == User.role_id)\
            .join(RolePermission, RolePermission.role_id == Role.id)\
            .join(Permission, Permission.id == RolePermission.permission_id)\
            .filter(Permission.name == permission_name)\
            .filter(User.created == True)\
            .filter(User.activated == True)\
            .filter(User.confirmed == True)\
            .filter(User.deleted == False)

    @property
    def is_suspended(self):
        return self.role.name == u'挂起'

    @property
    def is_volunteer(self):
        return self.role.name == u'志愿者'

    @property
    def is_moderator(self):
        return self.role.name == u'协管员'

    @property
    def is_administrator(self):
        return self.role.name == u'管理员'

    @property
    def is_developer(self):
        return self.role.name == u'开发人员'

    def is_superior_than(self, user):
        if self.is_developer:
            if not user.is_developer:
                return True
        if self.is_administrator:
            if not (user.is_developer or user.is_administrator):
                return True
        if self.is_moderator:
            if not (user.is_developer or user.is_administrator or user.is_moderator):
                return True
        if self.is_volunteer:
            if not (user.is_developer or user.is_administrator or user.is_moderator or user.is_volunteer):
                return True
        return False

    def ping(self):
        self.last_seen_at = datetime.utcnow()
        db.session.add(self)

    def generate_auth_token(self, expiration):
        serial = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return serial.dumps({'id': self.id}).decode('ascii')

    @staticmethod
    def verify_auth_token(token):
        serial = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = serial.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    @property
    def name_alias(self):
        return u'%s（%s）' % (self.name, self.email)

    @property
    def birthdate_alias(self):
        if self.birthdate:
            return u'%s年%s月%s日' % (self.birthdate.year, self.birthdate.month, self.birthdate.day)
        return u'无'

    @property
    def email_hash(self):
        return md5(self.email.encode('utf-8')).hexdigest()

    def avatar(self, size=512, default='identicon', rating='g', wrap=False):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        email_hash = md5(self.email.encode('utf-8')).hexdigest()
        base_url = '%s/%s' % (url, email_hash)
        payload = {
            's': size,
            'd': default,
            'r': rating,
        }
        avatar_url = '%s?%s' % (base_url, '&'.join(['%s=%s' % (key, payload[key]) for key in payload]))
        if wrap:
            payload['d'] = 404
            try:
                r = requests.get(base_url, params=payload)
                if r.status_code == 200:
                    return '<img class="ui small-avatar image" src="data:%s;base64,%s">' % (r.headers['Content-Type'], b64encode(r.content))
                else:
                    return '<i class="fa fa-user-circle-o"></i>'
            except Exception as e:
                return '<i class="fa fa-user-circle-o"></i>'
        return avatar_url

    def add_tag(self, tag):
        if not self.has_tag(tag):
            tag = UserTag(user_id=self.id, tag_id=tag.id)
            db.session.add(tag)

    def remove_tag(self, tag):
        tag = self.has_tags.filter_by(tag_id=tag.id).first()
        if tag:
            db.session.delete(tag)

    def has_tag(self, tag):
        return self.has_tags.filter_by(tag_id=tag.id).first() is not None

    def has_tag_name(self, tag_name):
        tag = Tag.query.filter_by(name=tag_name).first()
        return tag is not None and self.has_tag(tag)

    @property
    def has_tags_alias(self):
        if self.has_tags.count() == 0:
            return u'无'
        return u' · '.join([tag.tag.name for tag in self.has_tags if tag.tag.name])

    def add_education_record(self, education_type, school, year, major=None, gpa=None, full_gpa=None):
        if gpa and (not isinstance(gpa, float)):
            gpa = float(gpa)
        else:
            gpa = None
        if full_gpa and (not isinstance(full_gpa, float)):
            full_gpa = float(full_gpa)
        else:
            full_gpa = None
        education_record = EducationRecord(
            user_id=self.id,
            type_id=education_type.id,
            school=school,
            major=major,
            gpa=gpa,
            full_gpa=full_gpa,
            year=year
        )
        db.session.add(education_record)

    def add_employment_record(self, employer, position, year):
        employment_record = EmploymentRecord(
            user_id=self.id,
            employer=employer,
            position=position,
            year=year
        )
        db.session.add(employment_record)

    def add_score_record(self, score_type, score=None, full_score=None, remark=None):
        if score and (not isinstance(score, int)):
            score = int(score)
        else:
            score = None
        if full_score and (not isinstance(full_score, int)):
            full_score = int(full_score)
        else:
            full_score = None
        score_record = ScoreRecord(
            user_id=self.id,
            type_id=score_type.id,
            score=score,
            full_score=full_score,
            remark=remark
        )
        db.session.add(score_record)

    def add_purpose(self, purpose_type, remark=None):
        if not self.has_purpose(purpose_type):
            purpose = Purpose(user_id=self.id, type_id=purpose_type.id, remark=remark)
        else:
            purpose = self.purposes.filter_by(type_id=purpose_type.id).first()
            purpose.remark = remark
            purpose.timestamp = datetime.utcnow()
        db.session.add(purpose)

    def remove_purpose(self, purpose_type):
        purpose = self.purposes.filter_by(type_id=purpose_type.id).first()
        if purpose:
            db.session.delete(purpose)

    def has_purpose(self, purpose_type):
        return self.purposes.filter_by(type_id=purpose_type.id).first() is not None

    @property
    def purposes_alias(self):
        if self.purposes.count() == 0:
            return u'无'
        return u' · '.join([purpose.type.name for purpose in self.purposes if purpose.type.name != u'其它'] + [purpose.remark for purpose in self.purposes if purpose.type.name == u'其它'])

    def add_referrer(self, referrer_type, remark=None):
        if not self.has_referrer(referrer_type):
            referrer = Referrer(user_id=self.id, type_id=referrer_type.id, remark=remark)
        else:
            referrer = self.referrers.filter_by(type_id=referrer_type.id).first()
            referrer.remark = remark
            referrer.timestamp = datetime.utcnow()
        db.session.add(referrer)

    def remove_referrer(self, referrer_type):
        referrer = self.referrers.filter_by(type_id=referrer_type.id).first()
        if referrer:
            db.session.delete(referrer)

    def has_referrer(self, referrer_type):
        return self.referrers.filter_by(type_id=referrer_type.id).first() is not None

    @property
    def referrers_alias(self):
        if self.referrers.count() == 0:
            return u'无'
        return u' · '.join([referrer.type.name for referrer in self.referrers if referrer.type.name != u'其它'] + [referrer.remark for referrer in self.referrers if referrer.type.name == u'其它'])

    def add_purchase(self, product, quantity=1):
        purchase = Purchase(user_id=self.id, product_id=product.id, quantity=quantity)
        db.session.add(purchase)

    def update_group_registration_purchase(self, quantity):
        purchase = Purchase.query.filter_by(user_id=self.id, product_id=Product.query.filter_by(name=u'团报优惠').first().id).first()
        if purchase is not None:
            if quantity > 0:
                purchase.quantity = quantity
                purchase.timestamp = datetime.utcnow()
                db.session.add(purchase)
            else:
                db.session.delete(purchase)
        else:
            self.add_purchase(product=Product.query.filter_by(name=u'团报优惠').first(), quantity=quantity)

    @property
    def purchases_alias(self):
        if self.purchases.count() == 0:
            return u'无'
        return u' · '.join([purchase.alias for purchase in self.purchases])

    @property
    def purchases_total(self):
        return u'%g 元' % sum([purchase.total for purchase in self.purchases])

    def toggle_suspension(self, modified_by):
        if self.is_suspended:
            suspension_record = self.suspension_records.filter_by(end_datetime=None).order_by(SuspensionRecord.modified_at.desc()).first()
            if suspension_record is not None:
                suspension_record.end_datetime = datetime.utcnow()
                suspension_record.ping(modified_by=modified_by)
                db.session.add(suspension_record)
                self.role_id = suspension_record.original_role_id
                db.session.add(self)
                return False
            return True
        else:
            suspension_record = SuspensionRecord(user_id=self.id, original_role_id=self.role_id, modified_by_id=modified_by.id)
            db.session.add(suspension_record)
            self.role_id = Role.query.filter_by(name=u'挂起').first().id
            db.session.add(self)
            return True

    @property
    def due_datetime(self):
        if self.is_developer or self.is_administrator or self.is_moderator:
            return
        extended_years = sum([purchase.quantity for purchase in self.purchases.filter_by(product_id=Product.query.filter_by(name=u'一次性延长2年有效期').first().id)]) * 2
        extended_months = sum([purchase.quantity for purchase in self.purchases.filter_by(product_id=Product.query.filter_by(name=u'按月延长有效期').first().id)])
        year = self.activated_at.year + 1 + extended_years + (self.activated_at.month + extended_months) / 12
        month = (self.activated_at.month + extended_months) % 12
        day = self.activated_at.day
        suspended_time = reduce(lambda timedelta1, timedelta2: timedelta1 + timedelta2, [record.end_datetime - record.start_datetime for record in self.suspension_records if record.end_datetime is not None], timedelta(0))
        return datetime(year, month, day, self.activated_at.hour, self.activated_at.minute, self.activated_at.second, self.activated_at.microsecond) + suspended_time

    @property
    def overdue(self):
        if self.is_developer or self.is_administrator or self.is_moderator:
            return False
        return datetime.utcnow() > self.due_datetime

    def invite_user(self, user, invitation_type):
        if not self.invited_user(user):
            invitation = Invitation(inviter_id=self.id, user_id=user.id, type_id=invitation_type.id)
        else:
            invitation = self.sent_invitations.filter_by(user_id=user.id).first()
            invitation.type_id = invitation_type.id
            invitation.timestamp = datetime.utcnow()
        db.session.add(invitation)

    def uninvite_user(self, user):
        invitation = self.sent_invitations.filter_by(user_id=user.id).first()
        if invitation:
            db.session.delete(invitation)

    def invited_user(self, user):
        return self.sent_invitations.filter_by(user_id=user.id).first() is not None

    @property
    def inviters(self):
        if self.accepted_invitations.count() == 0:
            return u'无'
        return u' · '.join([u'%s（%s）[%s]' % (invitation.inviter.name, invitation.inviter.email, invitation.type.name) for invitation in self.accepted_invitations])

    def receive_user(self, user):
        if not self.received_user(user):
            reception = Reception(receptionist_id=self.id, user_id=user.id)
        else:
            reception = self.made_receptions.filter_by(user_id=user.id).first()
            reception.timestamp = datetime.utcnow()
        db.session.add(reception)

    def unreceive_user(self, user):
        reception = self.made_receptions.filter_by(user_id=user.id).first()
        if reception:
            db.session.delete(reception)

    def received_user(self, user):
        return self.made_receptions.filter_by(user_id=user.id).first() is not None

    @property
    def received_by(self):
        if self.received_receptions.count():
            return self.received_receptions.first().receptionist

    def create_user(self, user):
        user.created = True
        user.created_at = datetime.utcnow()
        db.session.add(user)
        db.session.commit()
        if not self.created_user(user):
            user_creation = UserCreation(creator_id=self.id, user_id=user.id, timestamp=user.created_at)
        else:
            user_creation = self.made_user_creations.filter_by(user_id=user.id).first()
            user_creation.timestamp = user.created_at
        db.session.add(user_creation)

    def uncreate_user(self, user):
        user_creation = self.made_user_creations.filter_by(user_id=user.id).first()
        if user_creation:
            db.session.delete(user_creation)

    def created_user(self, user):
        return self.made_user_creations.filter_by(user_id=user.id).first() is not None

    @property
    def created_by(self):
        return self.received_user_creations.first().creator

    def register_group(self, organizer):
        if not self.is_registering_group(organizer):
            group_registration = GroupRegistration(organizer_id=organizer.id, member_id=self.id)
        else:
            group_registration = self.registered_groups.filter_by(organizer_id=organizer.id).first()
            group_registration.timestamp = datetime.utcnow()
        db.session.add(group_registration)
        db.session.commit()
        for g_registration in organizer.organized_groups:
            g_registration.member.update_group_registration_purchase(quantity=organizer.organized_groups.count())

    def unregister_group(self, organizer):
        group_registration = self.registered_groups.filter_by(organizer_id=organizer.id).first()
        if group_registration:
            for g_registration in organizer.organized_groups:
                if g_registration.member_id != self.id:
                    g_registration.member.update_group_registration_purchase(quantity=organizer.organized_groups.count()-1)
                else:
                    g_registration.member.update_group_registration_purchase(quantity=0)
            db.session.delete(group_registration)

    def is_registering_group(self, organizer):
        return self.registered_groups.filter_by(organizer_id=organizer.id).first() is not None

    def register_course(self, course):
        if not self.is_registering_course(course):
            course_registration = CourseRegistration(user_id=self.id, course_id=course.id)
        else:
            course_registration = self.course_registrations.filter_by(course_id=course.id).first()
            course_registration.timestamp = datetime.utcnow()
        db.session.add(course_registration)

    def unregister_course(self, course):
        course_registration = self.course_registrations.filter_by(course_id=course.id).first()
        if course_registration:
            db.session.delete(course_registration)

    def is_registering_course(self, course):
        return self.course_registrations.filter_by(course_id=course.id).first() is not None

    @property
    def vb_course(self):
        return Course.query\
            .join(CourseRegistration, CourseRegistration.course_id == Course.id)\
            .join(CourseType, CourseType.id == Course.type_id)\
            .filter(CourseRegistration.user_id == self.id)\
            .filter(CourseType.name == u'VB')\
            .first()

    @property
    def y_gre_course(self):
        return Course.query\
            .join(CourseRegistration, CourseRegistration.course_id == Course.id)\
            .join(CourseType, CourseType.id == Course.type_id)\
            .filter(CourseRegistration.user_id == self.id)\
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
        booking = self.bookings.filter_by(schedule_id=schedule.id).first()
        if booking:
            booking.state_id = BookingState.query.filter_by(name=u'取消').first().id
            db.session.add(booking)
        # transfer to candidate if exist
        waited_booking = Booking.query\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .filter(Schedule.id == schedule.id)\
            .filter(BookingState.name == u'排队')\
            .order_by(Booking.timestamp.desc())\
            .first()
        if waited_booking:
            waited_booking.state_id = BookingState.query.filter_by(name=u'预约').first().id
            waited_booking.ping()
            db.session.add(waited_booking)
            return User.query.get(waited_booking.user_id)

    def miss(self, schedule):
        booking = self.bookings.filter_by(schedule_id=schedule.id).first()
        if booking:
            booking.state_id = BookingState.query.filter_by(name=u'爽约').first().id
            db.session.add(booking)

    def booked(self, schedule):
        return (self.bookings.filter_by(schedule_id=schedule.id).first() is not None) and\
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

    def booking_wait(self, schedule):
        return BookingState.query\
            .join(Booking, Booking.state_id == BookingState.id)\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .filter(Schedule.id == schedule.id)\
            .filter(Booking.user_id == self.id)\
            .filter(BookingState.name == u'排队')\
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
    def walk_in_rentals(self):
        return Rental.query.filter_by(user_id=self.id, walk_in=True)

    @property
    def fitted_ipads(self):
        return iPad.query\
            .join(iPadState, iPadState.id == iPad.state_id)\
            .join(iPadContent, iPadContent.ipad_id == iPad.id)\
            .join(Section, Section.lesson_id == iPadContent.lesson_id)\
            .join(Punch, Punch.section_id == Section.id)\
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

    def punch(self, section):
        timestamp = datetime.utcnow()
        if self.last_punch is None or section.order == 0:
            self.__punch(section=section, milestone=True)
            return
        if section.lesson.type_id == self.last_punch.section.lesson.type_id:
            if section.order > self.last_punch.section.order + 1:
                covered_sections = Section.query\
                    .join(Lesson, Lesson.id == Section.lesson_id)\
                    .filter(Lesson.type_id == section.lesson.type_id)\
                    .filter(and_(
                        Section.order > self.last_punch.section.order,
                        Section.order < section.order
                    ))\
                    .order_by(Section.order.asc())\
                    .all()
                for covered_section in covered_sections:
                    self.__punch(section=covered_section, timestamp=timestamp)
            if section.order < self.last_punch.section.order:
                uncovered_sections = Section.query\
                    .join(Lesson, Lesson.id == Section.lesson_id)\
                    .filter(Lesson.type_id == section.lesson.type_id)\
                    .filter(and_(
                        Section.order > section.order,
                        Section.order <= self.last_punch.section.order
                    ))\
                    .all()
                for uncovered_section in uncovered_sections:
                    self.__unpunch(section=uncovered_section)
            self.__punch(section=section, milestone=True, timestamp=timestamp)
            return
        if self.last_punch.section.lesson.type.name == u'VB' and section.lesson.type.name == u'Y-GRE':
            covered_sections = Section.query\
                .filter(Section.lesson_id == self.last_punch.section.lesson_id)\
                .filter(Section.order > self.last_punch.section.order)\
                .order_by(Section.order.asc())\
                .all() + \
                Section.query\
                .join(Lesson, Lesson.id == Section.lesson_id)\
                .filter(Lesson.type_id == section.lesson.type_id)\
                .filter(and_(
                    Section.order >= 1,
                    Section.order < section.order
                ))\
                .order_by(Section.order.asc())\
                .all()
            for covered_section in covered_sections:
                self.__punch(section=covered_section, timestamp=timestamp)
            self.__punch(section=section, milestone=True, timestamp=timestamp)
            return
        if self.last_punch.section.lesson.type.name == u'Y-GRE' and section.lesson.type.name == u'VB':
            uncovered_sections = Section.query\
                .join(Lesson, Lesson.id == Section.lesson_id)\
                .filter(Lesson.type_id == self.last_punch.section.lesson.type_id)\
                .filter(Section.order >= 1)\
                .all() + \
                Section.query\
                .join(Lesson, Lesson.id == Section.lesson_id)\
                .filter(Lesson.type_id == section.lesson.type_id)\
                .filter(Section.order > section.order)\
                .all()
            for uncovered_section in uncovered_sections:
                self.__unpunch(section=uncovered_section)
            covered_sections = Section.query\
                .join(Lesson, Lesson.id == Section.lesson_id)\
                .filter(Lesson.type_id == section.lesson.type_id)\
                .filter(and_(
                    Section.order > self.last_vb_punch.section.order,
                    Section.order < section.order
                ))\
                .order_by(Section.order.asc())\
                .all()
            for covered_section in covered_sections:
                self.__punch(section=covered_section, timestamp=timestamp)
            self.__punch(section=section, milestone=True, timestamp=timestamp)
            return

    def __initial_punch(self):
        self.__punch(section=Section.query.filter_by(name=u'Day 1-1').first(), milestone=True)

    def __punch(self, section, milestone=False, timestamp=datetime.utcnow()):
        if not self.punched(section):
            punch = Punch(user_id=self.id, section_id=section.id, milestone=milestone, timestamp=timestamp)
        else:
            punch = self.punches.filter_by(section_id=section.id).first()
            punch.milestone = milestone
            punch.timestamp = timestamp
        db.session.add(punch)

    def unpunch(self, section):
        if section.order == 0:
            self.__unpunch(section)

    def __unpunch(self, section):
        punch = self.punches.filter_by(section_id=section.id).first()
        if punch:
            db.session.delete(punch)

    def punched(self, section):
        return self.punches.filter_by(section_id=section.id).first() is not None

    @property
    def last_punch(self):
        if self.last_y_gre_punch is not None:
            return self.last_y_gre_punch
        return self.last_vb_punch

    @property
    def vb_punches(self):
        return Punch.query\
            .join(Section, Section.id == Punch.section_id)\
            .join(Lesson, Lesson.id == Section.lesson_id)\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(Punch.user_id == self.id)\
            .filter(CourseType.name == u'VB')\
            .order_by(Section.order.desc())

    @property
    def last_vb_punch(self):
        return self.vb_punches.filter(Section.order >= 1).first()

    @property
    def last_vb_punch_json(self):
        if self.last_vb_punch:
            return self.last_vb_punch.to_json()
        return None

    @property
    def y_gre_punches(self):
        return Punch.query\
            .join(Section, Section.id == Punch.section_id)\
            .join(Lesson, Lesson.id == Section.lesson_id)\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(Punch.user_id == self.id)\
            .filter(CourseType.name == u'Y-GRE')\
            .order_by(Section.order.desc())

    @property
    def last_y_gre_punch(self):
        return self.y_gre_punches.filter(Section.order >= 1).first()

    @property
    def last_y_gre_punch_json(self):
        if self.last_y_gre_punch:
            return self.last_y_gre_punch.to_json()
        return None

    @property
    def vb_progress_json(self):
        punched_sections = Punch.query\
            .join(Section, Section.id == Punch.section_id)\
            .join(Lesson, Lesson.id == Section.lesson_id)\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(Punch.user_id == self.id)\
            .filter(CourseType.name == u'VB')\
            .count()
        query = Section.query\
            .join(Lesson, Lesson.id == Section.lesson_id)\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(CourseType.name == u'VB')
        if self.can_access_advanced_vb:
            total_sections = query.count()
        else:
            total_sections = query.filter(Lesson.advanced == False).count()
        assignments = Assignment.query\
            .join(Lesson, Lesson.id == Assignment.lesson_id)\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(CourseType.name == u'VB')
        submitted_assignments = sum([self.submitted(assignment=assignment) is not None for assignment in assignments])
        total_assignments = assignments.count()
        tests = Test.query\
            .join(Lesson, Lesson.id == Test.lesson_id)\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(CourseType.name == u'VB')
        taken_tests = sum([self.taken_vb(test=test) is not None for test in tests])
        total_tests = tests.count()
        return {
            'value': punched_sections + submitted_assignments + taken_tests,
            'total': total_sections + total_assignments + total_tests,
            'percent': int(float(punched_sections + submitted_assignments + taken_tests) / (total_sections + total_assignments + total_tests) * 100),
        }

    @property
    def y_gre_progress_json(self):
        punched_sections = Punch.query\
            .join(Section, Section.id == Punch.section_id)\
            .join(Lesson, Lesson.id == Section.lesson_id)\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(Punch.user_id == self.id)\
            .filter(CourseType.name == u'Y-GRE')\
            .count()
        total_sections = Section.query\
            .join(Lesson, Lesson.id == Section.lesson_id)\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(CourseType.name == u'Y-GRE')\
            .filter(Section.order >= 1)\
            .count()
        assignments = Assignment.query\
            .join(Lesson, Lesson.id == Assignment.lesson_id)\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(CourseType.name == u'Y-GRE')
        submitted_assignments = sum([self.submitted(assignment=assignment) is not None for assignment in assignments])
        total_assignments = assignments.count()
        tests = Test.query\
            .join(Lesson, Lesson.id == Test.lesson_id)\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(CourseType.name == u'Y-GRE')
        taken_tests = sum([self.taken_y_gre(test=test) is not None for test in tests])
        total_tests = tests.count()
        return {
            'value': punched_sections + submitted_assignments + taken_tests,
            'total': total_sections + total_assignments + total_tests,
            'percent': int(float(punched_sections + submitted_assignments + taken_tests) / (total_sections + total_assignments + total_tests) * 100),
        }

    @property
    def next_punch(self):
        if self.last_punch.section.lesson.type.name == u'VB':
            return Section.query\
                .join(Lesson, Lesson.id == Section.lesson_id)\
                .join(CourseType, CourseType.id == Lesson.type_id)\
                .filter(CourseType.name == u'VB')\
                .filter(Section.order >= self.last_punch.section.order)\
                .order_by(Section.order.asc())\
                .limit(10)\
                .all() + \
                [Section.query.filter_by(name=u'Y-GRE总论').first()]
        if self.last_punch.section.lesson.type.name == u'Y-GRE':
            return Section.query\
                .join(Lesson, Lesson.id == Section.lesson_id)\
                .join(CourseType, CourseType.id == Lesson.type_id)\
                .filter(CourseType.name == u'Y-GRE')\
                .filter(Section.order >= self.last_punch.section.order)\
                .order_by(Section.order.asc())\
                .all()

    def add_toefl_test_score(self, test_date, total_score, reading_score, listening_score, speaking_score, writing_score, modified_by):
        test = TOEFLTest.query.filter_by(date=test_date).first()
        if test is None:
            test = TOEFLTest(date=test_date)
            db.session.add(test)
            db.session.commit()
        toefl_test_score = TOEFLTestScore(
            user_id=self.id,
            test_id=test.id,
            total_score=total_score,
            reading_score=reading_score,
            listening_score=listening_score,
            speaking_score=speaking_score,
            writing_score=writing_score,
            modified_by_id=modified_by.id
        )
        db.session.add(toefl_test_score)

    def submitted(self, assignment):
        return self.assignment_scores.filter_by(assignment_id=assignment.id).order_by(AssignmentScore.modified_at.desc()).first()

    @property
    def vb_assignment_scores(self):
        assignments = Assignment.query\
            .join(Lesson, Lesson.id == Assignment.lesson_id)\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(CourseType.name == u'VB')\
            .all()
        scores = []
        for assignment in assignments:
            score = self.submitted(assignment=assignment)
            if score is not None:
                scores.append(score)
        return scores

    def taken_vb(self, test):
        return self.vb_test_scores.filter_by(test_id=test.id).order_by(VBTestScore.modified_at.desc()).first()

    def taken_y_gre(self, test):
        return self.y_gre_test_scores.filter_by(test_id=test.id).order_by(YGRETestScore.modified_at.desc()).first()

    @property
    def vb_test_scores_alias(self):
        tests = Test.query\
            .join(Lesson, Lesson.id == Test.lesson_id)\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(CourseType.name == u'VB')\
            .all()
        scores = []
        for test in tests:
            score = self.taken_vb(test=test)
            if score is not None:
                scores.append(score)
        return scores

    @property
    def y_gre_test_scores_alias(self):
        tests = Test.query\
            .join(Lesson, Lesson.id == Test.lesson_id)\
            .join(CourseType, CourseType.id == Lesson.type_id)\
            .filter(CourseType.name == u'Y-GRE')\
            .all()
        scores = []
        for test in tests:
            score = self.taken_y_gre(test=test)
            if score is not None:
                scores.append(score)
        return scores

    @property
    def can_access_advanced_vb(self):
        vb_test_score = self.vb_test_scores.filter_by(test_id=Test.query.filter_by(name=u'L6-9').first().id).first()
        return vb_test_score is not None and vb_test_score.score >= 90.0

    def notified_by(self, announcement):
        return self.read_announcements.filter_by(announcement_id=announcement.id).first() is not None

    @property
    def gre_verbal_prediction(self):
        if self.has_tag_name(u'北大') or self.has_tag_name(u'清华'):
            if self.has_tag_name(u'竞赛') or self.has_tag_name(u'六级600+') or self.has_tag_name(u'GPA90+'):
                if self.has_tag_name(u'6th'):
                    return u'160+'
                if self.has_tag_name(u'3rd'):
                    return u'160-'
            else:
                if self.has_tag_name(u'6th'):
                    return u'155+'
                if self.has_tag_name(u'3rd'):
                    return u'155-'
        if self.has_tag_name(u'一本'):
            if self.has_tag_name(u'六级600+') or self.has_tag_name(u'高考数学135+'):
                if self.has_tag_name(u'6th'):
                    return u'155+'
                if self.has_tag_name(u'3rd'):
                    return u'155-'
            else:
                if self.has_tag_name(u'6th'):
                    return u'150+'
                if self.has_tag_name(u'3rd'):
                    return u'150-'
        if self.has_tag_name(u'非一本'):
            if self.has_tag_name(u'6th'):
                return u'145+'
            if self.has_tag_name(u'3rd'):
                return u'145-'

    def activate(self, new_password=None):
        self.activated = True
        self.activated_at = datetime.utcnow()
        if new_password:
            self.password = new_password
        db.session.add(self)
        self.__initial_punch()

    def to_json(self):
        user_json = {
            'name': self.name,
            'email': self.email,
            'name_alias': self.name_alias,
            'avatar': self.avatar(),
            'role': self.role.name,
            'last_punch': self.last_punch.to_json(),
            'last_seen_at': self.last_seen_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'url': url_for('main.profile_overview', id=self.id),
        }
        return user_json

    def to_json_suggestion(self, suggest_email=False, include_role=True, include_url=False):
        user_json_suggestion = {
            'image': self.avatar(size=80),
        }
        if suggest_email:
            user_json_suggestion['title'] = self.email
            if include_role:
                user_json_suggestion['description'] = u'%s [%s]' % (self.name, self.role.name)
            else:
                user_json_suggestion['description'] = self.name
        else:
            user_json_suggestion['title'] = self.name
            if include_role:
                user_json_suggestion['description'] = u'%s [%s]' % (self.email, self.role.name)
            else:
                user_json_suggestion['description'] = self.email
        if include_url:
            user_json_suggestion['url'] = url_for('main.profile_overview', id=self.id)
        return user_json_suggestion

    @staticmethod
    def insert_admin():
        admin = User.query.filter_by(email=current_app.config['YSYS_ADMIN']).first()
        if admin is None:
            admin = User(
                email=current_app.config['YSYS_ADMIN'],
                confirmed=True,
                role_id=Role.query.filter_by(name=u'开发人员').first().id,
                password=os.getenv('YSYS_ADMIN_PASSWORD'),
                activated=True,
                activated_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow(),
                name=u'SysOp'
            )
            db.session.add(admin)
            db.session.commit()
            admin.create_user(user=admin)
            admin.__initial_punch()
            db.session.commit()
            print u'初始化系统管理员信息'

    def __repr__(self):
        return '<User %r, %r>' % (self.name, self.email)


class AnonymousUser(AnonymousUserMixin):
    def can(self, permission_name):
        return False

    @property
    def is_suspended(self):
        return False

    @property
    def is_volunteer(self):
        return False

    @property
    def is_moderator(self):
        return False

    @property
    def is_administrator(self):
        return False

    @property
    def is_developer(self):
        return False

    def is_superior_than(self, user):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    color_id = db.Column(db.Integer, db.ForeignKey('colors.id'))
    tagged_users = db.relationship(
        'UserTag',
        foreign_keys=[UserTag.tag_id],
        backref=db.backref('tag', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @property
    def valid_tagged_users(self):
        return UserTag.query\
            .join(User, User.id == UserTag.user_id)\
            .filter(UserTag.tag_id == self.id)\
            .filter(User.created == True)\
            .filter(User.deleted == False)

    @staticmethod
    def insert_tags():
        tags = [
            (u'北大', u'Red', ),
            (u'清华', u'Purple', ),
            (u'一本', u'Blue', ),
            (u'非一本', u'Grey', ),
            (u'GPA90+', u'Teal', ),
            (u'竞赛', u'Teal', ),
            (u'六级600+', u'Teal', ),
            (u'高考数学135+', u'Teal', ),
            (u'3rd', u'Green', ),
            (u'6th', u'Green', ),
            (u'未缴纳齐全款', u'Red', ),
        ]
        for entry in tags:
            tag = Tag.query.filter_by(name=entry[0]).first()
            if tag is None:
                tag = Tag(
                    name=entry[0],
                    color_id=Color.query.filter_by(name=entry[1]).first().id
                )
                db.session.add(tag)
                print u'导入用户标签信息', entry[0], entry[1]
        db.session.commit()

    def __repr__(self):
        return '<Tag %r>' % self.name


class EducationType(db.Model):
    __tablename__ = 'education_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    education_records = db.relationship('EducationRecord', backref='type', lazy='dynamic')

    @staticmethod
    def insert_education_types():
        education_types = [
            (u'高中', ),
            (u'本科', ),
            (u'硕士', ),
            (u'博士', ),
        ]
        for entry in education_types:
            education_type = EducationType.query.filter_by(name=entry[0]).first()
            if education_type is None:
                education_type = EducationType(name=entry[0])
                db.session.add(education_type)
                print u'导入学历类型信息', entry[0]
        db.session.commit()

    def __repr__(self):
        return '<Education Type %r>' % self.name


class EducationRecord(db.Model):
    __tablename__ = 'education_records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('education_types.id'))
    school = db.Column(db.Unicode(64))
    major = db.Column(db.Unicode(64))
    gpa = db.Column(db.Float)
    full_gpa = db.Column(db.Float)
    year = db.Column(db.Unicode(16))

    @property
    def alias(self):
        return u'%s %s %s %s' % (self.user.name, self.type.name, self.school, self.year)

    @property
    def gpa_alias(self):
        if self.gpa is not None:
            return u'%g/%g' % (self.gpa, self.full_gpa)
        return u''

    @property
    def gpa_percentage(self):
        if self.full_gpa:
            return float(self.gpa) / float(self.full_gpa)
        return None

    @property
    def gpa_percentage_alias(self):
        if self.percentage:
            return u'%g%%' % (self.percentage * 100)
        return u'N/A'

    def __repr__(self):
        return '<Education Record %r>' % self.alias


class EmploymentRecord(db.Model):
    __tablename__ = 'employment_records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    employer = db.Column(db.Unicode(64))
    position = db.Column(db.Unicode(64))
    year = db.Column(db.Unicode(16))

    @property
    def alias(self):
        return u'%s %s %s %s' % (self.user.name, self.employer, self.position, self.year)

    def __repr__(self):
        return '<Education Record %r>' % self.alias


class ScoreType(db.Model):
    __tablename__ = 'score_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    score_records = db.relationship('ScoreRecord', backref='type', lazy='dynamic')

    @staticmethod
    def insert_score_types():
        score_types = [
            (u'高考总分', ),
            (u'高考数学', ),
            (u'高考英语', ),
            (u'大学英语四级', ),
            (u'大学英语六级', ),
            (u'专业英语四级', ),
            (u'专业英语八级', ),
            (u'竞赛', ),
            (u'其它', ),
        ]
        for entry in score_types:
            score_type = ScoreType.query.filter_by(name=entry[0]).first()
            if score_type is None:
                score_type = ScoreType(name=entry[0])
                db.session.add(score_type)
                print u'导入既往成绩类型信息', entry[0]
        db.session.commit()

    def __repr__(self):
        return '<Score Record Type %r>' % self.name


class ScoreRecord(db.Model):
    __tablename__ = 'score_records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('score_types.id'))
    score = db.Column(db.Integer)
    full_score = db.Column(db.Integer)
    remark = db.Column(db.UnicodeText)

    @property
    def alias(self):
        return u'%s %s %s' % (self.user.name_alias, self.type.name, self.score_alias)

    @property
    def score_alias(self):
        if self.score:
            if self.full_score:
                return u'%g/%g 分' % (self.score, self.full_score)
            return u'%g 分' % self.score
        elif self.remark:
            return u'%s' % self.remark
        else:
            return u'N/A'

    @property
    def percentage(self):
        if self.full_score:
            return float(self.score) / float(self.full_score)
        return None

    @property
    def percentage_alias(self):
        if self.percentage:
            return u'%g%%' % (self.percentage * 100)
        return u'N/A'

    def __repr__(self):
        return '<Score Record %r>' % self.alias


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), index=True)
    price = db.Column(db.Float, default=0.0)
    available = db.Column(db.Boolean, default=False)
    fixed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    deleted = db.Column(db.Boolean, default=False)
    purchases = db.relationship(
        'Purchase',
        foreign_keys=[Purchase.product_id],
        backref=db.backref('product', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def ping(self, modified_by):
        self.modified_at = datetime.utcnow()
        self.modified_by_id = modified_by.id
        db.session.add(self)

    def safe_delete(self, modified_by):
        self.deleted = True
        self.ping(modified_by=modified_by)
        db.session.add(self)

    def toggle_availability(self, modified_by):
        self.available = not self.available
        self.ping(modified_by=modified_by)
        db.session.add(self)

    @property
    def alias(self):
        return u'%s [%g元]' % (self.name, self.price)

    @property
    def price_alias(self):
        return u'%g' % self.price

    @property
    def sales_volume(self):
        return sum([purchase.quantity for purchase in self.purchases if purchase.user.created and purchase.user.activated and not purchase.user.deleted])

    @staticmethod
    def insert_products():
        products = [
            (u'VB基本技术费', 6800.0, True, False, ),
            (u'Y-GRE基本技术费', 6800.0, True, False, ),
            (u'联报优惠', -1000.0, True, False, ),
            (u'在校生减免', -800.0, True, False, ),
            (u'本校减免', -500.0, True, False, ),
            (u'团报优惠', -200.0, True, True, ),
            (u'AW费用', 800.0, True, False, ),
            (u'Q费用', 800.0, True, False, ),
            (u'Y-GRE多轮费用', 2000.0, True, False, ),
            (u'按月延长有效期', 1000.0, True, True, ),
            (u'一次性延长2年有效期', 3000.0, True, True, ),
        ]
        for entry in products:
            product = Product.query.filter_by(name=entry[0]).first()
            if product is None:
                product = Product(
                    name=entry[0],
                    price=entry[1],
                    available=entry[2],
                    fixed=entry[3],
                    modified_by_id=User.query.get(1).id
                )
                db.session.add(product)
                print u'导入课程类型信息', entry[0]
        db.session.commit()

    def __repr__(self):
        return '<Product %r>' % self.alias


class CourseType(db.Model):
    __tablename__ = 'course_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    lessons = db.relationship('Lesson', backref='type', lazy='dynamic')
    courses = db.relationship('Course', backref='type', lazy='dynamic')
    periods = db.relationship('Period', backref='type', lazy='dynamic')

    @property
    def alias(self):
        return self.name.lower()

    @staticmethod
    def insert_course_types():
        course_types = [
            (u'VB', ),
            (u'Y-GRE', ),
        ]
        for entry in course_types:
            course_type = CourseType.query.filter_by(name=entry[0]).first()
            if course_type is None:
                course_type = CourseType(name=entry[0])
                db.session.add(course_type)
                print u'导入课程类型信息', entry[0]
        db.session.commit()

    def __repr__(self):
        return '<Course Type %r>' % self.name


class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), index=True)
    type_id = db.Column(db.Integer, db.ForeignKey('course_types.id'))
    show = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    deleted = db.Column(db.Boolean, default=False)
    registrations = db.relationship(
        'CourseRegistration',
        foreign_keys=[CourseRegistration.course_id],
        backref=db.backref('course', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def ping(self, modified_by):
        self.modified_at = datetime.utcnow()
        self.modified_by_id = modified_by.id
        db.session.add(self)

    def safe_delete(self, modified_by):
        self.show = False
        self.deleted = True
        self.ping(modified_by=modified_by)
        db.session.add(self)

    def toggle_show(self, modified_by):
        self.show = not self.show
        self.ping(modified_by=modified_by)
        db.session.add(self)

    @property
    def valid_registrations(self):
        return CourseRegistration.query\
            .join(User, User.id == CourseRegistration.user_id)\
            .filter(CourseRegistration.course_id == self.id)\
            .filter(User.created == True)\
            .filter(User.deleted == False)

    @staticmethod
    def insert_courses():
        import xlrd
        data = xlrd.open_workbook('initial-courses.xlsx')
        table = data.sheet_by_index(0)
        courses = [table.row_values(row) for row in range(table.nrows) if row >= 1]
        for entry in courses:
            course = Course.query.filter_by(name=entry[0]).first()
            if course is None:
                course = Course(
                    name=entry[0],
                    type_id=CourseType.query.filter_by(name=entry[1]).first().id,
                    modified_by_id=User.query.get(1).id
                )
                db.session.add(course)
                print u'导入课程信息', entry[0], entry[1]
        db.session.commit()

    def __repr__(self):
        return '<Course %r>' % self.name


class Period(db.Model):
    __tablename__ = 'periods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    type_id = db.Column(db.Integer, db.ForeignKey('course_types.id'))
    show = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    deleted = db.Column(db.Boolean, default=False)
    schedules = db.relationship('Schedule', backref='period', lazy='dynamic')

    def ping(self, modified_by):
        self.modified_at = datetime.utcnow()
        self.modified_by_id = modified_by.id
        db.session.add(self)

    def safe_delete(self, modified_by):
        self.show = False
        self.deleted = True
        self.ping(modified_by=modified_by)
        db.session.add(self)

    def toggle_show(self, modified_by):
        self.show = not self.show
        self.ping(modified_by=modified_by)
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
            'course_type': self.type.name,
            'show': self.show,
            'modified_at': self.modified_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'modified_by': self.modified_by.name,
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
        for entry in periods:
            period = Period.query.filter_by(name=entry[0]).first()
            if period is None:
                period = Period(
                    name=entry[0],
                    start_time=entry[1],
                    end_time=entry[2],
                    type_id=CourseType.query.filter_by(name=entry[3]).first().id,
                    modified_by_id=User.query.get(1).id
                )
                db.session.add(period)
                print u'导入时段信息', entry[0], entry[1], entry[2], entry[3]
        db.session.commit()

    def __repr__(self):
        return '<Period %r>' % self.alias


class Schedule(db.Model):
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, index=True)
    period_id = db.Column(db.Integer, db.ForeignKey('periods.id'))
    quota = db.Column(db.Integer, default=0)
    available = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    booked_users = db.relationship(
        'Booking',
        foreign_keys=[Booking.schedule_id],
        backref=db.backref('schedule', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    schedules = db.relationship('Rental', backref='schedule', lazy='dynamic')

    def ping(self, modified_by):
        self.modified_at = datetime.utcnow()
        self.modified_by_id = modified_by.id
        db.session.add(self)

    def publish(self, modified_by):
        self.available = True
        self.ping(modified_by=modified_by)
        db.session.add(self)

    def retract(self, modified_by):
        self.available = False
        self.ping(modified_by=modified_by)
        db.session.add(self)

    def increase_quota(self, modified_by):
        self.quota += 1
        self.ping(modified_by=modified_by)
        db.session.add(self)
        waited_booking = Booking.query\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .join(Schedule, Schedule.id == Booking.schedule_id)\
            .filter(Schedule.id == self.id)\
            .filter(BookingState.name == u'排队')\
            .order_by(Booking.timestamp.desc())\
            .first()
        if waited_booking:
            waited_booking.state_id = BookingState.query.filter_by(name=u'预约').first().id
            waited_booking.ping()
            db.session.add(waited_booking)
            return User.query.get(waited_booking.user_id)

    def decrease_quota(self, modified_by):
        if self.quota > 0:
            self.quota += -1
            self.ping(modified_by=modified_by)
            db.session.add(self)

    @property
    def today(self):
        return self.date == date.today()

    @property
    def out_of_date(self):
        return self.date < date.today()

    @property
    def time_state(self):
        start_time_utc = datetime(self.date.year, self.date.month, self.date.day, self.period.start_time.hour, self.period.start_time.minute) - timedelta(hours=current_app.config['UTC_OFFSET'])
        end_time_utc = datetime(self.date.year, self.date.month, self.date.day, self.period.end_time.hour, self.period.end_time.minute) - timedelta(hours=current_app.config['UTC_OFFSET'])
        if datetime.utcnow() < start_time_utc:
            return u'未开始'
        if start_time_utc <= datetime.utcnow() and datetime.utcnow() <= end_time_utc:
            return u'进行中'
        if end_time_utc < datetime.utcnow():
            return u'已结束'

    @property
    def unstarted(self):
        return datetime.utcnow() < datetime(self.date.year, self.date.month, self.date.day, self.period.start_time.hour, self.period.start_time.minute) - timedelta(hours=current_app.config['UTC_OFFSET'])

    def unstarted_n_min(self, n_min):
        return datetime.utcnow() < datetime(self.date.year, self.date.month, self.date.day, self.period.start_time.hour, self.period.start_time.minute) - timedelta(hours=current_app.config['UTC_OFFSET']) + timedelta(minutes=n_min)

    @property
    def started(self):
        return datetime(self.date.year, self.date.month, self.date.day, self.period.start_time.hour, self.period.start_time.minute) - timedelta(hours=current_app.config['UTC_OFFSET']) <= datetime.utcnow() and datetime.utcnow() <= datetime(self.date.year, self.date.month, self.date.day, self.period.end_time.hour, self.period.end_time.minute) - timedelta(hours=current_app.config['UTC_OFFSET'])

    def started_n_min(self, n_min):
        return datetime(self.date.year, self.date.month, self.date.day, self.period.start_time.hour, self.period.start_time.minute) - timedelta(hours=current_app.config['UTC_OFFSET']) + timedelta(minutes=n_min) <= datetime.utcnow() and datetime.utcnow() <= datetime(self.date.year, self.date.month, self.date.day, self.period.end_time.hour, self.period.end_time.minute) - timedelta(hours=current_app.config['UTC_OFFSET'])

    @property
    def ended(self):
        return datetime(self.date.year, self.date.month, self.date.day, self.period.end_time.hour, self.period.end_time.minute) - timedelta(hours=current_app.config['UTC_OFFSET']) < datetime.utcnow()

    def is_booked_by(self, user):
        return (self.booked_users.filter_by(user_id=user.id).first() is not None) and\
            (Booking.query.filter_by(user_id=user.id, schedule_id=self.id).first().canceled == False) and\
            (Booking.query.filter_by(user_id=user.id, schedule_id=self.id).first().invalid == False)

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

    @staticmethod
    def current_schedule(type_name):
        for schedule in Schedule.query\
            .join(Period, Period.id == Schedule.period_id)\
            .join(CourseType, CourseType.id == Period.type_id)\
            .filter(CourseType.name == type_name)\
            .filter(or_(
                Schedule.date == date.today() - timedelta(days=1),
                Schedule.date == date.today(),
                Schedule.date == date.today() + timedelta(days=1),
            ))\
            .all():
            if schedule.started:
                return schedule
        return None

    def booked_ipads_quantity(self, lesson):
        return Booking.query\
            .join(BookingState, BookingState.id == Booking.state_id)\
            .join(Punch, Punch.user_id == Booking.user_id)\
            .join(Section, Section.id == Punch.section_id)\
            .filter(Booking.schedule_id == self.id)\
            .filter(BookingState.name == u'预约')\
            .filter(Section.lesson_id == lesson.id)\
            .count()

    def to_json(self):
        schedule_json = {
            'date': self.date,
            'period': self.period.to_json(),
            'quota': self.quota,
            'available': self.available,
            'modified_at': self.modified_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'modified_by': self.modified_by.name,
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
            (u'256GB', ),
        ]
        for entry in ipad_capacities:
            ipad_capacity = iPadCapacity.query.filter_by(name=entry[0]).first()
            if ipad_capacity is None:
                ipad_capacity = iPadCapacity(name=entry[0])
                db.session.add(ipad_capacity)
                print u'导入iPad容量信息', entry[0]
        db.session.commit()

    def __repr__(self):
        return '<iPad Capacity %r>' % self.name


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
        for entry in ipad_states:
            ipad_state = iPadState.query.filter_by(name=entry[0]).first()
            if ipad_state is None:
                ipad_state = iPadState(name=entry[0])
                db.session.add(ipad_state)
                print u'导入iPad状态信息', entry[0]
        db.session.commit()

    def __repr__(self):
        return '<iPad State %r>' % self.name


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
        for entry in rooms:
            room = Room.query.filter_by(name=entry[0]).first()
            if room is None:
                room = Room(name=entry[0])
                db.session.add(room)
                print u'导入房间信息', entry[0]
        db.session.commit()

    def __repr__(self):
        return '<Room %r>' % self.name


class iPadContent(db.Model):
    __tablename__ = 'ipad_contents'
    ipad_id = db.Column(db.Integer, db.ForeignKey('ipads.id'), primary_key=True, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), primary_key=True, index=True)

    def to_json(self):
        ipad_content_json = {
            'ipad': self.ipad.alias,
            'lesson': self.lesson.name,
            'element_id': 'ipad-%s-lesson-%s' % (self.ipad_id, self.lesson_id),
        }
        return ipad_content_json

    @staticmethod
    def insert_ipad_contents():
        import xlrd
        data = xlrd.open_workbook('initial-ipad-contents.xlsx')
        table = data.sheet_by_index(0)
        lesson_ids = [Lesson.query.filter_by(name=value).first().id for value in table.row_values(0) if Lesson.query.filter_by(name=value).first()]
        ipad_contents = [table.row_values(row) for row in range(table.nrows) if row >= 1]
        for entry in ipad_contents:
            ipad_id = iPad.query.filter_by(alias=entry[0]).first().id
            for exist_lesson, lesson_id in zip(entry[1:], lesson_ids):
                if exist_lesson:
                    if iPadContent.query.filter_by(ipad_id=ipad_id, lesson_id=lesson_id).first() is None:
                        ipad_content = iPadContent(
                            ipad_id=ipad_id,
                            lesson_id=lesson_id,
                        )
                        db.session.add(ipad_content)
                        print u'导入iPad内容信息', entry[0], Lesson.query.get(lesson_id).name
        db.session.commit()


class iPad(db.Model):
    __tablename__ = 'ipads'
    id = db.Column(db.Integer, primary_key=True)
    serial = db.Column(db.Unicode(64), index=True)
    alias = db.Column(db.Unicode(64), index=True)
    capacity_id = db.Column(db.Integer, db.ForeignKey('ipad_capacities.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    state_id = db.Column(db.Integer, db.ForeignKey('ipad_states.id'))
    video_playback = db.Column(db.Interval, default=timedelta(hours=10))
    battery_life = db.Column(db.Integer, default=100)
    charged_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    deleted = db.Column(db.Boolean, default=False)
    contents = db.relationship(
        'iPadContent',
        foreign_keys=[iPadContent.ipad_id],
        backref=db.backref('ipad', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    rentals = db.relationship('Rental', backref='ipad', lazy='dynamic')

    def ping(self, modified_by):
        self.modified_at = datetime.utcnow()
        self.modified_by_id = modified_by.id
        db.session.add(self)

    def safe_delete(self, modified_by):
        self.serial = u'%s_%s_deleted' % (self.serial, self.id)
        self.alias = u'%s_%s_deleted' % (self.alias, self.id)
        self.state_id = iPadState.query.filter_by(name=u'退役').first().id
        for content in self.contents:
            self.remove_lesson(lesson=content.lesson)
        self.deleted = True
        self.ping(modified_by=modified_by)
        db.session.add(self)

    def set_state(self, state_name, modified_by, battery_life=-1):
        self.state_id = iPadState.query.filter_by(name=state_name).first().id
        if battery_life > -1:
            self.battery_life = battery_life
            self.charged_at = datetime.utcnow()
        self.ping(modified_by=modified_by)
        db.session.add(self)

    def add_lesson(self, lesson):
        if not self.has_lesson(lesson):
            ipad_content = iPadContent(ipad_id=self.id, lesson_id=lesson.id)
            db.session.add(ipad_content)

    def remove_lesson(self, lesson):
        ipad_content = self.contents.filter_by(lesson_id=lesson.id).first()
        if ipad_content:
            db.session.delete(ipad_content)

    def has_lesson(self, lesson):
        return self.contents.filter_by(lesson_id=lesson.id).first() is not None

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
    def vb_lesson_ids_included_unicode(self):
        vb_lessons = self.has_vb_lessons
        return [unicode(vb_lesson.id) for vb_lesson in vb_lessons]

    @property
    def y_gre_lesson_ids_included(self):
        y_gre_lessons = self.has_y_gre_lessons
        return [y_gre_lesson.id for y_gre_lesson in y_gre_lessons]

    @property
    def y_gre_lesson_ids_included_unicode(self):
        y_gre_lessons = self.has_y_gre_lessons
        return [unicode(y_gre_lesson.id) for y_gre_lesson in y_gre_lessons]

    @property
    def video_playback_alias(self):
        return u'%g 小时' % (self.video_playback.total_seconds() / 3600)

    @property
    def current_battery_life(self):
        delta = datetime.utcnow() - self.charged_at
        current_battery_life = self.battery_life - int(delta.total_seconds() / self.video_playback.total_seconds() * 100)
        if current_battery_life < 0:
            return 0
        if current_battery_life > 100:
            return 100
        return current_battery_life

    @property
    def current_battery_life_level(self):
        if self.current_battery_life <= 10:
            return u'empty'
        elif self.current_battery_life > 10 and self.current_battery_life <= 35:
            return u'low'
        elif self.current_battery_life > 35 and self.current_battery_life <= 65:
            return u'medium'
        elif self.current_battery_life > 65 and self.current_battery_life <= 90:
            return u'high'
        elif self.current_battery_life > 90 and self.current_battery_life <= 100:
            return u'full'

    @property
    def now_rented_by(self):
        if self.current_rental is not None:
            return self.current_rental.user

    @property
    def current_rental(self):
        return Rental.query\
            .filter_by(ipad_id=self.id, returned=False)\
            .first()

    @staticmethod
    def quantity_in_room(room_name, state_name=None):
        if state_name:
            return iPad.query\
                .join(Room, Room.id == iPad.room_id)\
                .join(iPadState, iPadState.id == iPad.state_id)\
                .filter(Room.name == room_name)\
                .filter(iPadState.name == state_name)\
                .filter(iPad.deleted == False)\
                .count()
        return iPad.query\
            .join(Room, Room.id == iPad.room_id)\
            .filter(Room.name == room_name)\
            .filter(iPad.deleted == False)\
            .count()

    def to_json(self):
        ipad_json = {
            'id': self.id,
            'serial': self.serial,
            'alias': self.alias,
            'capacity': self.capacity.name,
            'state': self.state.name,
            'modified_at': self.modified_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'modified_by': self.modified_by.name,
        }
        if self.state.name == u'待机':
            ipad_json['maintain_url'] = url_for('manage.set_ipad_state_maintain', id=self.id, next=url_for('manage.summary'))
            ipad_json['charge_url'] = url_for('manage.set_ipad_state_charge', id=self.id, next=url_for('manage.summary'))
        if self.state.name == u'维护':
            ipad_json['standby_url'] = url_for('manage.set_ipad_state_standby', id=self.id, next=url_for('manage.summary'))
            ipad_json['charge_url'] = url_for('manage.set_ipad_state_charge', id=self.id, next=url_for('manage.summary'))
        if self.state.name == u'充电':
            ipad_json['standby_url'] = url_for('manage.set_ipad_state_standby', id=self.id, next=url_for('manage.summary'))
            ipad_json['maintain_url'] = url_for('manage.set_ipad_state_maintain', id=self.id, next=url_for('manage.summary'))
        if self.state.name == u'借出':
            ipad_json['now_rented_by'] = self.now_rented_by.to_json()
            ipad_json['battery_life'] = {
                'percent': self.current_battery_life,
                'level': self.current_battery_life_level,
            }
            ipad_json['overtime'] = self.current_rental.is_overtime
            ipad_json['return_url'] = url_for('manage.rental_return_step_1', next=url_for('manage.summary'))
            ipad_json['exchange_url'] = url_for('manage.rental_exchange_step_1', rental_id=self.current_rental.id, next=url_for('manage.summary'))
        return ipad_json

    @staticmethod
    def insert_ipads():
        import xlrd
        data = xlrd.open_workbook('initial-ipads.xlsx')
        table = data.sheet_by_index(0)
        ipads = [table.row_values(row) for row in range(table.nrows) if row >= 1]
        for entry in ipads:
            if isinstance(entry[3], float):
                entry[3] = int(entry[3])
            ipad = iPad.query.filter_by(serial=entry[1]).first()
            if ipad is None:
                ipad = iPad(
                    serial=entry[1].upper(),
                    alias=entry[0],
                    capacity_id=iPadCapacity.query.filter_by(name=entry[2]).first().id,
                    room_id=Room.query.filter_by(name=unicode(str(entry[3]))).first().id,
                    state_id=iPadState.query.filter_by(name=entry[4]).first().id,
                    modified_by_id=User.query.get(1).id
                )
                print u'导入iPad信息', entry[1], entry[0], entry[2], entry[3], entry[4]
                db.session.add(ipad)
        db.session.commit()

    def __repr__(self):
        return '<iPad %r, %r>' % (self.alias, self.serial)


class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    type_id = db.Column(db.Integer, db.ForeignKey('course_types.id'))
    hour = db.Column(db.Interval, default=timedelta(hours=0))
    priority = db.Column(db.Integer, default=0)
    order = db.Column(db.Integer, default=0)
    include_video = db.Column(db.Boolean, default=False)
    advanced = db.Column(db.Boolean, default=False)
    sections = db.relationship('Section', backref='lesson', lazy='dynamic')
    assignments = db.relationship('Assignment', backref='lesson', lazy='dynamic')
    tests = db.relationship('Test', backref='lesson', lazy='dynamic')
    occupied_ipads = db.relationship(
        'iPadContent',
        foreign_keys=[iPadContent.lesson_id],
        backref=db.backref('lesson', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @property
    def alias(self):
        return u'%s - %s' % (self.type.name, self.name)

    @property
    def abbr(self):
        abbreviations = {
            u'词典使用': u'词',
            u'VB总论': u'总',
            u'L1': u'1',
            u'L2': u'2',
            u'L3': u'3',
            u'L4': u'4',
            u'L5': u'5',
            u'L6': u'6',
            u'L7': u'7',
            u'L8': u'8',
            u'L9': u'9',
            u'L10': u'10',
            u'L11': u'11',
            u'L12': u'12',
            u'L13': u'13',
            u'L14': u'14',
            u'Y-GRE总论': u'总',
            u'1st': u'1',
            u'2nd': u'2',
            u'3rd': u'3',
            u'4th': u'4',
            u'5th': u'5',
            u'6th': u'6',
            u'7th': u'7',
            u'8th': u'8',
            u'9th': u'9',
            u'Test': u'T',
            u'AW总论': u'A',
        }
        return abbreviations[self.name]

    @property
    def hour_alias(self):
        if self.hour.total_seconds():
            return u'%g 小时' % (self.hour.total_seconds() / 3600)
        return u'N/A'

    @property
    def occupied_ipads_alias(self):
        return iPadContent.query\
            .join(iPad, iPad.id == iPadContent.ipad_id)\
            .filter(iPadContent.lesson_id == self.id)\
            .filter(iPad.deleted == False)

    @property
    def available_ipads(self):
        return iPad.query\
            .join(iPadState, iPadState.id == iPad.state_id)\
            .join(iPadContent, iPadContent.ipad_id == iPad.id)\
            .filter(iPad.deleted == False)\
            .filter(iPadState.name != u'退役')\
            .filter(iPadContent.lesson_id == self.id)

    def to_json(self):
        lesson_json = {
            'name': self.name,
            'alias': self.alias,
            'abbr': self.abbr,
            'course_type': self.type.name,
            'hour': self.hour_alias,
            'priority': self.priority,
            'order': self.order,
            'include_video': self.include_video,
            'advanced': self.advanced,
            'sections': [section.to_json() for section in self.sections],
            'assignments': [assignment.to_json() for assignment in self.assignments],
            'tests': [test.to_json() for test in self.tests],
            'element_id': '%s-lesson-%s' % (self.type.alias, self.id),
        }
        return lesson_json

    @staticmethod
    def insert_lessons():
        lessons = [
            (u'词典使用', u'VB', 0, 0, 0, False, False, ),
            (u'VB总论', u'VB', 20, 16, 1, True, False, ),
            (u'L1', u'VB', 8, 15, 2, True, False, ),
            (u'L2', u'VB', 8, 14, 3, True, False, ),
            (u'L3', u'VB', 8, 13, 4, True, False, ),
            (u'L4', u'VB', 8, 12, 5, True, False, ),
            (u'L5', u'VB', 8, 11, 6, True, False, ),
            (u'L6', u'VB', 10, 7, 7, True, False, ),
            (u'L7', u'VB', 10, 6, 8, True, False, ),
            (u'L8', u'VB', 10, 5, 9, True, False, ),
            (u'L9', u'VB', 10, 4, 10, True, False, ),
            (u'L10', u'VB', 0, 0, 11, False, False, ),
            (u'L11', u'VB', 10, -1, 12, True, True, ),
            (u'L12', u'VB', 10, -1, 13, True, True, ),
            (u'L13', u'VB', 10, -1, 14, True, True, ),
            (u'L14', u'VB', 10, -1, 15, True, True, ),
            (u'Y-GRE总论', u'Y-GRE', 10, 17, 1, True, False, ),
            (u'1st', u'Y-GRE', 30, 17, 2, True, False, ),
            (u'2nd', u'Y-GRE', 30, 17, 3, True, False, ),
            (u'3rd', u'Y-GRE', 50, 17, 4, True, False, ),
            (u'AW总论', u'Y-GRE', 3, 17, 5, True, False, ),
            (u'4th', u'Y-GRE', 30, 10, 6, True, False, ),
            (u'5th', u'Y-GRE', 40, 9, 7, True, False, ),
            (u'6th', u'Y-GRE', 40, 8, 8, True, False, ),
            (u'7th', u'Y-GRE', 30, 3, 9, True, False, ),
            (u'8th', u'Y-GRE', 30, 2, 10, True, False, ),
            (u'9th', u'Y-GRE', 30, 1, 11, True, False, ),
            (u'Test', u'Y-GRE', 0, 0, -1, True, False, ),
        ]
        for entry in lessons:
            lesson = Lesson.query.filter_by(name=entry[0]).first()
            if lesson is None:
                lesson = Lesson(
                    name=entry[0],
                    type_id=CourseType.query.filter_by(name=entry[1]).first().id,
                    hour=timedelta(hours=entry[2]),
                    priority=entry[3],
                    order=entry[4],
                    include_video=entry[5],
                    advanced=entry[6]
                )
                db.session.add(lesson)
                print u'导入课程信息', entry[0], entry[1]
        db.session.commit()

    def __repr__(self):
        return '<Lesson %r>' % self.alias


class Section(db.Model):
    __tablename__ = 'sections'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'))
    order = db.Column(db.Integer, default=0)
    punches = db.relationship(
        'Punch',
        foreign_keys=[Punch.section_id],
        backref=db.backref('section', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @property
    def alias(self):
        if self.lesson.sections.count() > 1:
            return u'%s - %s' % (self.lesson.name, self.name)
        return u'%s' % self.name

    @property
    def alias2(self):
        return u'%s - %s' % (self.lesson.type.name, self.alias)

    @property
    def abbr(self):
        if self.name[:3] == u'Day':
            return u'0.%s%s' % (self.name[4], self.name[6])
        return self.name

    def to_json(self):
        section_json = {
            'name': self.name,
            'alias': self.alias,
            'alias2': self.alias2,
            'abbr': self.abbr,
            'lesson': self.lesson.name,
            'course_type': self.lesson.type.name,
            'order': self.order,
            'element_id': '%s-lesson-%s-section-%s' % (self.lesson.type.alias, self.lesson.id, self.id),
        }
        return section_json

    @staticmethod
    def insert_sections():
        sections = [
            (u'词典使用', u'词典使用', 0, ),
            (u'Day 1-1', u'VB总论', 1, ),
            (u'Day 1-2', u'VB总论', 2, ),
            (u'Day 1-3', u'VB总论', 3, ),
            (u'Day 1-4', u'VB总论', 4, ),
            (u'Day 2-1', u'VB总论', 5, ),
            (u'Day 2-2', u'VB总论', 6, ),
            (u'Day 2-3', u'VB总论', 7, ),
            (u'Day 2-4', u'VB总论', 8, ),
            (u'Day 3-1', u'VB总论', 9, ),
            (u'Day 3-2', u'VB总论', 10, ),
            (u'Day 3-3', u'VB总论', 11, ),
            (u'Day 3-4', u'VB总论', 12, ),
            (u'Day 4-1', u'VB总论', 13, ),
            (u'Day 4-2', u'VB总论', 14, ),
            (u'Day 4-3', u'VB总论', 15, ),
            (u'Day 4-4', u'VB总论', 16, ),
            (u'1.1', u'L1', 17, ),
            (u'1.2', u'L1', 18, ),
            (u'1.3', u'L1', 19, ),
            (u'1.4', u'L1', 20, ),
            (u'1.5', u'L1', 21, ),
            (u'1.6', u'L1', 22, ),
            (u'1.7', u'L1', 23, ),
            (u'1.8', u'L1', 24, ),
            (u'2.1', u'L2', 25, ),
            (u'2.2', u'L2', 26, ),
            (u'2.3', u'L2', 27, ),
            (u'2.4', u'L2', 28, ),
            (u'2.5', u'L2', 29, ),
            (u'2.6', u'L2', 30, ),
            (u'2.7', u'L2', 31, ),
            (u'2.8', u'L2', 32, ),
            (u'3.1', u'L3', 33, ),
            (u'3.2', u'L3', 34, ),
            (u'3.3', u'L3', 35, ),
            (u'3.4', u'L3', 36, ),
            (u'3.5', u'L3', 37, ),
            (u'3.6', u'L3', 38, ),
            (u'3.7', u'L3', 39, ),
            (u'3.8', u'L3', 40, ),
            (u'4.1', u'L4', 41, ),
            (u'4.2', u'L4', 42, ),
            (u'4.3', u'L4', 43, ),
            (u'4.4', u'L4', 44, ),
            (u'4.5', u'L4', 45, ),
            (u'4.6', u'L4', 46, ),
            (u'4.7', u'L4', 47, ),
            (u'4.8', u'L4', 48, ),
            (u'5.1', u'L5', 49, ),
            (u'5.2', u'L5', 50, ),
            (u'5.3', u'L5', 51, ),
            (u'5.4', u'L5', 52, ),
            (u'5.5', u'L5', 53, ),
            (u'5.6', u'L5', 54, ),
            (u'5.7', u'L5', 55, ),
            (u'5.8', u'L5', 56, ),
            (u'6.1', u'L6', 57, ),
            (u'6.2', u'L6', 58, ),
            (u'6.3', u'L6', 59, ),
            (u'6.4', u'L6', 60, ),
            (u'6.5', u'L6', 61, ),
            (u'6.6', u'L6', 62, ),
            (u'6.7', u'L6', 63, ),
            (u'6.8', u'L6', 64, ),
            (u'7.1', u'L7', 65, ),
            (u'7.2', u'L7', 66, ),
            (u'7.3', u'L7', 67, ),
            (u'7.4', u'L7', 68, ),
            (u'7.5', u'L7', 69, ),
            (u'7.6', u'L7', 70, ),
            (u'7.7', u'L7', 71, ),
            (u'7.8', u'L7', 72, ),
            (u'8.1', u'L8', 73, ),
            (u'8.2', u'L8', 74, ),
            (u'8.3', u'L8', 75, ),
            (u'8.4', u'L8', 76, ),
            (u'8.5', u'L8', 77, ),
            (u'8.6', u'L8', 78, ),
            (u'8.7', u'L8', 79, ),
            (u'8.8', u'L8', 80, ),
            (u'8.9', u'L8', 81, ),
            (u'9.1', u'L9', 82, ),
            (u'9.2', u'L9', 83, ),
            (u'9.3', u'L9', 84, ),
            (u'9.4', u'L9', 85, ),
            (u'9.5', u'L9', 86, ),
            (u'9.6', u'L9', 87, ),
            (u'9.7', u'L9', 88, ),
            (u'9.8', u'L9', 89, ),
            (u'9.9', u'L9', 90, ),
            (u'L10', u'L10', 91, ),
            (u'11.1', u'L11', 92, ),
            (u'11.2', u'L11', 93, ),
            (u'11.3', u'L11', 94, ),
            (u'11.4', u'L11', 95, ),
            (u'11.5', u'L11', 96, ),
            (u'11.6', u'L11', 97, ),
            (u'11.7', u'L11', 98, ),
            (u'11.8', u'L11', 99, ),
            (u'11.9', u'L11', 100, ),
            (u'11.10', u'L11', 101, ),
            (u'11.11', u'L11', 102, ),
            (u'11.12', u'L11', 103, ),
            (u'12.1', u'L12', 104, ),
            (u'12.2', u'L12', 105, ),
            (u'12.3', u'L12', 106, ),
            (u'12.4', u'L12', 107, ),
            (u'12.5', u'L12', 108, ),
            (u'12.6', u'L12', 109, ),
            (u'12.7', u'L12', 110, ),
            (u'12.8', u'L12', 111, ),
            (u'12.9', u'L12', 112, ),
            (u'12.10', u'L12', 113, ),
            (u'12.11', u'L12', 114, ),
            (u'12.12', u'L12', 115, ),
            (u'13.1', u'L13', 116, ),
            (u'13.2', u'L13', 117, ),
            (u'13.3', u'L13', 118, ),
            (u'13.4', u'L13', 119, ),
            (u'13.5', u'L13', 120, ),
            (u'13.6', u'L13', 121, ),
            (u'13.7', u'L13', 122, ),
            (u'13.8', u'L13', 123, ),
            (u'13.9', u'L13', 124, ),
            (u'13.10', u'L13', 125, ),
            (u'13.11', u'L13', 126, ),
            (u'13.12', u'L13', 127, ),
            (u'14.1', u'L14', 128, ),
            (u'14.2', u'L14', 129, ),
            (u'14.3', u'L14', 130, ),
            (u'14.4', u'L14', 131, ),
            (u'14.5', u'L14', 132, ),
            (u'14.6', u'L14', 133, ),
            (u'14.7', u'L14', 134, ),
            (u'14.8', u'L14', 135, ),
            (u'14.9', u'L14', 136, ),
            (u'14.10', u'L14', 137, ),
            (u'14.11', u'L14', 138, ),
            (u'14.12', u'L14', 139, ),
            (u'Y-GRE总论', u'Y-GRE总论', 1, ),
            (u'1st', u'1st', 2, ),
            (u'2nd', u'2nd', 3, ),
            (u'3rd', u'3rd', 4, ),
            (u'AW总论', u'AW总论', 5, ),
            (u'4th', u'4th', 6, ),
            (u'5th', u'5th', 7, ),
            (u'6th', u'6th', 8, ),
            (u'7th', u'7th', 9, ),
            (u'8th', u'8th', 10, ),
            (u'9th', u'9th', 11, ),
            (u'Test', u'Test', -1, ),
        ]
        for entry in sections:
            section = Section.query.filter_by(name=entry[0]).first()
            if section is None:
                section = Section(
                    name=entry[0],
                    lesson_id=Lesson.query.filter_by(name=entry[1]).first().id,
                    order=entry[2]
                )
                db.session.add(section)
                print u'导入节信息', entry[0], entry[1]
        db.session.commit()

    def __repr__(self):
        return '<Section %r>' % self.alias


class Assignment(db.Model):
    __tablename__ = 'assignments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'))
    finished_by = db.relationship(
        'AssignmentScore',
        foreign_keys=[AssignmentScore.assignment_id],
        backref=db.backref('assignment', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @property
    def alias(self):
        return u'%s - %s' % (self.lesson.type.name, self.name)

    @property
    def finished_by_alias(self):
        return AssignmentScore.query\
            .join(User, User.id == AssignmentScore.user_id)\
            .filter(AssignmentScore.assignment_id == self.id)\
            .filter(User.created == True)\
            .filter(User.activated == True)\
            .filter(User.deleted == False)

    def to_json(self):
        assignment_json = {
            'name': self.name,
            'alias': self.alias,
            'lesson': self.lesson.name,
            'course_type': self.lesson.type.name,
            'element_id': '%s-lesson-%s-assignment-%s' % (self.lesson.type.alias, self.lesson.id, self.id),
        }
        return assignment_json

    @staticmethod
    def insert_assignments():
        assignments = [
            (u'L1', u'L1', ),
            (u'L2', u'L2', ),
            (u'R1-2', u'L2', ),
            (u'L3', u'L3', ),
            (u'L4', u'L4', ),
            (u'R3-4', u'L4', ),
            (u'L5', u'L5', ),
            (u'L6', u'L6', ),
            (u'R5-6', u'L6', ),
            (u'L7', u'L7', ),
            (u'L8', u'L8', ),
            (u'R7-8', u'L8', ),
            (u'R9-10', u'L10', ),
        ]
        for entry in assignments:
            assignment = Assignment.query.filter_by(name=entry[0]).first()
            if assignment is None:
                assignment = Assignment(
                    name=entry[0],
                    lesson_id=Lesson.query.filter_by(name=entry[1]).first().id
                )
                db.session.add(assignment)
                print u'导入作业信息', entry[0], entry[1]
        db.session.commit()

    def __repr__(self):
        return '<Assignment %r>' % self.alias


class Test(db.Model):
    __tablename__ = 'tests'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'))
    vb_finished_by = db.relationship(
        'VBTestScore',
        foreign_keys=[VBTestScore.test_id],
        backref=db.backref('test', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    y_gre_finished_by = db.relationship(
        'YGRETestScore',
        foreign_keys=[YGRETestScore.test_id],
        backref=db.backref('test', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @property
    def alias(self):
        return u'%s - %s' % (self.lesson.type.name, self.name)

    @property
    def finished_by_alias(self):
        if self.lesson.type.name == u'VB':
            return VBTestScore.query\
                .join(User, User.id == VBTestScore.user_id)\
                .filter(VBTestScore.test_id == self.id)\
                .filter(User.created == True)\
                .filter(User.activated == True)\
                .filter(User.deleted == False)
        if self.lesson.type.name == u'Y-GRE':
            return YGRETestScore.query\
                .join(User, User.id == YGRETestScore.user_id)\
                .filter(YGRETestScore.test_id == self.id)\
                .filter(User.created == True)\
                .filter(User.activated == True)\
                .filter(User.deleted == False)

    def to_json(self):
        test_json = {
            'name': self.name,
            'alias': self.alias,
            'lesson': self.lesson.name,
            'course_type': self.lesson.type.name,
            'element_id': '%s-lesson-%s-test-%s' % (self.lesson.type.alias, self.lesson.id, self.id),
        }
        return test_json

    @staticmethod
    def insert_tests():
        tests = [
            (u'L1-5', u'L5', ),
            (u'L6-9', u'L9', ),
            (u'入学测试', u'Y-GRE总论', ),
            (u'Unit 1', u'1st', ),
            (u'Unit 2', u'2nd', ),
            (u'Unit 3', u'3rd', ),
            (u'模考1', u'3rd', ),
            (u'PPII-1', u'3rd', ),
            (u'Unit 4', u'4th', ),
            (u'Unit 5', u'5th', ),
            (u'Unit 6', u'6th', ),
            (u'模考2', u'6th', ),
            (u'PPII-2', u'6th', ),
        ]
        for entry in tests:
            test = Test.query.filter_by(name=entry[0]).first()
            if test is None:
                test = Test(
                    name=entry[0],
                    lesson_id=Lesson.query.filter_by(name=entry[1]).first().id
                )
                db.session.add(test)
                print u'导入考试信息', entry[0], entry[1]
        db.session.commit()

    def __repr__(self):
        return '<Test %r>' % self.alias


class AnnouncementType(db.Model):
    __tablename__ = 'announcement_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    announcements = db.relationship('Announcement', backref='type', lazy='dynamic')

    @staticmethod
    def insert_announcement_types():
        announcement_types = [
            (u'登录通知', ),
            (u'用户主页通知', ),
            (u'管理主页通知', ),
            (u'预约VB通知', ),
            (u'预约Y-GRE通知', ),
            (u'用户邮件通知', ),
            (u'管理邮件通知', ),
        ]
        for entry in announcement_types:
            announcement_type = AnnouncementType.query.filter_by(name=entry[0]).first()
            if announcement_type is None:
                announcement_type = AnnouncementType(name=entry[0])
                db.session.add(announcement_type)
                print u'导入通知类型', entry[0]
        db.session.commit()

    def __repr__(self):
        return '<AnnouncementType %r>' % self.name


class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode(64))
    body = db.Column(db.UnicodeText)
    body_html = db.Column(db.UnicodeText)
    type_id = db.Column(db.Integer, db.ForeignKey('announcement_types.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    show = db.Column(db.Boolean, default=False)
    deleted = db.Column(db.Boolean, default=False)
    users_notified = db.relationship(
        'UserAnnouncement',
        foreign_keys=[UserAnnouncement.announcement_id],
        backref=db.backref('announcement', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def ping(self, modified_by):
        self.modified_at = datetime.utcnow()
        self.modified_by_id = modified_by.id
        db.session.add(self)

    def safe_delete(self, modified_by):
        self.clean_up()
        self.show = False
        self.deleted = True
        self.ping(modified_by=modified_by)
        db.session.add(self)

    def publish(self, modified_by):
        self.clean_up()
        if self.type.name == u'登录通知':
            announcements = Announcement.query\
                .join(AnnouncementType, AnnouncementType.id == Announcement.type_id)\
                .filter(AnnouncementType.name == u'登录通知')\
                .all()
            for announcement in announcements:
                announcement.retract(modified_by=modified_by)
        if self.type.name == u'用户邮件通知':
            send_emails(User.users_can(u'预约').all(), self.title, 'manage/mail/announcement', user=user, announcement=self)
        if self.type.name == u'管理邮件通知':
            send_emails(User.users_can(u'管理').all(), self.title, 'manage/mail/announcement', user=user, announcement=self)
        self.show = True
        self.ping(modified_by=modified_by)
        db.session.add(self)

    def retract(self, modified_by):
        self.clean_up()
        self.show = False
        self.ping(modified_by=modified_by)
        db.session.add(self)

    def notify(self, user):
        log = UserAnnouncement(user_id=user.id, announcement_id=self.id)
        db.session.add(log)

    def clean_up(self):
        logs = UserAnnouncement.query\
            .filter_by(announcement_id=self.id)\
            .all()
        for log in logs:
            db.session.delete(log)

    @staticmethod
    def on_changed_body_html(target, value, oldvalue, initiator):
        newline_tags = ['p', 'li']
        soup = BeautifulSoup(value, 'html.parser')
        target.body = u'\n\n'.join([child.get_text() for child in [child for child in soup.descendants if (reduce(lambda tag1, tag2: len(BeautifulSoup(unicode(child), 'html.parser').find_all(tag1)) == 1 or len(BeautifulSoup(unicode(child), 'html.parser').find_all(tag2)) == 1, newline_tags))] if child.get_text()])

    def __repr__(self):
        return '<Announcement %r>' % self.title


db.event.listen(Announcement.body_html, 'set', Announcement.on_changed_body_html)