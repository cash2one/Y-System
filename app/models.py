# -*- coding: utf-8 -*-

from os import urandom
from datetime import datetime, date, time, timedelta
from sqlalchemy import or_
from base64 import urlsafe_b64encode
import hashlib
import json
from bs4 import BeautifulSoup
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from app.exceptions import ValidationError
from . import db, login_manager
from .email import send_email


class RolePermission(db.Model):
    __tablename__ = 'role_permissions'
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), primary_key=True)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), primary_key=True)


class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
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
            (u'预约', ),
            (u'预约VB课程', ),
            (u'预约Y-GRE课程', ),
            (u'预约VB课程x2', ),
            (u'预约任意课程', ),
            (u'管理', ),
            (u'管理课程预约', ),
            (u'管理学习进度', ),
            (u'管理iPad借阅', ),
            (u'管理预约时段', ),
            (u'管理iPad设备', ),
            (u'管理作业', ),
            (u'管理考试', ),
            (u'管理通知', ),
            (u'管理站内信', ),
            (u'管理反馈', ),
            (u'管理进站', ),
            (u'管理用户', ),
            (u'管理权限', ),
            (u'开发权限', ),
        ]
        for P in permissions:
            permission = Permission.query.filter_by(name=P[0]).first()
            if permission is None:
                permission = Permission(name=P[0])
                db.session.add(permission)
                print u'导入用户权限信息', P[0]
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

    @staticmethod
    def insert_roles():
        roles = [
            (u'挂起', [], ),
            (u'单VB', [u'预约', u'预约VB课程'], ),
            (u'Y-GRE 普通', [u'预约', u'预约VB课程', u'预约Y-GRE课程'], ),
            (u'Y-GRE VBx2', [u'预约', u'预约VB课程', u'预约Y-GRE课程', u'预约VB课程x2'], ),
            (u'Y-GRE A权限', [u'预约', u'预约VB课程', u'预约Y-GRE课程', u'预约任意课程'], ),
            (u'志愿者', [u'管理', u'管理课程预约', u'管理学习进度', u'管理iPad借阅'], ),
            (u'协管员', [u'管理', u'管理课程预约', u'管理学习进度', u'管理iPad借阅', u'管理预约时段', u'管理iPad设备', u'管理作业', u'管理考试', u'管理通知', u'管理站内信', u'管理反馈', u'管理进站', u'管理用户'], ),
            (u'管理员', [u'管理', u'管理课程预约', u'管理学习进度', u'管理iPad借阅', u'管理预约时段', u'管理iPad设备', u'管理作业', u'管理考试', u'管理通知', u'管理站内信', u'管理反馈', u'管理进站', u'管理用户', u'管理权限'], ),
            (u'开发人员', [u'管理', u'管理课程预约', u'管理学习进度', u'管理iPad借阅', u'管理预约时段', u'管理iPad设备', u'管理作业', u'管理考试', u'管理通知', u'管理站内信', u'管理反馈', u'管理进站', u'管理用户', u'管理权限', u'开发权限'], ),
        ]
        for R in roles:
            role = Role.query.filter_by(name=R[0]).first()
            if role is None:
                role = Role(name=R[0])
                db.session.add(role)
                db.session.commit()
                for P in R[1]:
                    permission = Permission.query.filter_by(name=P).first()
                    role.add_permission(permission=permission)
                print u'导入用户角色信息', R[0]
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
        for G in genders:
            gender = Gender.query.filter_by(name=G[0]).first()
            if gender is None:
                gender = Gender(name=G[0])
                db.session.add(gender)
                print u'导入性别类型信息', G[0]
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
            (u'同学', ),
            (u'同事', ),
            (u'朋友', ),
        ]
        for R in relationships:
            relationship = Relationship.query.filter_by(name=R[0]).first()
            if relationship is None:
                relationship = Relationship(name=R[0])
                db.session.add(relationship)
                print u'导入关系类型信息', R[0]
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
        for PT in purpose_types:
            purpose_type = PurposeType.query.filter_by(name=PT[0]).first()
            if purpose_type is None:
                purpose_type = PurposeType(name=PT[0])
                db.session.add(purpose_type)
                print u'导入研修目的类型信息', PT[0]
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
        for RT in referrer_types:
            referrer_type = ReferrerType.query.filter_by(name=RT[0]).first()
            if referrer_type is None:
                referrer_type = ReferrerType(name=RT[0])
                db.session.add(referrer_type)
                print u'导入来源类型信息', RT[0]
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


class SuspensionRecord(db.Model):
    __tablename__ = 'suspension_records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    deleted = db.Column(db.Boolean, default=False)

    def ping(self, modified_by):
        self.modified_at = datetime.utcnow()
        self.modified_by_id = modified_by.id
        db.session.add(self)

    def safe_delete(self, modified_by):
        self.deleted = True
        self.ping(modified_by=modified_by)
        db.session.add(self)

    def __repr__(self):
        return '<Suspension Record %r, %r, %r>' % (self.user.name, self.start_date, self.end_date)


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
        for BS in booking_states:
            booking_state = BookingState.query.filter_by(name=BS[0]).first()
            if booking_state is None:
                booking_state = BookingState(name=BS[0])
                db.session.add(booking_state)
                print u'导入预约状态信息', BS[0]
        db.session.commit()

    def __repr__(self):
        return '<Booking State %r>' % self.name


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
            .filter(Schedule.date == date.today())\
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
            .filter(Schedule.date == date.today())\
            .filter(CourseType.name == u'Y-GRE')\
            .all():
            if schedule.started:
                return sum([booking.user.last_punch.section.lesson.name in lessons for booking in Booking.query.filter_by(schedule_id=schedule.id).all() if booking.state.name in [u'预约', u'排队', u'赴约', u'迟到']])
        return 0

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
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def alias(self):
        return u'%s - %s' % (self.section.lesson.name, self.section.name)

    @property
    def alias2(self):
        return u'%s - %s - %s' % (self.section.lesson.type.name, self.section.lesson.name, self.section.name)

    @property
    def alias3(self):
        return u'%s - %s' % (self.section.lesson.type.name, self.section.lesson.name)

    def to_json(self):
        punch_json = {
            'user': self.user.name,
            'course_type': self.section.lesson.type.name,
            'lesson': self.section.lesson.name,
            'section': self.section.name,
            'alias': self.alias,
            'alias2': self.alias2,
            'alias3': self.alias3,
            'punched_at': self.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
        return punch_json

    def __repr__(self):
        return '<Punch %r, %r>' % (self.user.name, self.alias)


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
        for ASG in assignment_score_grades:
            assignment_score_grade = AssignmentScoreGrade.query.filter_by(name=ASG[0]).first()
            if assignment_score_grade is None:
                assignment_score_grade = AssignmentScoreGrade(name=ASG[0])
                db.session.add(assignment_score_grade)
                print u'导入作业成绩类型信息', ASG[0]
        db.session.commit()

    def __repr__(self):
        return '<Assignment Score Grade %r>' % self.name


class AssignmentScore(db.Model):
    __tablename__ = 'assignment_scores'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'))
    grade_id = db.Column(db.Integer, db.ForeignKey('assignment_score_grades.id'))
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Assignment Score %r, %r>' % (self.user.name, self.assignment.name)


class VBTestScore(db.Model):
    __tablename__ = 'vb_test_scores'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'))
    score = db.Column(db.Float)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<VB Test Score %r, %r>' % (self.user.name, self.test.name)


class GREVScore(db.Model):
    __tablename__ = 'gre_v_scores'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    value = db.Column(db.Integer)
    y_gre_test_scores = db.relationship('YGRETestScore', backref='v_score', lazy='dynamic')

    @staticmethod
    def insert_gre_v_scores():
        gre_v_scores = [(unicode(x), x, ) for x in range(130, 171)]
        for GVS in gre_v_scores:
            gre_v_score = GREVScore.query.filter_by(name=GVS[0]).first()
            if gre_v_score is None:
                gre_v_score = GREVScore(name=GVS[0], value=GVS[1])
                db.session.add(gre_v_score)
                print u'导入GRE Verbal成绩类型信息', GVS[0]
        db.session.commit()

    def __repr__(self):
        return '<GRE Verbal Reasoning Score %r>' % self.name


class GREQScore(db.Model):
    __tablename__ = 'gre_q_scores'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    value = db.Column(db.Integer)
    y_gre_test_scores = db.relationship('YGRETestScore', backref='q_score', lazy='dynamic')

    @staticmethod
    def insert_gre_q_scores():
        gre_q_scores = [(unicode(x), x, ) for x in range(130, 171)]
        for GQS in gre_q_scores:
            gre_q_score = GREQScore.query.filter_by(name=GQS[0]).first()
            if gre_q_score is None:
                gre_q_score = GREQScore(name=GQS[0], value=GQS[1])
                db.session.add(gre_q_score)
                print u'导入GRE Quantitative成绩类型信息', GQS[0]
        db.session.commit()

    def __repr__(self):
        return '<GRE Quantitative Reasoning Score %r>' % self.name


class GREAWScore(db.Model):
    __tablename__ = 'gre_aw_scores'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    value = db.Column(db.Float)
    y_gre_test_scores = db.relationship('YGRETestScore', backref='aw_score', lazy='dynamic')

    @staticmethod
    def insert_gre_aw_scores():
        gre_aw_scores = [(unicode(x/2.0), x/2.0, ) for x in range(0, 13)]
        for GAWS in gre_aw_scores:
            gre_aw_score = GREAWScore.query.filter_by(name=GAWS[0]).first()
            if gre_aw_score is None:
                gre_aw_score = GREAWScore(name=GAWS[0], value=GAWS[1])
                db.session.add(gre_aw_score)
                print u'导入GRE AW成绩类型信息', GAWS[0]
        db.session.commit()

    def __repr__(self):
        return '<GRE Analytical Writing Score %r>' % self.name


class YGRETestScore(db.Model):
    __tablename__ = 'y_gre_test_scores'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'))
    v_score_id = db.Column(db.Integer, db.ForeignKey('gre_v_scores.id'))
    q_score_id = db.Column(db.Integer, db.ForeignKey('gre_q_scores.id'))
    aw_score_id = db.Column(db.Integer, db.ForeignKey('gre_aw_scores.id'))
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Y-GRE Test Score %r, %r>' % (self.user.name, self.test.name)


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
        for IT in invitation_types:
            invitation_type = InvitationType.query.filter_by(name=IT[0]).first()
            if invitation_type is None:
                invitation_type = InvitationType(name=IT[0])
                db.session.add(invitation_type)
                print u'导入邀请类型信息', IT[0]
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


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    # basic properties
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Unicode(64), unique=True, index=True)
    confirmed = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    activated = db.Column(db.Boolean, default=False)
    activated_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen_at = db.Column(db.DateTime, default=datetime.utcnow)
    deleted = db.Column(db.Boolean, default=False)
    # profile properties
    name = db.Column(db.Unicode(64), index=True)
    gender_id = db.Column(db.Integer, db.ForeignKey('genders.id'))
    id_number = db.Column(db.Unicode(64), index=True)
    birthdate = db.Column(db.Date)
    mobile = db.Column(db.Unicode(64))
    wechat = db.Column(db.Unicode(64))
    qq = db.Column(db.Unicode(64))
    address = db.Column(db.Unicode(128))
    emergency_contact_name = db.Column(db.Unicode(64))
    emergency_contact_mobile = db.Column(db.Unicode(64))
    emergency_contact_relationship_id = db.Column(db.Integer, db.ForeignKey('relationships.id'))
    previous_achievements = db.relationship('PreviousAchievement', backref='user', lazy='dynamic')
    education_records = db.relationship('EducationRecord', backref='user', lazy='dynamic')
    employment_records = db.relationship('EmploymentRecord', backref='user', lazy='dynamic')
    worked_in_same_field = db.Column(db.Boolean, default=False)
    deformity = db.Column(db.Boolean, default=False)
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
    registered_courses = db.relationship(
        'CourseRegistration',
        foreign_keys=[CourseRegistration.user_id],
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
    punches = db.relationship(
        'Punch',
        foreign_keys=[Punch.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    finished_assignments = db.relationship(
        'AssignmentScore',
        foreign_keys=[AssignmentScore.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    finished_vb_tests = db.relationship(
        'VBTestScore',
        foreign_keys=[VBTestScore.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    finished_y_gre_tests = db.relationship(
        'YGRETestScore',
        foreign_keys=[YGRETestScore.user_id],
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
    managed_ipads_rent = db.relationship(
        'Rental',
        foreign_keys=[Rental.rent_agent_id],
        backref=db.backref('rent_agent', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    managed_ipads_return = db.relationship(
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
    modified_announcements = db.relationship('Announcement', backref='modified_by', lazy='dynamic')
    # user relationship properties
    invited_users = db.relationship(
        'Invitation',
        foreign_keys=[Invitation.inviter_id],
        backref=db.backref('inviter', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    invited_by = db.relationship(
        'Invitation',
        foreign_keys=[Invitation.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    received_users = db.relationship(
        'Reception',
        foreign_keys=[Reception.receptionist_id],
        backref=db.backref('receptionist', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    received_by = db.relationship(
        'Reception',
        foreign_keys=[Reception.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    created_users = db.relationship(
        'UserCreation',
        foreign_keys=[UserCreation.creator_id],
        backref=db.backref('creator', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    created_by = db.relationship(
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

    def safe_delete(self):
        self.role_id = Role.query.filter_by(name=u'挂起').first().id
        self.deleted = True
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
        return self.role is not None and self.role.has_permission(permission=Permission.query.filter_by(name=permission_name).first())

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
            if user.is_developer:
                return False
        if self.is_administrator:
            if user.is_developer or user.is_administrator:
                return False
        if self.is_moderator:
            if user.is_developer or user.is_administrator or user.is_moderator:
                return False
        if self.is_volunteer:
            if user.is_developer or user.is_administrator or user.is_moderator or user.is_volunteer:
                return False
        return True

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

    def add_purpose(self, purpose_type, remark=u''):
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

    def add_referrer(self, referrer_type, remark=u''):
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

    def invite_user(self, user, invitation_type):
        if not self.invited_user(user):
            invitation = Invitation(inviter_id=self.id, user_id=user.id, type_id=invitation_type.id)
        else:
            invitation = self.invited_users.filter_by(user_id=user.id).first()
            invitation.type_id = invitation_type.id
            invitation.timestamp = datetime.utcnow()
        db.session.add(invitation)

    def uninvite_user(self, user):
        invitation = self.invited_users.filter_by(user_id=user.id).first()
        if invitation:
            db.session.delete(invitation)

    def invited_user(self, user):
        return self.invited_users.filter_by(user_id=user.id).first() is not None

    def receive_user(self, user):
        if not self.received_user(user):
            reception = Reception(receptionist_id=self.id, user_id=user.id)
        else:
            reception = self.received_users.filter_by(user_id=user.id).first()
            reception.timestamp = datetime.utcnow()
        db.session.add(reception)

    def unreceive_user(self, user):
        reception = self.received_users.filter_by(user_id=user.id).first()
        if reception:
            db.session.delete(reception)

    def received_user(self, user):
        return self.received_users.filter_by(user_id=user.id).first() is not None

    def create_user(self, user):
        if not self.created_user(user):
            user_creation = UserCreation(creator_id=self.id, user_id=user.id)
        else:
            user_creation = self.created_users.filter_by(user_id=user.id).first()
            user_creation.timestamp = datetime.utcnow()
        db.session.add(user_creation)

    def uncreate_user(self, user):
        user_creation = self.created_users.filter_by(user_id=user.id).first()
        if user_creation:
            db.session.delete(user_creation)

    def created_user(self, user):
        return self.created_users.filter_by(user_id=user.id).first() is not None

    def register_group(self, organizer):
        if not self.is_registering_group(organizer):
            group_registration = GroupRegistration(organizer_id=organizer.id, member_id=self.id)
        else:
            group_registration = self.registered_groups.filter_by(organizer_id=organizer.id).first()
            group_registration.timestamp = datetime.utcnow()
        db.session.add(group_registration)

    def unregister_group(self, organizer):
        group_registration = self.registered_groups.filter_by(organizer_id=organizer.id).first()
        if group_registration:
            db.session.delete(group_registration)

    def is_registering_group(self, organizer):
        return self.registered_groups.filter_by(organizer_id=organizer.id).first() is not None

    def register_course(self, course):
        if not self.is_registering_course(course):
            course_registration = CourseRegistration(user_id=self.id, course_id=course.id)
        else:
            course_registration = self.registered_courses.filter_by(course_id=course.id).first()
            course_registration.timestamp = datetime.utcnow()
        db.session.add(course_registration)

    def unregister_course(self, course):
        course_registration = self.registered_courses.filter_by(course_id=course.id).first()
        if course_registration:
            db.session.delete(course_registration)

    def is_registering_course(self, course):
        return self.registered_courses.filter_by(course_id=course.id).first() is not None

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
        booking = self.booked_schedules.filter_by(schedule_id=schedule.id).first()
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
        booking = self.booked_schedules.filter_by(schedule_id=schedule.id).first()
        if booking:
            booking.state_id = BookingState.query.filter_by(name=u'爽约').first().id
            db.session.add(booking)

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
        if not self.punched(section):
            punch = Punch(user_id=self.id, section_id=section.id)
        else:
            punch = self.punches.filter_by(section_id=section.id).first()
            punch.timestamp = datetime.utcnow()
        db.session.add(punch)

    def unpunch(self, section):
        punch = self.punches.filter_by(section_id=section.id).first()
        if punch:
            db.session.delete(punch)

    def punched(self, section):
        return self.punches.filter_by(section_id=section.id).first() is not None

    @property
    def last_punch(self):
        return self.punches.order_by(Punch.timestamp.desc()).first()

    def notified_by(self, announcement):
        return self.read_announcements.filter_by(announcement_id=announcement.id).first() is not None

    def activate(self):
        self.activated = True
        self.activated_at = datetime.utcnow()
        db.session.add(self)
        self.punch(section=Section.query.get(1))

    def to_json(self):
        user_json = {
            'name': self.name,
            'email': self.email,
            'role': self.role.name,
            'last_punch': self.last_punch.to_json(),
            'last_seen_at': self.last_seen_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'url': url_for('main.profile_user', user_id=self.id),
        }
        return user_json

    def to_json_suggestion(self, suggest_email=False, include_url=False):
        if suggest_email:
            user_json_suggestion = {
                'title': self.email,
                'description': '%s [%s]' % (self.name, self.role.name),
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
                role_id=Role.query.filter_by(name=u'开发人员').first().id,
                password=current_app.config['YSYS_ADMIN_PASSWORD'],
                name=u'Admin'
            )
            db.session.add(admin)
            db.session.commit()
            admin.create_user(user=admin)
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


class PreviousAchievementType(db.Model):
    __tablename__ = 'previous_achievement_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    previous_achievements = db.relationship('PreviousAchievement', backref='type', lazy='dynamic')

    @staticmethod
    def insert_previous_achievement_types():
        previous_achievement_types = [
            (u'高考总分', ),
            (u'高考数学', ),
            (u'高考英语', ),
            (u'大学英语四级', ),
            (u'大学英语六级', ),
            (u'专业英语四级', ),
            (u'专业英语八级', ),
            (u'TOEFL', ),
            (u'其它', ),
        ]
        for PAT in previous_achievement_types:
            previous_achievement_type = PreviousAchievementType.query.filter_by(name=PAT[0]).first()
            if previous_achievement_type is None:
                previous_achievement_type = PreviousAchievementType(name=PAT[0])
                db.session.add(previous_achievement_type)
                print u'导入既往成绩类型信息', PAT[0]
        db.session.commit()

    def __repr__(self):
        return '<Previous Achievement Type %r>' % self.name


class PreviousAchievement(db.Model):
    __tablename__ = 'previous_achievements'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('previous_achievement_types.id'))
    score = db.Column(db.Integer)
    remark = db.Column(db.UnicodeText)

    def __repr__(self):
        return '<Previous Achievement %r, %r, %r, %r>' % (self.user.name, self.type.name, self.score)


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
        for ET in education_types:
            education_type = EducationType.query.filter_by(name=ET[0]).first()
            if education_type is None:
                education_type = EducationType(name=ET[0])
                db.session.add(education_type)
                print u'导入学历类型信息', ET[0]
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

    def __repr__(self):
        return '<Education Record %r, %r, %r, %r>' % (self.user.name, self.type.name, self.school, self.year)


class EmploymentRecord(db.Model):
    __tablename__ = 'employment_records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    employer = db.Column(db.Unicode(64))
    position = db.Column(db.Unicode(64))
    year = db.Column(db.Unicode(16))

    def __repr__(self):
        return '<Education Record %r, %r, %r>' % (self.user.name, self.employer, self.position)


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    price = db.Column(db.Float, default=0.0)
    available = db.Column(db.Boolean, default=False)
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

    @staticmethod
    def insert_products():
        products = [
            (u'VB基本技术费', 6800.0, ),
            (u'Y-GRE基本技术费', 6800.0, ),
            (u'AW费用', 800.0, ),
            (u'Q费用', 800.0, ),
            (u'多轮费用', 800.0, ),
            (u'未毕业减免', -800.0, ),
            (u'本校减免', -500.0, ),
            (u'联报优惠', -1000.0, ),
            (u'团报优惠', -200.0, ),
            (u'按月延长有效期', 1000.0, ),
            (u'一次性延长2年有效期', 3000.0, ),
        ]
        for P in products:
            product = Product.query.filter_by(name=P[0]).first()
            if product is None:
                product = Product(
                    name=P[0],
                    price=P[1],
                    modified_by_id=User.query.get(1).id
                )
                db.session.add(product)
                print u'导入课程类型信息', P[0]
        db.session.commit()

    def __repr__(self):
        return '<Product %r>' % self.name


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
        return '<Course Type %r>' % self.name


class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    type_id = db.Column(db.Integer, db.ForeignKey('course_types.id'))
    show = db.Column(db.Boolean, default=False)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    deleted = db.Column(db.Boolean, default=False)
    registered_users = db.relationship(
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

    def flip_show(self, modified_by):
        self.show = not self.show
        self.ping(modified_by=modified_by)
        db.session.add(self)

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
                    type_id=CourseType.query.filter_by(name=C[1]).first().id,
                    modified_by_id=User.query.get(1).id
                )
                db.session.add(course)
                print u'导入课程信息', C[0], C[1]
        db.session.commit()

    def __repr__(self):
        return '<Course %r>' % self.name


class Period(db.Model):
    __tablename__ = 'periods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    type_id = db.Column(db.Integer, db.ForeignKey('course_types.id'))
    show = db.Column(db.Boolean, default=False)
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

    def flip_show(self, modified_by):
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
            'type': self.type.show,
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
        for P in periods:
            period = Period.query.filter_by(name=P[0]).first()
            if period is None:
                period = Period(
                    name=P[0],
                    start_time=P[1],
                    end_time=P[2],
                    type_id=CourseType.query.filter_by(name=P[3]).first().id,
                    modified_by_id=User.query.get(1).id
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
            .filter(Schedule.date == date.today())\
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
        for PC in ipad_capacities:
            ipad_capacity = iPadCapacity.query.filter_by(name=PC[0]).first()
            if ipad_capacity is None:
                ipad_capacity = iPadCapacity(name=PC[0])
                db.session.add(ipad_capacity)
                print u'导入iPad容量信息', PC[0]
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
        for PS in ipad_states:
            ipad_state = iPadState.query.filter_by(name=PS[0]).first()
            if ipad_state is None:
                ipad_state = iPadState(name=PS[0])
                db.session.add(ipad_state)
                print u'导入iPad状态信息', PS[0]
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
        for R in rooms:
            room = Room.query.filter_by(name=R[0]).first()
            if room is None:
                room = Room(name=R[0])
                db.session.add(room)
                print u'导入房间信息', R[0]
        db.session.commit()

    def __repr__(self):
        return '<Room %r>' % self.name


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
        json_string = unicode(json.dumps([{'alias': ipad.alias, 'lessons': [{'name': lesson.name, 'exist': (iPadContent.query.filter_by(ipad_id=ipad.id, lesson_id=lesson.id).first() is not None)} for lesson in Lesson.query.order_by(Lesson.id.asc()).all()]} for ipad in iPad.query.filter_by(deleted=False).order_by(iPad.alias.asc()).all()]))
        ipad_content_json = iPadContentJSON.query.get(1)
        if ipad_content_json is not None:
            ipad_content_json.json_string = json_string
            ipad_content_json.out_of_date = False
        else:
            ipad_content_json = iPadContentJSON(json_string=json_string, out_of_date=False)
        db.session.add(ipad_content_json)

    @staticmethod
    def mark_out_of_date():
        ipad_content_json = iPadContentJSON.query.get(1)
        if ipad_content_json is not None:
            ipad_content_json.out_of_date = True
        else:
            ipad_content_json = iPadContentJSON(out_of_date=True)
        db.session.add(ipad_content_json)

    def __repr__(self):
        return '<iPadContentJSON %r>' % self.json_string


class iPad(db.Model):
    __tablename__ = 'ipads'
    id = db.Column(db.Integer, primary_key=True)
    serial = db.Column(db.Unicode(12), unique=True, index=True)
    alias = db.Column(db.Unicode(64), index=True)
    capacity_id = db.Column(db.Integer, db.ForeignKey('ipad_capacities.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    state_id = db.Column(db.Integer, db.ForeignKey('ipad_states.id'))
    video_playback = db.Column(db.Interval, default=timedelta(hours=10))
    battery_life = db.Column(db.Integer, default=100)
    charged_at = db.Column(db.DateTime, default=datetime.utcnow)
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
    def y_gre_lesson_ids_included(self):
        y_gre_lessons = self.has_y_gre_lessons
        return [y_gre_lesson.id for y_gre_lesson in y_gre_lessons]

    @property
    def video_playback_alias(self):
        return u'%g小时' % (self.video_playback.total_seconds() / 3600)

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
        return User.query\
            .join(Rental, Rental.user_id == User.id)\
            .filter(Rental.returned == False)\
            .filter(Rental.ipad_id == self.id)\
            .first()

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
            'serial': self.serial,
            'alias': self.alias,
            'capacity': self.capacity.name,
            'state': self.state.name,
            'modified_at': self.modified_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'modified_by': self.modified_by.name,
        }
        if self.state.name == u'借出':
            ipad_json['now_rented_by'] = self.now_rented_by.to_json()
            ipad_json['battery_life'] = {
                'percent': self.current_battery_life,
                'level': self.current_battery_life_level,
            }
            ipad_json['overtime'] = self.current_rental.is_overtime
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
                    modified_by_id=User.query.get(1).id
                )
                print u'导入iPad信息', P[1], P[0], P[2], P[3], P[4]
                db.session.add(ipad)
        db.session.commit()

    def __repr__(self):
        return '<iPad %r, %r>' % (self.alias, self.serial)


class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    type_id = db.Column(db.Integer, db.ForeignKey('course_types.id'))
    advanced = db.Column(db.Boolean, default=False)
    sections = db.relationship('Section', backref='lesson', lazy='dynamic')
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
    def first_section(self):
        return self.sections\
            .order_by(Section.id.asc())\
            .first()

    @property
    def available_ipads(self):
        return iPad.query\
            .join(iPadState, iPadState.id == iPad.state_id)\
            .join(iPadContent, iPadContent.ipad_id == iPad.id)\
            .filter(iPadState.name != u'退役')\
            .filter(iPadContent.lesson_id == self.id)

    @staticmethod
    def insert_lessons():
        lessons = [
            (u'VB总论', u'VB', False, ),
            (u'L1', u'VB', False, ),
            (u'L2', u'VB', False, ),
            (u'L3', u'VB', False, ),
            (u'L4', u'VB', False, ),
            (u'L5', u'VB', False, ),
            (u'L6', u'VB', False, ),
            (u'L7', u'VB', False, ),
            (u'L8', u'VB', False, ),
            (u'L9', u'VB', False, ),
            (u'L10', u'VB', False, ),
            (u'L11', u'VB', True, ),
            (u'L12', u'VB', True, ),
            (u'L13', u'VB', True, ),
            (u'L14', u'VB', True, ),
            (u'Y-GRE总论', u'Y-GRE', False, ),
            (u'1st', u'Y-GRE', False, ),
            (u'2nd', u'Y-GRE', False, ),
            (u'3rd', u'Y-GRE', False, ),
            (u'4th', u'Y-GRE', False, ),
            (u'5th', u'Y-GRE', False, ),
            (u'6th', u'Y-GRE', False, ),
            (u'7th', u'Y-GRE', False, ),
            (u'8th', u'Y-GRE', False, ),
            (u'9th', u'Y-GRE', False, ),
            (u'Test', u'Y-GRE', False, ),
            (u'AW总论', u'Y-GRE', False, ),
        ]
        for L in lessons:
            lesson = Lesson.query.filter_by(name=L[0]).first()
            if lesson is None:
                lesson = Lesson(
                    name=L[0],
                    type_id=CourseType.query.filter_by(name=L[1]).first().id,
                    advanced=L[2]
                )
                db.session.add(lesson)
                print u'导入课程信息', L[0], L[1]
        db.session.commit()

    def __repr__(self):
        return '<Lesson %r>' % self.name


class Section(db.Model):
    __tablename__ = 'sections'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True)
    hour = db.Column(db.Interval, default=timedelta(hours=0))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'))
    punches = db.relationship(
        'Punch',
        foreign_keys=[Punch.section_id],
        backref=db.backref('section', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @property
    def alias(self):
        return u'%s - %s' % (self.lesson.name, self.name)

    @property
    def alias2(self):
        return u'%s - %s - %s' % (self.lesson.type.name, self.lesson.name, self.name)

    @property
    def alias3(self):
        return u'%s - %s' % (self.lesson.type.name, self.lesson.name)

    @staticmethod
    def insert_sections():
        sections = [
            (u'Day 1-1', u'VB总论', 1, ),
            (u'Day 1-2', u'VB总论', 1, ),
            (u'Day 1-3', u'VB总论', 1, ),
            (u'Day 1-4', u'VB总论', 1, ),
            (u'Day 2-1', u'VB总论', 1, ),
            (u'Day 2-2', u'VB总论', 1, ),
            (u'Day 2-3', u'VB总论', 1, ),
            (u'Day 2-4', u'VB总论', 1, ),
            (u'Day 3-1', u'VB总论', 1, ),
            (u'Day 3-2', u'VB总论', 1, ),
            (u'Day 3-3', u'VB总论', 1, ),
            (u'Day 3-4', u'VB总论', 1, ),
            (u'Day 4-1', u'VB总论', 1, ),
            (u'Day 4-2', u'VB总论', 1, ),
            (u'Day 4-3', u'VB总论', 1, ),
            (u'Day 4-4', u'VB总论', 1, ),
            (u'1.1', u'L1', 1, ),
            (u'1.2', u'L1', 1, ),
            (u'1.3', u'L1', 1, ),
            (u'1.4', u'L1', 1, ),
            (u'1.5', u'L1', 1, ),
            (u'1.6', u'L1', 1, ),
            (u'1.7', u'L1', 1, ),
            (u'1.8', u'L1', 1, ),
            (u'2.1', u'L2', 1, ),
            (u'2.2', u'L2', 1, ),
            (u'2.3', u'L2', 1, ),
            (u'2.4', u'L2', 1, ),
            (u'2.5', u'L2', 1, ),
            (u'2.6', u'L2', 1, ),
            (u'2.7', u'L2', 1, ),
            (u'2.8', u'L2', 1, ),
            (u'3.1', u'L3', 1, ),
            (u'3.2', u'L3', 1, ),
            (u'3.3', u'L3', 1, ),
            (u'3.4', u'L3', 1, ),
            (u'3.5', u'L3', 1, ),
            (u'3.6', u'L3', 1, ),
            (u'3.7', u'L3', 1, ),
            (u'3.8', u'L3', 1, ),
            (u'4.1', u'L4', 1, ),
            (u'4.2', u'L4', 1, ),
            (u'4.3', u'L4', 1, ),
            (u'4.4', u'L4', 1, ),
            (u'4.5', u'L4', 1, ),
            (u'4.6', u'L4', 1, ),
            (u'4.7', u'L4', 1, ),
            (u'4.8', u'L4', 1, ),
            (u'5.1', u'L5', 1, ),
            (u'5.2', u'L5', 1, ),
            (u'5.3', u'L5', 1, ),
            (u'5.4', u'L5', 1, ),
            (u'5.5', u'L5', 1, ),
            (u'5.6', u'L5', 1, ),
            (u'5.7', u'L5', 1, ),
            (u'5.8', u'L5', 1, ),
            (u'6.1', u'L6', 1, ),
            (u'6.2', u'L6', 1, ),
            (u'6.3', u'L6', 1, ),
            (u'6.4', u'L6', 1, ),
            (u'6.5', u'L6', 1, ),
            (u'6.6', u'L6', 1, ),
            (u'6.7', u'L6', 1, ),
            (u'6.8', u'L6', 1, ),
            (u'7.1', u'L7', 1, ),
            (u'7.2', u'L7', 1, ),
            (u'7.3', u'L7', 1, ),
            (u'7.4', u'L7', 1, ),
            (u'7.5', u'L7', 1, ),
            (u'7.6', u'L7', 1, ),
            (u'7.7', u'L7', 1, ),
            (u'7.8', u'L7', 1, ),
            (u'8.1', u'L8', 1, ),
            (u'8.2', u'L8', 1, ),
            (u'8.3', u'L8', 1, ),
            (u'8.4', u'L8', 1, ),
            (u'8.5', u'L8', 1, ),
            (u'8.6', u'L8', 1, ),
            (u'8.7', u'L8', 1, ),
            (u'8.8', u'L8', 1, ),
            (u'8.9', u'L8', 1, ),
            (u'9.1', u'L9', 1, ),
            (u'9.2', u'L9', 1, ),
            (u'9.3', u'L9', 1, ),
            (u'9.4', u'L9', 1, ),
            (u'9.5', u'L9', 1, ),
            (u'9.6', u'L9', 1, ),
            (u'9.7', u'L9', 1, ),
            (u'9.8', u'L9', 1, ),
            (u'9.9', u'L9', 1, ),
            (u'L10', u'L10', 1, ),
            (u'L11', u'L11', 1, ),
            (u'L12', u'L12', 1, ),
            (u'L13', u'L13', 1, ),
            (u'L14', u'L14', 1, ),
            (u'Y-GRE总论', u'Y-GRE总论', 10, ),
            (u'1st', u'1st', 30, ),
            (u'2nd', u'2nd', 30, ),
            (u'3rd', u'3rd', 50, ),
            (u'4th', u'4th', 30, ),
            (u'5th', u'5th', 40, ),
            (u'6th', u'6th', 30, ),
            (u'7th', u'7th', 30, ),
            (u'8th', u'8th', 30, ),
            (u'9th', u'9th', 30, ),
            (u'Test', u'Test', 0, ),
            (u'AW总论', u'AW总论', 2.5, ),
        ]
        for S in sections:
            section = Section.query.filter_by(name=S[0]).first()
            if section is None:
                section = Section(
                    name=S[0],
                    lesson_id=Lesson.query.filter_by(name=S[1]).first().id,
                    hour=timedelta(hours=S[2])
                )
                db.session.add(section)
                print u'导入节信息', S[0], S[1]
        db.session.commit()

    def __repr__(self):
        return '<Section %r>' % self.name


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
        for A in assignments:
            assignment = Assignment.query.filter_by(name=A[0]).first()
            if assignment is None:
                assignment = Assignment(
                    name=A[0],
                    lesson_id=Lesson.query.filter_by(name=A[1]).first().id
                )
                db.session.add(assignment)
                print u'导入作业信息', A[0], A[1]
        db.session.commit()

    def __repr__(self):
        return '<Assignment %r>' % self.name


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

    @staticmethod
    def insert_tests():
        tests = [
            (u'L1-5', u'L5', ),
            (u'L6-9', u'L9', ),
            (u'初始成绩', u'Y-GRE总论', ),
            (u'Unit 1', u'1st', ),
            (u'Unit 2', u'2nd', ),
            (u'Unit 3', u'3rd', ),
            (u'Unit 4', u'4th', ),
            (u'Unit 5', u'5th', ),
            (u'Unit 6', u'6th', ),
            (u'模考1', u'Y-GRE总论', ),
            (u'模考2', u'Y-GRE总论', ),
            (u'PPII-1', u'Y-GRE总论', ),
            (u'PPII-2', u'Y-GRE总论', ),
            (u'GRE', u'Y-GRE总论', ),
        ]
        for T in tests:
            test = Test.query.filter_by(name=T[0]).first()
            if test is None:
                test = Test(
                    name=T[0],
                    lesson_id=Lesson.query.filter_by(name=T[1]).first().id
                )
                db.session.add(test)
                print u'导入考试信息', T[0], T[1]
        db.session.commit()

    def __repr__(self):
        return '<Test %r>' % self.name


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
        for AT in announcement_types:
            announcement_type = AnnouncementType.query.filter_by(name=AT[0]).first()
            if announcement_type is None:
                announcement_type = AnnouncementType(name=AT[0])
                db.session.add(announcement_type)
                print u'导入通知类型', AT[0]
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
            for user in User.query.all():
                if user.can(Permission.BOOK):
                    send_email(user.email, self.title, 'manage/mail/announcement', user=user, announcement=self)
        if self.type.name == u'管理邮件通知':
            for user in User.query.all():
                if user.can(Permission.MANAGE):
                    send_email(user.email, self.title, 'manage/mail/announcement', user=user, announcement=self)
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
        target.body = reduce(lambda paragraph1, paragraph2: paragraph1 + '\n\n' + paragraph2, [child.get_text() for child in [child for child in soup.descendants if (reduce(lambda tag1, tag2: len(BeautifulSoup(unicode(child), 'html.parser').find_all(tag1))==1 or len(BeautifulSoup(unicode(child), 'html.parser').find_all(tag2))==1, newline_tags))] if child.get_text()])

    def __repr__(self):
        return '<Announcement %r>' % self.title


db.event.listen(Announcement.body_html, 'set', Announcement.on_changed_body_html)