# -*- coding: utf-8 -*-

from datetime import date, time, timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, DateField, IntegerField, FloatField, SelectField, SelectMultipleField, SubmitField
from wtforms.validators import Required, NumberRange, Length, Email
from wtforms import ValidationError
from ..models import Role, User, Relationship, PurposeType, ReferrerType, TOEFLTotalScore, TOEFLReadingScore, TOEFLListeningScore, TOEFLSpeakingScore, TOEFLWritingScore, EducationType, PreviousAchievementType, Product, Period, iPad, iPadCapacity, iPadState, Room, Lesson, Section, Course, CourseType, Announcement, AnnouncementType


EN_2_CN = {
    u'Mon': u'周一',
    u'Tue': u'周二',
    u'Wed': u'周三',
    u'Thu': u'周四',
    u'Fri': u'周五',
    u'Sat': u'周六',
    u'Sun': u'周日',
}


def NextDayString(days, short=False):
    day = date.today() + timedelta(days=1) * days
    if short:
        return day.strftime(u'%Y-%m-%d')
    return day.strftime(u'%Y-%m-%d') + u' ' + EN_2_CN[day.strftime(u'%a')]


def NextHalfHourString(halfHours, startHour=6):
    t = time(startHour + halfHours/2, (halfHours % 2) * 30)
    return t.strftime(u'%H:%M')


class NewScheduleForm(FlaskForm):
    date = SelectField(u'日期', coerce=unicode, validators=[Required()])
    period = SelectMultipleField(u'时段', coerce=unicode, validators=[Required()])
    quota = IntegerField(u'名额', validators=[Required(), NumberRange(min=1)])
    publish_now = BooleanField(u'立即发布')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewScheduleForm, self).__init__(*args, **kwargs)
        self.date.choices = [(u'', u'选择日期')] + [(NextDayString(x, short=True), NextDayString(x), ) for x in range(30)]
        self.period.choices = [(u'', u'选择时段')] + [(unicode(period.id), period.alias3) for period in Period.query.order_by(Period.id.asc()).all() if (period.show and not period.deleted)]


class NewPeriodForm(FlaskForm):
    name = StringField(u'时段名称', validators=[Required()])
    start_time = SelectField(u'开始时间', coerce=unicode, validators=[Required()])
    end_time = SelectField(u'结束时间', coerce=unicode, validators=[Required()])
    period_type = SelectField(u'时段类型', coerce=unicode, validators=[Required()])
    show = BooleanField(u'显示为可选')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewPeriodForm, self).__init__(*args, **kwargs)
        self.start_time.choices = [(u'', u'选择开始时间')] + [(NextHalfHourString(x), NextHalfHourString(x), ) for x in range(36)]
        self.end_time.choices = [(u'', u'选择结束时间')] + [(NextHalfHourString(x), NextHalfHourString(x), ) for x in range(36)]
        self.period_type.choices = [(u'', u'选择时段类型')] + [(unicode(period_type.id), period_type.name) for period_type in CourseType.query.order_by(CourseType.id.asc()).all()]


class EditPeriodForm(FlaskForm):
    name = StringField(u'时段名称', validators=[Required()])
    start_time = SelectField(u'开始时间', coerce=unicode, validators=[Required()])
    end_time = SelectField(u'结束时间', coerce=unicode, validators=[Required()])
    period_type = SelectField(u'时段类型', coerce=unicode, validators=[Required()])
    show = BooleanField(u'显示为可选')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditPeriodForm, self).__init__(*args, **kwargs)
        self.start_time.choices = [(u'', u'选择开始时间')] + [(NextHalfHourString(x), NextHalfHourString(x), ) for x in range(36)]
        self.end_time.choices = [(u'', u'选择结束时间')] + [(NextHalfHourString(x), NextHalfHourString(x), ) for x in range(36)]
        self.period_type.choices = [(u'', u'选择时段类型')] + [(unicode(period_type.id), period_type.name) for period_type in CourseType.query.order_by(CourseType.id.asc()).all()]


class DeletePeriodForm(FlaskForm):
    submit = SubmitField(u'删除')


class NewiPadForm(FlaskForm):
    alias = StringField(u'编号')
    serial = StringField(u'序列号', validators=[Required()])
    capacity = SelectField(u'容量', coerce=unicode, validators=[Required()])
    room = SelectField(u'房间', coerce=unicode, validators=[Required()])
    state = SelectField(u'状态', coerce=unicode, validators=[Required()])
    video_playback = FloatField(u'电池寿命', validators=[Required(), NumberRange(min=0)])
    vb_lessons = SelectMultipleField(u'VB内容', coerce=unicode)
    y_gre_lessons = SelectMultipleField(u'Y-GRE内容', coerce=unicode)
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewiPadForm, self).__init__(*args, **kwargs)
        self.capacity.choices = [(u'', u'选择容量')] + [(unicode(capacity.id), capacity.name) for capacity in iPadCapacity.query.order_by(iPadCapacity.id.asc()).all()]
        self.room.choices = [(u'', u'选择房间')] + [(u'0', u'无')] + [(unicode(room.id), room.name) for room in Room.query.order_by(Room.id.asc()).all()]
        self.state.choices = [(u'', u'选择状态')] + [(unicode(state.id), state.name) for state in iPadState.query.order_by(iPadState.id.asc()).all() if state.name not in [u'借出']]
        self.vb_lessons.choices = [(u'', u'选择VB内容')] + [(unicode(lesson.id), lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'VB']
        self.y_gre_lessons.choices = [(u'', u'选择Y-GRE内容')] + [(unicode(lesson.id), lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'Y-GRE']

    def validate_serial(self, field):
        if iPad.query.filter_by(serial=field.data).first():
            raise ValidationError(u'序列号为%s的iPad已存在' % field.data)


class EditiPadForm(FlaskForm):
    alias = StringField(u'编号')
    serial = StringField(u'序列号', validators=[Required()])
    capacity = SelectField(u'容量', coerce=unicode, validators=[Required()])
    room = SelectField(u'房间', coerce=unicode, validators=[Required()])
    state = SelectField(u'状态', coerce=unicode, validators=[Required()])
    video_playback = FloatField(u'电池寿命', validators=[Required(), NumberRange(min=0)])
    vb_lessons = SelectMultipleField(u'VB内容', coerce=unicode)
    y_gre_lessons = SelectMultipleField(u'Y-GRE内容', coerce=unicode)
    submit = SubmitField(u'提交')

    def __init__(self, ipad, *args, **kwargs):
        super(EditiPadForm, self).__init__(*args, **kwargs)
        self.capacity.choices = [(u'', u'选择容量')] + [(unicode(capacity.id), capacity.name) for capacity in iPadCapacity.query.order_by(iPadCapacity.id.asc()).all()]
        self.room.choices = [(u'', u'选择房间')] + [(u'0', u'无')] + [(unicode(room.id), room.name) for room in Room.query.order_by(Room.id.asc()).all()]
        self.state.choices = [(u'', u'选择状态')] + [(unicode(state.id), state.name) for state in iPadState.query.order_by(iPadState.id.asc()).all() if state.name not in [u'借出']]
        self.vb_lessons.choices = [(u'', u'选择VB内容')] + [(unicode(lesson.id), lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'VB']
        self.y_gre_lessons.choices = [(u'', u'选择Y-GRE内容')] + [(unicode(lesson.id), lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'Y-GRE']
        self.ipad = ipad

    def validate_serial(self, field):
        if field.data != self.ipad.serial and iPad.query.filter_by(serial=field.data).first():
            raise ValidationError(u'序列号为%s的iPad已存在' % field.data)


class DeleteiPadForm(FlaskForm):
    submit = SubmitField(u'删除')


class FilteriPadForm(FlaskForm):
    vb_lessons = SelectMultipleField(u'VB内容', coerce=unicode)
    y_gre_lessons = SelectMultipleField(u'Y-GRE内容', coerce=unicode)
    submit = SubmitField(u'筛选')

    def __init__(self, *args, **kwargs):
        super(FilteriPadForm, self).__init__(*args, **kwargs)
        self.vb_lessons.choices = [(u'', u'选择VB内容')] + [(unicode(lesson.id), lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'VB']
        self.y_gre_lessons.choices = [(u'', u'选择Y-GRE内容')] + [(unicode(lesson.id), lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'Y-GRE']


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
    announcement_type = SelectField(u'通知类型', coerce=unicode, validators=[Required()])
    show = BooleanField(u'立即发布')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewAnnouncementForm, self).__init__(*args, **kwargs)
        self.announcement_type.choices = [(u'', u'选择通知类型')] + [(unicode(announcement_type.id), announcement_type.name) for announcement_type in AnnouncementType.query.order_by(AnnouncementType.id.asc()).all()]


class EditAnnouncementForm(FlaskForm):
    title = StringField(u'通知标题', validators=[Required()])
    body = TextAreaField(u'通知内容', validators=[Required()])
    announcement_type = SelectField(u'通知类型', coerce=unicode, validators=[Required()])
    show = BooleanField(u'发布')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditAnnouncementForm, self).__init__(*args, **kwargs)
        self.announcement_type.choices = [(u'', u'选择通知类型')] + [(unicode(announcement_type.id), announcement_type.name) for announcement_type in AnnouncementType.query.order_by(AnnouncementType.id.asc()).all()]


class DeleteAnnouncementForm(FlaskForm):
    submit = SubmitField(u'删除')


class NewUserForm(FlaskForm):
    name = StringField(u'姓名', validators=[Required(), Length(1, 64)])
    id_number = StringField(u'身份证号', validators=[Required(), Length(1, 64)])
    email = StringField(u'电子邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    mobile = StringField(u'移动电话', validators=[Required(), Length(1, 64)])
    address = StringField(u'联系地址', validators=[Required(), Length(1, 64)])
    qq = StringField(u'QQ', validators=[Length(0, 64)])
    wechat = StringField(u'微信', validators=[Length(0, 64)])
    emergency_contact_name = StringField(u'姓名', validators=[Required(), Length(1, 64)])
    emergency_contact_relationship = SelectField(u'关系', coerce=unicode, validators=[Required()])
    emergency_contact_mobile = StringField(u'联系方式', validators=[Required(), Length(1, 64)])
    # registration
    # purposes = SelectMultipleField(u'研修目的', coerce=unicode)
    # other_purpose = StringField(u'其它研修目的', validators=[Length(1, 64)])
    # application_major = StringField(u'申请方向', validators=[Length(1, 64)])
    # referrers = SelectMultipleField(u'了解渠道', coerce=unicode)
    # other_referrer = StringField(u'其它了解渠道', validators=[Length(1, 64)])
    # inviter_email = StringField(u'推荐人（邮箱）', validators=[Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    # role = SelectField(u'研修类别', coerce=unicode, validators=[Required()])
    # vb_course = SelectField(u'VB班', coerce=unicode, validators=[Required()])
    # y_gre_course = SelectField(u'Y-GRE班', coerce=unicode, validators=[Required()])
    # products = SelectMultipleField(u'研修产品', coerce=unicode, validators=[Required()])
    # worked_in_same_field = BooleanField(u'（曾）在培训/留学机构任职')
    # deformity = BooleanField(u'有严重心理或身体疾病')
    # submit
    # disclaimer = BooleanField(u'确认无偿授权“云英语”使用申请者姓名、肖像、GRE成绩单以及其它必要信息用于宣传', validators=[Required()])
    # receptionist_email = StringField(u'接待人（邮箱）', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    submit = SubmitField(u'下一步')

    def __init__(self, *args, **kwargs):
        super(NewUserForm, self).__init__(*args, **kwargs)
        self.emergency_contact_relationship.choices = [(u'', u'关系')] +  [(unicode(relationship.id), relationship.name) for relationship in Relationship.query.order_by(Relationship.id.asc()).all()]
        # self.purposes.choices = [(u'', u'选择研修目的')] + [(unicode(purpose_type.id), purpose_type.name) for purpose_type in PurposeType.query.order_by(PurposeType.id.asc()).all() if purpose_type.name != u'其它']
        # self.referrers.choices = [(u'', u'选择了解渠道')] + [(unicode(referrer_type.id), referrer_type.name) for referrer_type in ReferrerType.query.order_by(ReferrerType.id.asc()).all() if referrer_type.name != u'其它']
        # self.role.choices = [(u'', u'选择研修类别')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'单VB', u'Y-GRE 普通', u'Y-GRE VBx2', u'Y-GRE A权限']]
        # self.vb_course.choices = [(u'', u'选择VB班')] + [(u'0', u'无')] + [(unicode(course.id), course.name) for course in Course.query.filter_by(show=True, deleted=False).order_by(Course.id.desc()).all() if course.type.name == u'VB']
        # self.y_gre_course.choices = [(u'', u'选择Y-GRE班')] +  [(u'0', u'无')] + [(unicode(course.id), course.name) for course in Course.query.filter_by(show=True, deleted=False).order_by(Course.id.desc()).all() if course.type.name == u'Y-GRE']
        # self.products.choices = [(u'', u'选择研修产品')] + [(unicode(product.id), u'%s（%s元）' % (product.name, product.price)) for product in Product.query.filter_by(available=True, deleted=False).order_by(Product.id.asc()).all() if product.name not in [u'团报优惠', u'按月延长有效期', u'一次性延长2年有效期']]

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'%s已经被注册' % field.data)


class NewEducationRecordForm(FlaskForm):
    education_type = SelectField(u'学历类型', coerce=unicode, validators=[Required()])
    school = StringField(u'学校', validators=[Required(), Length(1, 64)])
    major = StringField(u'院系（专业）', validators=[Required(), Length(1, 64)])
    gpa = FloatField(u'GPA')
    full_gpa = FloatField(u'GPA满分')
    year = SelectField(u'入学年份', coerce=unicode, validators=[Required()])

    def __init__(self, *args, **kwargs):
        super(NewEducationRecordForm, self).__init__(*args, **kwargs)
        self.education_type.choices = [(u'', u'选择学历类型')] + [(unicode(education_type.id), education_type.name) for education_type in EducationType.query.order_by(EducationType.id.asc()).all()]
        self.year.choices = [(u'', u'选择年份')] + [(unicode(year), u'%s年' % year) for year in range(int(date.today().year), 1948, -1)]


class NewEmploymentRecordForm(FlaskForm):
    employer = StringField(u'工作单位', validators=[Required(), Length(1, 64)])
    position = StringField(u'职务', validators=[Required(), Length(1, 64)])
    year = SelectField(u'入职年份', coerce=unicode, validators=[Required()])

    def __init__(self, *args, **kwargs):
        super(NewUserForm, self).__init__(*args, **kwargs)
        self.year.choices = [(u'', u'选择年份')] + [(unicode(year), u'%s年' % year) for year in range(int(date.today().year), 1948, -1)]


class NewPreviousAchievementForm(FlaskForm):
    previous_achievement_type = SelectField(u'成绩类型', coerce=unicode, validators=[Required()])
    score = IntegerField(u'分数')
    remark = StringField(u'备注', validators=[Length(0, 128)])

    def __init__(self, *args, **kwargs):
        super(NewPreviousAchievementForm, self).__init__(*args, **kwargs)
        self.education_type.choices = [(u'', u'选择成绩类型')] + [(unicode(education_type.id), education_type.name) for education_type in EducationType.query.order_by(EducationType.id.asc()).all()]


class NewTOEFLTestScoreForm(FlaskForm):
    toefl_total = SelectField(u'TOEFL', coerce=unicode, validators=[Required()])
    toefl_reading = SelectField(u'Reading', coerce=unicode)
    toefl_listening = SelectField(u'Listening', coerce=unicode)
    toefl_speaking = SelectField(u'Speaking', coerce=unicode)
    toefl_writing = SelectField(u'Writing', coerce=unicode)

    def __init__(self, *args, **kwargs):
        super(NewTOEFLTestScoreForm, self).__init__(*args, **kwargs)
        self.toefl_total.choices = [(u'', u'选择TOEFL总分')] + [(unicode(toefl_total_score.id), toefl_total_score.name) for toefl_total_score in TOEFLTotalScore.query.order_by(TOEFLTotalScore.value.desc()).all()]
        self.toefl_reading.choices = [(u'', u'选择TOEFL阅读分数')] + [(unicode(toefl_reading_score.id), toefl_reading_score.name) for toefl_reading_score in TOEFLReadingScore.query.order_by(TOEFLReadingScore.value.desc()).all()]
        self.toefl_listening.choices = [(u'', u'选择TOEFL听力分数')] + [(unicode(toefl_reading_score.id), toefl_reading_score.name) for toefl_reading_score in TOEFLListeningScore.query.order_by(TOEFLListeningScore.value.desc()).all()]
        self.toefl_speaking.choices = [(u'', u'选择TOEFL口语分数')] + [(unicode(toefl_speaking_score.id), toefl_speaking_score.name) for toefl_speaking_score in TOEFLSpeakingScore.query.order_by(TOEFLSpeakingScore.value.desc()).all()]
        self.toefl_writing.choices = [(u'', u'选择TOEFL写作分数')] + [(unicode(toefl_writing_score.id), toefl_writing_score.name) for toefl_writing_score in TOEFLWritingScore.query.order_by(TOEFLWritingScore.value.desc()).all()]


class NewAdminForm(FlaskForm):
    name = StringField(u'姓名', validators=[Required(), Length(1, 64)])
    id_number = StringField(u'身份证号', validators=[Required(), Length(1, 64)])
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    role = SelectField(u'用户组', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'新建管理用户')

    def __init__(self, creator, *args, **kwargs):
        super(NewAdminForm, self).__init__(*args, **kwargs)
        if creator.is_developer:
            self.role.choices = [(u'', u'选择用户组')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'志愿者', u'协管员', u'管理员', u'开发人员']]
        else:
            self.role.choices = [(u'', u'选择用户组')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'志愿者', u'协管员', u'管理员']]

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'%s已经被注册' % field.data)


class EditUserForm(FlaskForm):
    name = StringField(u'姓名', validators=[Required(), Length(1, 64)])
    role = SelectField(u'用户组', coerce=unicode)
    # vb_course = SelectField(u'VB班', coerce=int)
    # y_gre_course = SelectField(u'Y-GRE班', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, editor, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        if editor.is_developer:
            self.role.choices = [(u'', u'选择用户组')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all()]
        elif editor.is_administrator:
            self.role.choices = [(u'', u'选择用户组')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name not in [u'开发人员']]
        else:
            self.role.choices = [(u'', u'选择用户组')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'挂起', u'单VB', u'Y-GRE 普通', u'Y-GRE VBx2', u'Y-GRE A权限']]
        # self.vb_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.filter_by(show=True, deleted=False).order_by(Course.id.desc()).all() if course.type.name == u'VB']
        # self.y_gre_course.choices = [(0, u'无')] + [(course.id, course.name) for course in Course.query.filter_by(show=True, deleted=False).order_by(Course.id.desc()).all() if course.type.name == u'Y-GRE']


class DeleteUserForm(FlaskForm):
    submit = SubmitField(u'删除')


class RestoreUserForm(FlaskForm):
    role = SelectField(u'用户组', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'恢复')

    def __init__(self, restorer, *args, **kwargs):
        super(RestoreUserForm, self).__init__(*args, **kwargs)
        if restorer.is_developer:
            self.role.choices = [(u'', u'选择用户组')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all()]
        elif restorer.is_administrator:
            self.role.choices = [(u'', u'选择用户组')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name not in [u'开发人员']]
        else:
            self.role.choices = [(u'', u'选择用户组')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'挂起', u'单VB', u'Y-GRE 普通', u'Y-GRE VBx2', u'Y-GRE A权限']]


class FindUserForm(FlaskForm):
    name_or_email = StringField(u'用户姓名/邮箱', validators=[Required(), Length(1, 64)])
    submit = SubmitField(u'检索')


class NewCourseForm(FlaskForm):
    name = StringField(u'班级名称', validators=[Required(), Length(1, 64)])
    course_type = SelectField(u'班级类型', coerce=unicode, validators=[Required()])
    show = BooleanField(u'显示为可选')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewCourseForm, self).__init__(*args, **kwargs)
        self.course_type.choices = [(u'', u'选择班级类型')] + [(unicode(course_type.id), course_type.name) for course_type in CourseType.query.order_by(CourseType.id.asc()).all()]


class EditCourseForm(FlaskForm):
    name = StringField(u'班级名称', validators=[Required(), Length(1, 64)])
    course_type = SelectField(u'班级类型', coerce=unicode, validators=[Required()])
    show = BooleanField(u'显示为可选')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditCourseForm, self).__init__(*args, **kwargs)
        self.course_type.choices = [(u'', u'选择班级类型')] + [(unicode(course_type.id), course_type.name) for course_type in CourseType.query.order_by(CourseType.id.asc()).all()]


class DeleteCourseForm(FlaskForm):
    submit = SubmitField(u'删除')