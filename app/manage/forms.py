# -*- coding: utf-8 -*-

from datetime import date, time, timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, DateField, IntegerField, SelectField, SelectMultipleField, SubmitField
from wtforms.validators import Required, NumberRange, Length, Email
from wtforms import ValidationError
from ..models import Role, User, Period, iPad, iPadCapacity, iPadState, Room, Lesson, Section, Course, CourseType, Announcement, AnnouncementType


def NextDayString(days, short=False):
    day = date.today() + timedelta(days=1) * days
    if short:
        return day.strftime(u'%Y-%m-%d')
    return day.strftime(u'%Y-%m-%d %a')


def NextHalfHourString(halfHours, startHour=6):
    t = time(startHour + halfHours/2, (halfHours % 2) * 30)
    return t.strftime(u'%H:%M')


class NewScheduleForm(FlaskForm):
    date = SelectField(u'日期', coerce=unicode)
    period = SelectMultipleField(u'时段', coerce=int)
    quota = IntegerField(u'名额', validators=[Required(), NumberRange(min=1)])
    publish_now = BooleanField(u'立即发布')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewScheduleForm, self).__init__(*args, **kwargs)
        self.date.choices = [(NextDayString(x, short=True), NextDayString(x), ) for x in range(30)]
        self.period.choices = [(period.id, period.alias3) for period in Period.query.order_by(Period.id.asc()).all() if (period.show and not period.deleted)]


class NewPeriodForm(FlaskForm):
    name = StringField(u'时段名称', validators=[Required(message=u'请输入时段名称')])
    start_time = SelectField(u'开始时间', coerce=unicode)
    end_time = SelectField(u'结束时间', coerce=unicode)
    period_type = SelectField(u'时段类型', coerce=int)
    show = BooleanField(u'显示为可选')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewPeriodForm, self).__init__(*args, **kwargs)
        self.start_time.choices = [(NextHalfHourString(x), NextHalfHourString(x), ) for x in range(36)]
        self.end_time.choices = [(NextHalfHourString(x), NextHalfHourString(x), ) for x in range(36)]
        self.period_type.choices = [(period_type.id, period_type.name) for period_type in CourseType.query.order_by(CourseType.id.asc()).all()]


class EditPeriodForm(FlaskForm):
    name = StringField(u'时段名称', validators=[Required(message=u'请输入时段名称')])
    start_time = SelectField(u'开始时间', coerce=unicode)
    end_time = SelectField(u'结束时间', coerce=unicode)
    period_type = SelectField(u'时段类型', coerce=int)
    show = BooleanField(u'显示为可选')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditPeriodForm, self).__init__(*args, **kwargs)
        self.start_time.choices = [(NextHalfHourString(x), NextHalfHourString(x), ) for x in range(36)]
        self.end_time.choices = [(NextHalfHourString(x), NextHalfHourString(x), ) for x in range(36)]
        self.period_type.choices = [(period_type.id, period_type.name) for period_type in CourseType.query.order_by(CourseType.id.asc()).all()]


class DeletePeriodForm(FlaskForm):
    submit = SubmitField(u'删除')


class NewiPadForm(FlaskForm):
    alias = StringField(u'编号')
    serial = StringField(u'序列号', validators=[Required(message=u'请输入iPad序列号')])
    capacity = SelectField(u'容量', coerce=int)
    room = SelectField(u'房间', coerce=int)
    state = SelectField(u'状态', coerce=int)
    video_playback = SelectField(u'满电量可播放视频时间', coerce=unicode)
    vb_lessons = SelectMultipleField(u'VB内容', coerce=int)
    y_gre_lessons = SelectMultipleField(u'Y-GRE内容', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewiPadForm, self).__init__(*args, **kwargs)
        self.capacity.choices = [(capacity.id, capacity.name) for capacity in iPadCapacity.query.order_by(iPadCapacity.id.asc()).all()]
        self.room.choices = [(0, u'无')] + [(room.id, room.name) for room in Room.query.order_by(Room.id.asc()).all()]
        self.state.choices = [(state.id, state.name) for state in iPadState.query.order_by(iPadState.id.asc()).all() if state.name not in [u'借出']]
        self.video_playback.choices = [(NextHalfHourString(x, startHour=0), NextHalfHourString(x, startHour=0), ) for x in range(20, 0, -1)]
        self.vb_lessons.choices = [(lesson.id, lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'VB']
        self.y_gre_lessons.choices = [(lesson.id, lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'Y-GRE']

    def validate_serial(self, field):
        if iPad.query.filter_by(serial=field.data).first():
            raise ValidationError(u'序列号为%s的iPad已存在' % field.data)


class EditiPadForm(FlaskForm):
    alias = StringField(u'编号')
    serial = StringField(u'序列号', validators=[Required(message=u'请输入iPad序列号')])
    capacity = SelectField(u'容量', coerce=int)
    room = SelectField(u'房间', coerce=int)
    state = SelectField(u'状态', coerce=int)
    video_playback = SelectField(u'满电量可播放视频时间', coerce=unicode)
    vb_lessons = SelectMultipleField(u'VB内容', coerce=int)
    y_gre_lessons = SelectMultipleField(u'Y-GRE内容', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, ipad, *args, **kwargs):
        super(EditiPadForm, self).__init__(*args, **kwargs)
        self.capacity.choices = [(capacity.id, capacity.name) for capacity in iPadCapacity.query.order_by(iPadCapacity.id.asc()).all()]
        self.room.choices = [(0, u'无')] + [(room.id, room.name) for room in Room.query.order_by(Room.id.asc()).all()]
        self.state.choices = [(state.id, state.name) for state in iPadState.query.order_by(iPadState.id.asc()).all()  if state.name not in [u'借出']]
        self.video_playback.choices = [(NextHalfHourString(x, startHour=0), NextHalfHourString(x, startHour=0), ) for x in range(20, 0, -1)]
        self.vb_lessons.choices = [(lesson.id, lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'VB']
        self.y_gre_lessons.choices = [(lesson.id, lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'Y-GRE']
        self.ipad = ipad

    def validate_serial(self, field):
        if field.data != self.ipad.serial and iPad.query.filter_by(serial=field.data).first():
            raise ValidationError(u'序列号为%s的iPad已存在' % field.data)


class DeleteiPadForm(FlaskForm):
    submit = SubmitField(u'删除')


class FilteriPadForm(FlaskForm):
    vb_lessons = SelectMultipleField(u'VB内容', coerce=int)
    y_gre_lessons = SelectMultipleField(u'Y-GRE内容', coerce=int)
    submit = SubmitField(u'筛选')

    def __init__(self, *args, **kwargs):
        super(FilteriPadForm, self).__init__(*args, **kwargs)
        self.vb_lessons.choices = [(lesson.id, lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'VB']
        self.y_gre_lessons.choices = [(lesson.id, lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'Y-GRE']


class NewActivationForm(FlaskForm):
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


class NewActivationFormAuth(FlaskForm):
    name = StringField(u'姓名', validators=[Required(message=u'请输入姓名'), Length(1, 64)])
    activation_code = StringField(u'激活码', validators=[Required(message=u'请输入激活码'), Length(6, 64)])
    role = SelectField(u'用户组', coerce=int)
    vb_course = SelectField(u'VB班', coerce=int)
    y_gre_course = SelectField(u'Y-GRE班', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewActivationFormAuth, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name not in [u'开发人员']]
        self.vb_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'VB']
        self.y_gre_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'Y-GRE']


class NewActivationFormAdmin(FlaskForm):
    name = StringField(u'姓名', validators=[Required(message=u'请输入姓名'), Length(1, 64)])
    activation_code = StringField(u'激活码', validators=[Required(message=u'请输入激活码'), Length(6, 64)])
    role = SelectField(u'用户组', coerce=int)
    vb_course = SelectField(u'VB班', coerce=int)
    y_gre_course = SelectField(u'Y-GRE班', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewActivationFormAdmin, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.id.asc()).all()]
        self.vb_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'VB']
        self.y_gre_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'Y-GRE']


class EditActivationForm(FlaskForm):
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


class EditActivationFormAuth(FlaskForm):
    name = StringField(u'姓名', validators=[Required(message=u'请输入姓名'), Length(1, 64)])
    activation_code = StringField(u'激活码', validators=[Required(message=u'请输入激活码'), Length(6, 64)])
    role = SelectField(u'用户组', coerce=int)
    vb_course = SelectField(u'VB班', coerce=int)
    y_gre_course = SelectField(u'Y-GRE班', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditActivationFormAuth, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name not in [u'开发人员']]
        self.vb_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'VB']
        self.y_gre_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'Y-GRE']


class EditActivationFormAdmin(FlaskForm):
    name = StringField(u'姓名', validators=[Required(message=u'请输入姓名'), Length(1, 64)])
    activation_code = StringField(u'激活码', validators=[Required(message=u'请输入激活码'), Length(6, 64)])
    role = SelectField(u'用户组', coerce=int)
    vb_course = SelectField(u'VB班', coerce=int)
    y_gre_course = SelectField(u'Y-GRE班', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditActivationFormAdmin, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.id.asc()).all()]
        self.vb_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'VB']
        self.y_gre_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'Y-GRE']


class DeleteActivationForm(FlaskForm):
    submit = SubmitField(u'删除')


class EditUserForm(FlaskForm):
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


class FindUserForm(FlaskForm):
    name_or_email = StringField(u'用户姓名/邮箱', validators=[Required(message=u'请输入用户姓名或者邮箱'), Length(1, 64)])
    submit = SubmitField(u'检索')


class EditPunchLessonForm(FlaskForm):
    lesson = SelectField(u'课程进度', coerce=int)
    submit = SubmitField(u'下一步')

    def __init__(self, *args, **kwargs):
        super(EditPunchLessonForm, self).__init__(*args, **kwargs)
        self.lesson.choices = [(lesson.id, u'%s：%s' % (lesson.type.name, lesson.name)) for lesson in Lesson.query.order_by(Lesson.id.asc()).all()]


class EditPunchSectionForm(FlaskForm):
    section = SelectField(u'视频进度', coerce=int)
    submit = SubmitField(u'下一步')

    def __init__(self, lesson, *args, **kwargs):
        super(EditPunchSectionForm, self).__init__(*args, **kwargs)
        self.section.choices = [(section.id, u'%s：%s' % (section.lesson.name, section.name)) for section in Section.query.filter_by(lesson_id=lesson.id).order_by(Section.id.asc()).all()]


class EditAuthForm(FlaskForm):
    name = StringField(u'姓名', validators=[Required(message=u'请输入姓名'), Length(1, 64)])
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    role = SelectField(u'用户组', coerce=int)
    vb_course = SelectField(u'VB班', coerce=int)
    y_gre_course = SelectField(u'Y-GRE班', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, user, *args, **kwargs):
        super(EditAuthForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name not in [u'开发人员']]
        self.vb_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'VB']
        self.y_gre_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'Y-GRE']
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError(u'%s已经被注册' % field.data)


class EditAuthFormAdmin(FlaskForm):
    name = StringField(u'姓名', validators=[Required(message=u'请输入姓名'), Length(1, 64)])
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    role = SelectField(u'用户组', coerce=int)
    vb_course = SelectField(u'VB班', coerce=int)
    y_gre_course = SelectField(u'Y-GRE班', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, user, *args, **kwargs):
        super(EditAuthFormAdmin, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.id.asc()).all()]
        self.vb_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'VB']
        self.y_gre_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.order_by(Course.id.desc()).all() if course.type.name == u'Y-GRE']
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError(u'%s已经被注册' % field.data)


class BookingCodeForm(FlaskForm):
    booking_code = StringField(u'预约码', validators=[Required(message=u'请输入预约码')])
    submit = SubmitField(u'下一步')


class RentiPadForm(FlaskForm):
    ipad = SelectField(u'可用iPad', coerce=int)
    submit = SubmitField(u'下一步')

    def __init__(self, user, *args, **kwargs):
        super(RentiPadForm, self).__init__(*args, **kwargs)
        self.ipad.choices = [(ipad.id, u'%s %s %s %s：%s' % (ipad.alias, ipad.capacity.name, ipad.state.name, ipad.room.name, reduce(lambda x, y: x + u'、' + y, [lesson.name for lesson in ipad.has_lessons]))) for ipad in user.fitted_ipads if ipad.state.name in [u'待机', u'候补']]


class RentalEmailForm(FlaskForm):
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    submit = SubmitField(u'下一步')


class ConfirmiPadForm(FlaskForm):
    serial = StringField(u'iPad序列号', validators=[Required(message=u'请输入iPad序列号')])
    battery_life = IntegerField(u'剩余电量', validators=[Required(message=u'请输入iPad电量'), NumberRange(min=0, max=100)])
    root = BooleanField(u'引导式访问状态正常')
    submit = SubmitField(u'确认并提交')


class ConfirmiPadFormWalkIn(FlaskForm):
    serial = StringField(u'iPad序列号', validators=[Required(message=u'请输入iPad序列号')])
    battery_life = IntegerField(u'剩余电量', validators=[Required(message=u'请输入iPad电量'), NumberRange(min=0, max=100)])
    root = BooleanField(u'引导式访问状态正常')
    walk_in = BooleanField(u'未预约到场')
    submit = SubmitField(u'确认并提交')


class iPadSerialForm(FlaskForm):
    serial = StringField(u'iPad序列号', validators=[Required(message=u'请输入iPad序列号')])
    root = BooleanField(u'引导式访问状态正常')
    battery = BooleanField(u'电量充足')
    submit = SubmitField(u'下一步')


class PunchLessonForm(FlaskForm):
    lesson = SelectField(u'课程进度', coerce=int)
    submit = SubmitField(u'下一步')

    def __init__(self, user, *args, **kwargs):
        super(PunchLessonForm, self).__init__(*args, **kwargs)
        self.lesson.choices = [(lesson.id, u'%s：%s' % (lesson.type.name, lesson.name)) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.id >= user.last_punch.lesson_id]


class PunchSectionForm(FlaskForm):
    section = SelectField(u'视频进度', coerce=int)
    submit = SubmitField(u'下一步')

    def __init__(self, user, lesson, *args, **kwargs):
        super(PunchSectionForm, self).__init__(*args, **kwargs)
        self.section.choices = [(section.id, u'%s：%s' % (section.lesson.name, section.name)) for section in Section.query.filter_by(lesson_id=lesson.id).order_by(Section.id.asc()).all() if section.id >= user.last_punch.section_id]


class ConfirmPunchForm(FlaskForm):
    submit = SubmitField(u'确认并提交')


class NewAnnouncementForm(FlaskForm):
    title = StringField(u'通知标题', validators=[Required(message=u'请输入通知标题')])
    body = TextAreaField(u'通知内容', validators=[Required(message=u'请输入通知内容')])
    announcement_type = SelectField(u'通知类型', coerce=int)
    show = BooleanField(u'立即发布')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewAnnouncementForm, self).__init__(*args, **kwargs)
        self.announcement_type.choices = [(announcement_type.id, announcement_type.name) for announcement_type in AnnouncementType.query.order_by(AnnouncementType.id.asc()).all()]


class EditAnnouncementForm(FlaskForm):
    title = StringField(u'通知标题', validators=[Required(message=u'请输入通知标题')])
    body = TextAreaField(u'通知内容', validators=[Required(message=u'请输入通知内容')])
    announcement_type = SelectField(u'通知类型', coerce=int)
    show = BooleanField(u'发布')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditAnnouncementForm, self).__init__(*args, **kwargs)
        self.announcement_type.choices = [(announcement_type.id, announcement_type.name) for announcement_type in AnnouncementType.query.order_by(AnnouncementType.id.asc()).all()]


class DeleteAnnouncementForm(FlaskForm):
    submit = SubmitField(u'删除')