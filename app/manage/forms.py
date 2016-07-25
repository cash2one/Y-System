# -*- coding: utf-8 -*-

from datetime import date, timedelta
from flask_wtf import Form
from wtforms import StringField, BooleanField, DateField, IntegerField, SelectField, SelectMultipleField, SubmitField
from wtforms.validators import Required, NumberRange, Length, Email
from wtforms import ValidationError
from ..models import Role, User, Period, iPad, iPadCapacity, iPadState, Room, Lesson, Course


def NextDayString(days, short=False):
    day = date.today() + timedelta(days=1) * days
    if short:
        return day.strftime('%Y-%m-%d')
    return day.strftime('%Y-%m-%d %a')


class NewScheduleForm(Form):
    date = SelectField(u'日期', coerce=unicode)
    period = SelectMultipleField(u'时段', coerce=int)
    quota = IntegerField(u'名额', validators=[Required(), NumberRange(min=1)])
    publish_now = BooleanField(u'立即发布')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewScheduleForm, self).__init__(*args, **kwargs)
        self.date.choices = [(NextDayString(x, short=True), NextDayString(x), ) for x in range(30)]
        self.period.choices = [(period.id, period.alias) for period in Period.query.order_by(Period.id.asc()).all()]


class NewiPadForm(Form):
    alias = StringField(u'编号')
    serial = StringField(u'序列号', validators=[Required(message=u'请输入iPad序列号')])
    capacity = SelectField(u'容量', coerce=int)
    room = SelectField(u'房间', coerce=int)
    state = SelectField(u'状态', coerce=int)
    vb_lessons = SelectMultipleField(u'VB内容', coerce=int)
    y_gre_lessons = SelectMultipleField(u'Y-GRE内容', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewiPadForm, self).__init__(*args, **kwargs)
        self.capacity.choices = [(capacity.id, capacity.name) for capacity in iPadCapacity.query.order_by(iPadCapacity.id.asc()).all()]
        self.room.choices = [(0, u'无')] + [(room.id, room.name) for room in Room.query.order_by(Room.id.asc()).all()]
        self.state.choices = [(state.id, state.name) for state in iPadState.query.order_by(iPadState.id.asc()).all()]
        self.vb_lessons.choices = [(lesson.id, lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'VB']
        self.y_gre_lessons.choices = [(lesson.id, lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'Y-GRE']

    def validate_serial(self, field):
        if iPad.query.filter_by(serial=field.data).first():
            raise ValidationError(u'序列号为%s的iPad已存在' % field.data)


class EditiPadForm(Form):
    alias = StringField(u'编号')
    serial = StringField(u'序列号', validators=[Required(message=u'请输入iPad序列号')])
    capacity = SelectField(u'容量', coerce=int)
    room = SelectField(u'房间', coerce=int)
    state = SelectField(u'状态', coerce=int)
    vb_lessons = SelectMultipleField(u'VB内容', coerce=int)
    y_gre_lessons = SelectMultipleField(u'Y-GRE内容', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, ipad, *args, **kwargs):
        super(EditiPadForm, self).__init__(*args, **kwargs)
        self.capacity.choices = [(capacity.id, capacity.name) for capacity in iPadCapacity.query.order_by(iPadCapacity.id.asc()).all()]
        self.room.choices = [(0, u'无')] + [(room.id, room.name) for room in Room.query.order_by(Room.id.asc()).all()]
        self.state.choices = [(state.id, state.name) for state in iPadState.query.order_by(iPadState.id.asc()).all()]
        self.vb_lessons.choices = [(lesson.id, lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'VB']
        self.y_gre_lessons.choices = [(lesson.id, lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'Y-GRE']
        self.ipad = ipad

    def validate_serial(self, field):
        if field.data != self.ipad.serial and iPad.query.filter_by(serial=field.data).first():
            raise ValidationError(u'序列号为%s的iPad已存在' % field.data)


class DeleteiPadForm(Form):
    submit = SubmitField(u'提交')


class FilteriPadForm(Form):
    vb_lessons = SelectMultipleField(u'VB内容', coerce=int)
    y_gre_lessons = SelectMultipleField(u'Y-GRE内容', coerce=int)
    submit = SubmitField(u'筛选')

    def __init__(self, *args, **kwargs):
        super(FilteriPadForm, self).__init__(*args, **kwargs)
        self.vb_lessons.choices = [(lesson.id, lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'VB']
        self.y_gre_lessons.choices = [(lesson.id, lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'Y-GRE']


class NewActivationForm(Form):
    name = StringField(u'姓名', validators=[Required(message=u'请输入姓名'), Length(1, 64)])
    activation_code = StringField(u'激活码', validators=[Required(message=u'请输入激活码'), Length(6, 64)])
    role = SelectField(u'用户组', coerce=int)
    vb_course = SelectField(u'VB班', coerce=int)
    y_gre_course = SelectField(u'Y-GRE班', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewActivationForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'禁止预约', u'单VB', u'Y-GRE 普通', u'Y-GRE VBx2', u'Y-GRE A权限']]
        self.vb_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'VB']
        self.y_gre_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'Y-GRE']


class EditActivationForm(Form):
    name = StringField(u'姓名', validators=[Required(message=u'请输入姓名'), Length(1, 64)])
    activation_code = StringField(u'激活码', validators=[Required(message=u'请输入激活码'), Length(6, 64)])
    role = SelectField(u'用户组', coerce=int)
    vb_course = SelectField(u'VB班', coerce=int)
    y_gre_course = SelectField(u'Y-GRE班', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditActivationForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'禁止预约', u'单VB', u'Y-GRE 普通', u'Y-GRE VBx2', u'Y-GRE A权限']]
        self.vb_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'VB']
        self.y_gre_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'Y-GRE']


class DeleteActivationForm(Form):
    submit = SubmitField(u'提交')


class EditUserForm(Form):
    name = StringField(u'姓名', validators=[Required(message=u'请输入姓名'), Length(1, 64)])
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    role = SelectField(u'用户组', coerce=int)
    vb_course = SelectField(u'VB班', coerce=int)
    y_gre_course = SelectField(u'Y-GRE班', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, user, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'禁止预约', u'单VB', u'Y-GRE 普通', u'Y-GRE VBx2', u'Y-GRE A权限']]
        self.vb_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'VB']
        self.y_gre_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'Y-GRE']
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError(u'%s已经被注册' % field.data)


class EditAuthForm(Form):
    name = StringField(u'姓名', validators=[Required(message=u'请输入姓名'), Length(1, 64)])
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    role = SelectField(u'用户组', coerce=int)
    vb_course = SelectField(u'VB班', coerce=int)
    y_gre_course = SelectField(u'Y-GRE班', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, user, *args, **kwargs):
        super(EditAuthForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name not in [u'管理员', u'开发人员']]
        self.vb_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'VB']
        self.y_gre_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'Y-GRE']
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError(u'%s已经被注册' % field.data)


class EditAuthFormAdmin(Form):
    name = StringField(u'姓名', validators=[Required(message=u'请输入姓名'), Length(1, 64)])
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    role = SelectField(u'用户组', coerce=int)
    vb_course = SelectField(u'VB班', coerce=int)
    y_gre_course = SelectField(u'Y-GRE班', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, user, *args, **kwargs):
        super(EditAuthFormAdmin, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name not in [u'开发人员']]
        self.vb_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'VB']
        self.y_gre_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'Y-GRE']
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError(u'%s已经被注册' % field.data)
