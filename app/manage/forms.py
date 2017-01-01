# -*- coding: utf-8 -*-

from datetime import date, time, timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, DateField, IntegerField, FloatField, SelectField, SelectMultipleField, SubmitField
from wtforms.validators import Required, NumberRange, Length, Email
from wtforms import ValidationError
from ..models import Role, User, Relationship, PurposeType, ReferrerType, Period, iPad, iPadCapacity, iPadState, Room, Lesson, Section, Course, CourseType, Announcement, AnnouncementType


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
    name = StringField(u'时段名称', validators=[Required()])
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
    name = StringField(u'时段名称', validators=[Required()])
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
    serial = StringField(u'序列号', validators=[Required()])
    capacity = SelectField(u'容量', coerce=int)
    room = SelectField(u'房间', coerce=int)
    state = SelectField(u'状态', coerce=int)
    video_playback = FloatField(u'满电量可播放视频时间', validators=[Required(), NumberRange(min=0)])
    vb_lessons = SelectMultipleField(u'VB内容', coerce=int)
    y_gre_lessons = SelectMultipleField(u'Y-GRE内容', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewiPadForm, self).__init__(*args, **kwargs)
        self.capacity.choices = [(capacity.id, capacity.name) for capacity in iPadCapacity.query.order_by(iPadCapacity.id.asc()).all()]
        self.room.choices = [(0, u'无')] + [(room.id, room.name) for room in Room.query.order_by(Room.id.asc()).all()]
        self.state.choices = [(state.id, state.name) for state in iPadState.query.order_by(iPadState.id.asc()).all() if state.name not in [u'借出']]
        self.vb_lessons.choices = [(lesson.id, lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'VB']
        self.y_gre_lessons.choices = [(lesson.id, lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'Y-GRE']

    def validate_serial(self, field):
        if iPad.query.filter_by(serial=field.data).first():
            raise ValidationError(u'序列号为%s的iPad已存在' % field.data)


class EditiPadForm(FlaskForm):
    alias = StringField(u'编号')
    serial = StringField(u'序列号', validators=[Required()])
    capacity = SelectField(u'容量', coerce=int)
    room = SelectField(u'房间', coerce=int)
    state = SelectField(u'状态', coerce=int)
    video_playback = FloatField(u'满电量可播放视频时间', validators=[Required(), NumberRange(min=0)])
    vb_lessons = SelectMultipleField(u'VB内容', coerce=int)
    y_gre_lessons = SelectMultipleField(u'Y-GRE内容', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, ipad, *args, **kwargs):
        super(EditiPadForm, self).__init__(*args, **kwargs)
        self.capacity.choices = [(capacity.id, capacity.name) for capacity in iPadCapacity.query.order_by(iPadCapacity.id.asc()).all()]
        self.room.choices = [(0, u'无')] + [(room.id, room.name) for room in Room.query.order_by(Room.id.asc()).all()]
        self.state.choices = [(state.id, state.name) for state in iPadState.query.order_by(iPadState.id.asc()).all()  if state.name not in [u'借出']]
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


class BookingCodeForm(FlaskForm):
    booking_code = StringField(u'预约码', validators=[Required()])
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
    serial = StringField(u'iPad序列号', validators=[Required()])
    battery_life = IntegerField(u'剩余电量', validators=[Required(), NumberRange(min=0, max=100)])
    root = BooleanField(u'引导式访问状态正常')
    submit = SubmitField(u'确认并提交')


class SelectLessonForm(FlaskForm):
    lesson = SelectField(u'课程', coerce=int)
    submit = SubmitField(u'下一步')

    def __init__(self, *args, **kwargs):
        super(SelectLessonForm, self).__init__(*args, **kwargs)
        self.lesson.choices = [(lesson.id, u'%s：%s' % (lesson.type.name, lesson.name)) for lesson in Lesson.query.order_by(Lesson.id.asc()).all()]


class RentiPadByLessonForm(FlaskForm):
    ipad = SelectField(u'可用iPad', coerce=int)
    submit = SubmitField(u'下一步')

    def __init__(self, lesson, *args, **kwargs):
        super(RentiPadByLessonForm, self).__init__(*args, **kwargs)
        self.ipad.choices = [(item.ipad_id, u'%s %s %s %s：%s' % (item.ipad.alias, item.ipad.capacity.name, item.ipad.state.name, item.ipad.room.name, reduce(lambda x, y: x + u'、' + y, [lesson.name for lesson in item.ipad.has_lessons]))) for item in lesson.occupied_ipads if (item.ipad.state.name in [u'待机', u'候补']) and (item.ipad.deleted == False)]


class iPadSerialForm(FlaskForm):
    serial = StringField(u'iPad序列号', validators=[Required()])
    root = BooleanField(u'引导式访问状态正常')
    battery = BooleanField(u'电量充足')
    submit = SubmitField(u'下一步')


class PunchLessonForm(FlaskForm):
    lesson = SelectField(u'课程进度', coerce=int)
    submit = SubmitField(u'下一步')

    def __init__(self, user, *args, **kwargs):
        super(PunchLessonForm, self).__init__(*args, **kwargs)
        self.lesson.choices = [(lesson.id, u'%s：%s' % (lesson.type.name, lesson.name)) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.id >= user.last_punch.section.lesson_id]


class PunchSectionForm(FlaskForm):
    section = SelectField(u'视频进度', coerce=int)
    submit = SubmitField(u'下一步')

    def __init__(self, user, lesson, *args, **kwargs):
        super(PunchSectionForm, self).__init__(*args, **kwargs)
        self.section.choices = [(section.id, u'%s：%s' % (section.lesson.name, section.name)) for section in Section.query.filter_by(lesson_id=lesson.id).order_by(Section.id.asc()).all() if section.id >= user.last_punch.section_id]


class ConfirmPunchForm(FlaskForm):
    submit = SubmitField(u'确认并提交')


class NewAnnouncementForm(FlaskForm):
    title = StringField(u'通知标题', validators=[Required()])
    body = TextAreaField(u'通知内容', validators=[Required()])
    announcement_type = SelectField(u'通知类型', coerce=int)
    show = BooleanField(u'立即发布')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewAnnouncementForm, self).__init__(*args, **kwargs)
        self.announcement_type.choices = [(announcement_type.id, announcement_type.name) for announcement_type in AnnouncementType.query.order_by(AnnouncementType.id.asc()).all()]


class EditAnnouncementForm(FlaskForm):
    title = StringField(u'通知标题', validators=[Required()])
    body = TextAreaField(u'通知内容', validators=[Required()])
    announcement_type = SelectField(u'通知类型', coerce=int)
    show = BooleanField(u'发布')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditAnnouncementForm, self).__init__(*args, **kwargs)
        self.announcement_type.choices = [(announcement_type.id, announcement_type.name) for announcement_type in AnnouncementType.query.order_by(AnnouncementType.id.asc()).all()]


class DeleteAnnouncementForm(FlaskForm):
    submit = SubmitField(u'删除')


class NewUserForm(FlaskForm):
    # basic
    name = StringField(u'姓名', validators=[Required(), Length(1, 64)])
    id_number = StringField(u'身份证号', validators=[Required(), Length(1, 64)])
    # education
    high_school = StringField(u'毕业高中', validators=[Length(1, 64)])
    cee_total = IntegerField(u'高考总分', validators=[NumberRange(min=0)])
    cee_math = IntegerField(u'高考数学', validators=[NumberRange(min=0)])
    cee_english = IntegerField(u'高考英语', validators=[NumberRange(min=0)])
    high_school_year = SelectField(u'入学年份', coerce=int)
    # bachelor
    bachelor_school = StringField(u'本科学校', validators=[Length(1, 64)])
    bachelor_major = StringField(u'院系（专业）', validators=[Length(1, 64)])
    bachelor_gpa = FloatField(u'GPA', validators=[NumberRange(min=0)])
    bachelor_full_gpa = FloatField(u'GPA满分', validators=[NumberRange(min=0)])
    bachelor_year = SelectField(u'入学年份', coerce=int)
    # master
    master_school = StringField(u'研究生学校（硕士）', validators=[Length(1, 64)])
    master_major = StringField(u'院系（专业）', validators=[Length(1, 64)])
    master_gpa = FloatField(u'GPA', validators=[NumberRange(min=0)])
    master_full_gpa = FloatField(u'GPA满分', validators=[NumberRange(min=0)])
    master_year = SelectField(u'入学年份', coerce=int)
    # doctor
    doctor_school = StringField(u'研究生学校（博士）', validators=[Length(1, 64)])
    doctor_major = StringField(u'院系（专业）', validators=[Length(1, 64)])
    doctor_gpa = FloatField(u'GPA', validators=[NumberRange(min=0)])
    doctor_full_gpa = FloatField(u'GPA满分', validators=[NumberRange(min=0)])
    doctor_year = SelectField(u'入学年份', coerce=int)
    # scores
    cet_4 = IntegerField(u'CET-4', validators=[NumberRange(min=0)])
    cet_6 = IntegerField(u'CET-6', validators=[NumberRange(min=0)])
    tem_4 = IntegerField(u'TEM-4', validators=[NumberRange(min=0)])
    tem_8 = IntegerField(u'TEM-8', validators=[NumberRange(min=0)])
    toefl_total = IntegerField(u'TOEFL', validators=[NumberRange(min=0, max=120)])
    toefl_reading = IntegerField(u'Reading', validators=[NumberRange(min=0, max=30)])
    toefl_listening = IntegerField(u'Listening', validators=[NumberRange(min=0, max=30)])
    toefl_speaking = IntegerField(u'Speaking', validators=[NumberRange(min=0, max=30)])
    toefl_writing = IntegerField(u'Writing', validators=[NumberRange(min=0, max=30)])
    competition = StringField(u'竞赛成绩', validators=[Length(1, 128)])
    other_score = StringField(u'其它成绩', validators=[Length(1, 128)])
    # job 1
    employer_1 = StringField(u'工作单位', validators=[Length(1, 64)])
    position_1 = StringField(u'职务', validators=[Length(1, 64)])
    job_year_1 = SelectField(u'入职年份', coerce=int)
    # job 2
    employer_2 = StringField(u'工作单位', validators=[Length(1, 64)])
    position_2 = StringField(u'职务', validators=[Length(1, 64)])
    job_year_2 = SelectField(u'入职年份', coerce=int)
    # contact
    email = StringField(u'电子邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    mobile = StringField(u'移动电话', validators=[Required(), Length(1, 64)])
    address = StringField(u'联系地址', validators=[Required(), Length(1, 64)])
    qq = StringField(u'QQ', validators=[Length(1, 64)])
    wechat = StringField(u'微信', validators=[Length(1, 64)])
    # emergency contact
    emergency_contact_name = StringField(u'姓名', validators=[Required(), Length(1, 64)])
    emergency_contact_relationship = SelectField(u'关系', coerce=int)
    emergency_contact_mobile = StringField(u'联系方式', validators=[Required(), Length(1, 64)])
    # registration
    purposes = SelectMultipleField(u'研修目的', coerce=int)
    other_purpose = StringField(u'其它研修目的', validators=[Length(1, 64)])
    referrers = SelectMultipleField(u'了解渠道', coerce=int)
    other_referrer = StringField(u'其它了解渠道', validators=[Length(1, 64)])
    role = SelectField(u'研修类别', coerce=int)
    vb_course = SelectField(u'VB班', coerce=int)
    y_gre_course = SelectField(u'Y-GRE班', coerce=int)
    worked_in_same_field = BooleanField(u'（曾）在培训/留学机构任职')
    deformity = BooleanField(u'有严重心理或身体疾病')
    # submit
    submit = SubmitField(u'新建学生用户')

    def __init__(self, *args, **kwargs):
        super(NewUserForm, self).__init__(*args, **kwargs)
        self.high_school_year.choices = [(year, u'%s年' % year) for year in range(int(date.today().year), 1948, -1)]
        self.bachelor_year.choices = [(year, u'%s年' % year) for year in range(int(date.today().year), 1948, -1)]
        self.master_year.choices = [(year, u'%s年' % year) for year in range(int(date.today().year), 1948, -1)]
        self.doctor_year.choices = [(year, u'%s年' % year) for year in range(int(date.today().year), 1948, -1)]
        self.job_year_1.choices = [(year, u'%s年' % year) for year in range(int(date.today().year), 1948, -1)]
        self.job_year_2.choices = [(year, u'%s年' % year) for year in range(int(date.today().year), 1948, -1)]
        self.emergency_contact_relationship.choices = [(relationship.id, relationship.name) for relationship in Relationship.query.order_by(Relationship.id.asc()).all()]
        self.purposes.choices = [(purpose_type.id, purpose_type.name) for purpose_type in PurposeType.query.order_by(PurposeType.id.asc()).all() if purpose_type.name != u'其它']
        self.referrers.choices = [(referrer_type.id, referrer_type.name) for referrer_type in ReferrerType.query.order_by(ReferrerType.id.asc()).all() if referrer_type.name != u'其它']
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'单VB', u'Y-GRE 普通', u'Y-GRE VBx2', u'Y-GRE A权限']]
        self.vb_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.filter_by(show=True, deleted=False).order_by(Course.id.desc()).all() if course.type.name == u'VB']
        self.y_gre_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.filter_by(show=True, deleted=False).order_by(Course.id.desc()).all() if course.type.name == u'Y-GRE']

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'%s已经被注册' % field.data)


class NewAdminForm(FlaskForm):
    name = StringField(u'姓名', validators=[Required(), Length(1, 64)])
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    activation_code = StringField(u'激活码', validators=[Required(), Length(6, 64)])
    role = SelectField(u'用户组', coerce=int)
    submit = SubmitField(u'新建管理用户')

    def __init__(self, creator, *args, **kwargs):
        super(NewAdminForm, self).__init__(*args, **kwargs)
        if creator.is_developer:
            self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'志愿者', u'协管员', u'管理员', u'开发人员']]
        else:
            self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'志愿者', u'协管员', u'管理员']]

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'%s已经被注册' % field.data)


class EditUserForm(FlaskForm):
    name = StringField(u'姓名', validators=[Required(), Length(1, 64)])
    role = SelectField(u'用户组', coerce=int)
    vb_course = SelectField(u'VB班', coerce=int)
    y_gre_course = SelectField(u'Y-GRE班', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, creator, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        if creator.is_developer:
            self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.id.asc()).all()]
        elif creator.is_administrator:
            self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name not in [u'开发人员']]
        else:
            self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'挂起', u'单VB', u'Y-GRE 普通', u'Y-GRE VBx2', u'Y-GRE A权限']]
        self.vb_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.filter_by(show=True, deleted=False).order_by(Course.id.desc()).all() if course.type.name == u'VB']
        self.y_gre_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.filter_by(show=True, deleted=False).order_by(Course.id.desc()).all() if course.type.name == u'Y-GRE']


class DeleteUserForm(FlaskForm):
    submit = SubmitField(u'删除')


class FindUserForm(FlaskForm):
    name_or_email = StringField(u'用户姓名/邮箱', validators=[Required(), Length(1, 64)])
    submit = SubmitField(u'检索')


class NewCourseForm(FlaskForm):
    name = StringField(u'班级名称', validators=[Required(), Length(1, 64)])
    course_type = SelectField(u'班级类型', coerce=int)
    show = BooleanField(u'显示为可选')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewCourseForm, self).__init__(*args, **kwargs)
        self.course_type.choices = [(course_type.id, course_type.name) for course_type in CourseType.query.order_by(CourseType.id.asc()).all()]


class EditCourseForm(FlaskForm):
    name = StringField(u'班级名称', validators=[Required(), Length(1, 64)])
    course_type = SelectField(u'班级类型', coerce=int)
    show = BooleanField(u'显示为可选')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditCourseForm, self).__init__(*args, **kwargs)
        self.course_type.choices = [(course_type.id, course_type.name) for course_type in CourseType.query.order_by(CourseType.id.asc()).all()]


class DeleteCourseForm(FlaskForm):
    submit = SubmitField(u'删除')