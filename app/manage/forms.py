# -*- coding: utf-8 -*-

from datetime import date, time, timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, IntegerField, FloatField, SelectField, SelectMultipleField, SubmitField
from wtforms.validators import Required, NumberRange, Length, Email
from wtforms import ValidationError
from ..models import Permission, Role, User
from ..models import Relationship, PurposeType, ReferrerType, InvitationType, EducationType, PreviousAchievementType
from ..models import Period
from ..models import Lesson, Section
from ..models import Assignment, AssignmentScoreGrade
from ..models import Test, GREAWScore, TOEFLTest
from ..models import iPad, iPadCapacity, iPadState, Room
from ..models import Course, CourseType
from ..models import Announcement, AnnouncementType
from ..models import Product


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

class EditPunchLessonForm(FlaskForm):
    lesson = SelectField(u'课程进度', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'下一步')

    def __init__(self, *args, **kwargs):
        super(EditPunchLessonForm, self).__init__(*args, **kwargs)
        self.lesson.choices = [(u'', u'选择课程进度')] + [(unicode(lesson.id), lesson.alias) for lesson in Lesson.query.order_by(Lesson.id.asc()).all()]


class EditPunchSectionForm(FlaskForm):
    section = SelectField(u'视频进度', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'下一步')

    def __init__(self, lesson, *args, **kwargs):
        super(EditPunchSectionForm, self).__init__(*args, **kwargs)
        self.section.choices = [(u'', u'选择视频进度')] + [(unicode(section.id), section.alias) for section in Section.query.filter_by(lesson_id=lesson.id).order_by(Section.id.asc()).all()]


class BookingCodeForm(FlaskForm):
    booking_code = StringField(u'预约码', validators=[Required()])
    submit = SubmitField(u'下一步')


class RentiPadForm(FlaskForm):
    ipad = SelectField(u'可用iPad', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'下一步')

    def __init__(self, user, *args, **kwargs):
        super(RentiPadForm, self).__init__(*args, **kwargs)
        self.ipad.choices = [(u'', u'选择iPad')] + [(unicode(ipad.id), u'%s %s %s %s：%s' % (ipad.alias, ipad.capacity.name, ipad.state.name, ipad.room.name, reduce(lambda x, y: x + u'、' + y, [lesson.name for lesson in ipad.has_lessons]))) for ipad in user.fitted_ipads if ipad.state.name in [u'待机', u'候补']]


class RentalEmailForm(FlaskForm):
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    submit = SubmitField(u'下一步')


class ConfirmiPadForm(FlaskForm):
    serial = StringField(u'iPad序列号', validators=[Required()])
    battery_life = IntegerField(u'剩余电量', validators=[Required(), NumberRange(min=0, max=100)])
    root = BooleanField(u'引导式访问状态正常')
    submit = SubmitField(u'确认并提交')


class SelectLessonForm(FlaskForm):
    lesson = SelectField(u'课程', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'下一步')

    def __init__(self, *args, **kwargs):
        super(SelectLessonForm, self).__init__(*args, **kwargs)
        self.lesson.choices = [(u'', u'选择课程')] + [(unicode(lesson.id), lesson.alias) for lesson in Lesson.query.order_by(Lesson.id.asc()).all()]


class RentiPadByLessonForm(FlaskForm):
    ipad = SelectField(u'可用iPad', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'下一步')

    def __init__(self, lesson, *args, **kwargs):
        super(RentiPadByLessonForm, self).__init__(*args, **kwargs)
        self.ipad.choices = [(u'', u'选择iPad')] + [(unicode(item.ipad_id), u'%s %s %s %s：%s' % (item.ipad.alias, item.ipad.capacity.name, item.ipad.state.name, item.ipad.room.name, reduce(lambda x, y: x + u'、' + y, [lesson.name for lesson in item.ipad.has_lessons]))) for item in lesson.occupied_ipads if (item.ipad.state.name in [u'待机', u'候补']) and (item.ipad.deleted == False)]


class iPadSerialForm(FlaskForm):
    serial = StringField(u'iPad序列号', validators=[Required()])
    root = BooleanField(u'引导式访问状态正常')
    battery = BooleanField(u'电量充足')
    submit = SubmitField(u'下一步')


class PunchLessonForm(FlaskForm):
    lesson = SelectField(u'课程进度', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'下一步')

    def __init__(self, user, *args, **kwargs):
        super(PunchLessonForm, self).__init__(*args, **kwargs)
        self.lesson.choices = [(u'', u'选择课程进度')] + [(unicode(lesson.id), lesson.alias) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.id >= user.last_punch.section.lesson_id]


class PunchSectionForm(FlaskForm):
    section = SelectField(u'视频进度', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'下一步')

    def __init__(self, user, lesson, *args, **kwargs):
        super(PunchSectionForm, self).__init__(*args, **kwargs)
        self.section.choices = [(u'', u'选择视频进度')] + [(unicode(section.id), section.alias) for section in Section.query.filter_by(lesson_id=lesson.id).order_by(Section.id.asc()).all() if section.id >= user.last_punch.section_id]


class ConfirmPunchForm(FlaskForm):
    submit = SubmitField(u'确认并提交')


class EditSectionHourForm(FlaskForm):
    hour = StringField('学习时间', validators=[Required()])
    submit = SubmitField(u'提交')


class NewAssignmentScoreForm(FlaskForm):
    email = StringField(u'用户（邮箱）', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    assignment = SelectField(u'作业', coerce=unicode, validators=[Required()])
    grade = SelectField(u'成绩', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewAssignmentScoreForm, self).__init__(*args, **kwargs)
        self.assignment.choices = [(u'', u'选择作业')] + [(unicode(assignment.id), assignment.alias) for assignment in Assignment.query.order_by(Assignment.id.asc()).all()]
        self.grade.choices = [(u'', u'选择成绩')] + [(unicode(grade.id), grade.name) for grade in AssignmentScoreGrade.query.order_by(AssignmentScoreGrade.id.asc()).all()]


class EditAssignmentScoreForm(FlaskForm):
    assignment = SelectField(u'作业', coerce=unicode, validators=[Required()])
    grade = SelectField(u'成绩', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditAssignmentScoreForm, self).__init__(*args, **kwargs)
        self.assignment.choices = [(u'', u'选择作业')] + [(unicode(assignment.id), assignment.alias) for assignment in Assignment.query.order_by(Assignment.id.asc()).all()]
        self.grade.choices = [(u'', u'选择成绩')] + [(unicode(grade.id), grade.name) for grade in AssignmentScoreGrade.query.order_by(AssignmentScoreGrade.id.asc()).all()]


class NewVBTestScoreForm(FlaskForm):
    email = StringField(u'用户（邮箱）', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    test = SelectField(u'考试', coerce=unicode, validators=[Required()])
    score = StringField(u'成绩', validators=[Required()])
    retrieved = BooleanField(u'已回收试卷')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewVBTestScoreForm, self).__init__(*args, **kwargs)
        self.test.choices = [(u'', u'选择VB考试')] + [(unicode(test.id), test.alias2) for test in Test.query.order_by(Test.id.asc()).all() if test.lesson.type.name == u'VB']


class EditVBTestScoreForm(FlaskForm):
    test = SelectField(u'考试', coerce=unicode, validators=[Required()])
    score = StringField(u'成绩', validators=[Required()])
    retrieved = BooleanField(u'已回收试卷')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditVBTestScoreForm, self).__init__(*args, **kwargs)
        self.test.choices = [(u'', u'选择VB考试')] + [(unicode(test.id), test.alias2) for test in Test.query.order_by(Test.id.asc()).all() if test.lesson.type.name == u'VB']


class NewYGRETestScoreForm(FlaskForm):
    email = StringField(u'用户（邮箱）', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    test = SelectField(u'考试', coerce=unicode, validators=[Required()])
    v_score = StringField(u'Verbal Reasoning', validators=[Required()])
    q_score = StringField(u'Quantitative Reasoning')
    aw_score = SelectField(u'Analytical Writing', coerce=unicode)
    retrieved = BooleanField(u'已回收试卷')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewYGRETestScoreForm, self).__init__(*args, **kwargs)
        self.test.choices = [(u'', u'选择Y-GRE考试')] + [(unicode(test.id), test.alias2) for test in Test.query.order_by(Test.id.asc()).all() if test.lesson.type.name == u'Y-GRE']
        self.aw_score.choices = [(u'', u'选择AW成绩')] + [(unicode(aw_score.id), aw_score.name) for aw_score in GREAWScore.query.order_by(GREAWScore.id.desc()).all()]


class EditYGRETestScoreForm(FlaskForm):
    test = SelectField(u'考试', coerce=unicode, validators=[Required()])
    v_score = StringField(u'Verbal Reasoning', validators=[Required()])
    q_score = StringField(u'Quantitative Reasoning')
    aw_score = SelectField(u'Analytical Writing', coerce=unicode)
    retrieved = BooleanField(u'已回收试卷')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditYGRETestScoreForm, self).__init__(*args, **kwargs)
        self.test.choices = [(u'', u'选择Y-GRE考试')] + [(unicode(test.id), test.alias2) for test in Test.query.order_by(Test.id.asc()).all() if test.lesson.type.name == u'Y-GRE']
        self.aw_score.choices = [(u'', u'选择AW成绩')] + [(unicode(aw_score.id), aw_score.name) for aw_score in GREAWScore.query.order_by(GREAWScore.id.desc()).all()]


class NewUserForm(FlaskForm):
    # basic
    name = StringField(u'姓名', validators=[Required(), Length(1, 64)])
    id_number = StringField(u'身份证号', validators=[Required(), Length(1, 64)])
    # contact
    email = StringField(u'电子邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    mobile = StringField(u'移动电话', validators=[Required(), Length(1, 64)])
    address = StringField(u'联系地址', validators=[Required(), Length(1, 64)])
    qq = StringField(u'QQ', validators=[Length(0, 64)])
    wechat = StringField(u'微信', validators=[Length(0, 64)])
    # emergency contact
    emergency_contact_name = StringField(u'姓名', validators=[Required(), Length(1, 64)])
    emergency_contact_relationship = SelectField(u'关系', coerce=unicode, validators=[Required()])
    emergency_contact_mobile = StringField(u'联系方式', validators=[Required(), Length(1, 64)])
    # high school
    high_school = StringField(u'毕业高中', validators=[Length(0, 64)])
    high_school_year = SelectField(u'入学年份', coerce=unicode)
    # bachelor
    bachelor_school = StringField(u'本科学校', validators=[Length(0, 64)])
    bachelor_major = StringField(u'院系（专业）', validators=[Length(0, 64)])
    bachelor_gpa = StringField(u'GPA', validators=[Length(0, 64)])
    bachelor_full_gpa = StringField(u'GPA满分', validators=[Length(0, 64)])
    bachelor_year = SelectField(u'入学年份', coerce=unicode)
    # master
    master_school = StringField(u'研究生学校（硕士）', validators=[Length(0, 64)])
    master_major = StringField(u'院系（专业）', validators=[Length(0, 64)])
    master_gpa = StringField(u'GPA', validators=[Length(0, 64)])
    master_full_gpa = StringField(u'GPA满分', validators=[Length(0, 64)])
    master_year = SelectField(u'入学年份', coerce=unicode)
    # doctor
    doctor_school = StringField(u'研究生学校（博士）', validators=[Length(0, 64)])
    doctor_major = StringField(u'院系（专业）', validators=[Length(0, 64)])
    doctor_gpa = StringField(u'GPA', validators=[Length(0, 64)])
    doctor_full_gpa = StringField(u'GPA满分', validators=[Length(0, 64)])
    doctor_year = SelectField(u'入学年份', coerce=unicode)
    # job 1
    employer_1 = StringField(u'工作单位', validators=[Length(0, 64)])
    position_1 = StringField(u'职务', validators=[Length(0, 64)])
    job_year_1 = SelectField(u'入职年份', coerce=unicode)
    # job 2
    employer_2 = StringField(u'工作单位', validators=[Length(0, 64)])
    position_2 = StringField(u'职务', validators=[Length(0, 64)])
    job_year_2 = SelectField(u'入职年份', coerce=unicode)
    # scores
    cee_total = StringField(u'高考总分', validators=[Length(0, 64)])
    cee_math = StringField(u'高考数学', validators=[Length(0, 64)])
    cee_english = StringField(u'高考英语', validators=[Length(0, 64)])
    cet_4 = StringField(u'CET-4', validators=[Length(0, 64)])
    cet_6 = StringField(u'CET-6', validators=[Length(0, 64)])
    tem_4 = StringField(u'TEM-4', validators=[Length(0, 64)])
    tem_8 = StringField(u'TEM-8', validators=[Length(0, 64)])
    toefl_total = StringField(u'TOEFL', validators=[Length(0, 64)])
    toefl_reading = StringField(u'Reading', validators=[Length(0, 64)])
    toefl_listening = StringField(u'Listening', validators=[Length(0, 64)])
    toefl_speaking = StringField(u'Speaking', validators=[Length(0, 64)])
    toefl_writing = StringField(u'Writing', validators=[Length(0, 64)])
    competition = StringField(u'竞赛成绩', validators=[Length(0, 128)])
    other_score = StringField(u'其它成绩', validators=[Length(0, 128)])
    # registration
    purposes = SelectMultipleField(u'研修目的', coerce=unicode)
    other_purpose = StringField(u'其它研修目的', validators=[Length(0, 64)])
    application_aim = StringField(u'申请方向', validators=[Length(0, 64)])
    referrers = SelectMultipleField(u'了解渠道', coerce=unicode)
    other_referrer = StringField(u'其它了解渠道', validators=[Length(0, 64)])
    inviter_email = StringField(u'同学推荐（邮箱）', validators=[Length(0, 64)])
    products = SelectMultipleField(u'研修产品', coerce=unicode, validators=[Required()])
    role = SelectField(u'用户权限', coerce=unicode, validators=[Required()])
    vb_course = SelectField(u'VB班', coerce=unicode, validators=[Required()])
    y_gre_course = SelectField(u'Y-GRE班', coerce=unicode, validators=[Required()])
    # submit
    submit = SubmitField(u'下一步')

    def __init__(self, *args, **kwargs):
        super(NewUserForm, self).__init__(*args, **kwargs)
        self.emergency_contact_relationship.choices = [(u'', u'选择关系')] +  [(unicode(relationship.id), relationship.name) for relationship in Relationship.query.order_by(Relationship.id.asc()).all()]
        self.high_school_year.choices = [(u'', u'入学年份')] + [(unicode(year), u'%s年' % year) for year in range(int(date.today().year), 1948, -1)]
        self.bachelor_year.choices = [(u'', u'入学年份')] + [(unicode(year), u'%s年' % year) for year in range(int(date.today().year), 1948, -1)]
        self.master_year.choices = [(u'', u'入学年份')] + [(unicode(year), u'%s年' % year) for year in range(int(date.today().year), 1948, -1)]
        self.doctor_year.choices = [(u'', u'入学年份')] + [(unicode(year), u'%s年' % year) for year in range(int(date.today().year), 1948, -1)]
        self.job_year_1.choices = [(u'', u'入职年份')] + [(unicode(year), u'%s年' % year) for year in range(int(date.today().year), 1948, -1)]
        self.job_year_2.choices = [(u'', u'入职年份')] + [(unicode(year), u'%s年' % year) for year in range(int(date.today().year), 1948, -1)]
        self.purposes.choices = [(u'', u'选择研修目的')] + [(unicode(purpose_type.id), purpose_type.name) for purpose_type in PurposeType.query.order_by(PurposeType.id.asc()).all() if purpose_type.name != u'其它']
        self.referrers.choices = [(u'', u'选择了解渠道')] + [(unicode(referrer_type.id), referrer_type.name) for referrer_type in ReferrerType.query.order_by(ReferrerType.id.asc()).all() if referrer_type.name != u'其它']
        self.products.choices = [(u'', u'选择研修产品')] + [(unicode(product.id), u'%s（%g元）' % (product.name, product.price)) for product in Product.query.filter_by(available=True, deleted=False).order_by(Product.id.asc()).all() if product.name not in [u'团报优惠', u'按月延长有效期', u'一次性延长2年有效期']]
        self.role.choices = [(u'', u'选择用户权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'单VB', u'Y-GRE 普通', u'Y-GRE VB×2', u'Y-GRE A权限']]
        self.vb_course.choices = [(u'', u'选择VB班')] + [(u'0', u'无')] + [(unicode(course.id), course.name) for course in Course.query.filter_by(show=True, deleted=False).order_by(Course.id.desc()).all() if course.type.name == u'VB']
        self.y_gre_course.choices = [(u'', u'选择Y-GRE班')] +  [(u'0', u'无')] + [(unicode(course.id), course.name) for course in Course.query.filter_by(show=True, deleted=False).order_by(Course.id.desc()).all() if course.type.name == u'Y-GRE']

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'%s已经被注册' % field.data)

    def validate_inviter_email(self, field):
        if field.data and User.query.filter_by(email=field.data, created=True, activated=True, deleted=False).first() is None:
            raise ValidationError(u'推荐人邮箱不存在：%s' % field.data)


class ConfirmUserForm(FlaskForm):
    worked_in_same_field = BooleanField(u'（曾）在培训/留学机构任职')
    deformity = BooleanField(u'有严重心理或身体疾病')
    disclaimer = BooleanField(u'确认无偿授权“云英语”使用申请者姓名、肖像、GRE成绩单以及其它必要信息用于宣传', validators=[Required()])
    receptionist_email = StringField(u'接待人（邮箱）', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    submit = SubmitField(u'确认并新建学生用户')

    def validate_receptionist_email(self, field):
        if field.data and User.query.filter_by(email=field.data, created=True, activated=True, deleted=False).first() is None:
            raise ValidationError(u'接待人邮箱不存在：%s' % field.data)


class NewEducationRecordForm(FlaskForm):
    education_type = SelectField(u'学历类型', coerce=unicode, validators=[Required()])
    school = StringField(u'学校', validators=[Required(), Length(1, 64)])
    major = StringField(u'院系（专业）', validators=[Length(0, 64)])
    gpa = StringField(u'GPA', validators=[Length(0, 64)])
    full_gpa = StringField(u'GPA满分', validators=[Length(0, 64)])
    year = SelectField(u'入学年份', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'添加')

    def __init__(self, *args, **kwargs):
        super(NewEducationRecordForm, self).__init__(*args, **kwargs)
        self.education_type.choices = [(u'', u'选择学历类型')] + [(unicode(education_type.id), education_type.name) for education_type in EducationType.query.order_by(EducationType.id.asc()).all()]
        self.year.choices = [(u'', u'选择入学年份')] + [(unicode(year), u'%s年' % year) for year in range(int(date.today().year), 1948, -1)]


class NewEmploymentRecordForm(FlaskForm):
    employer = StringField(u'工作单位', validators=[Required(), Length(1, 64)])
    position = StringField(u'职务', validators=[Required(), Length(1, 64)])
    year = SelectField(u'入职年份', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'添加')

    def __init__(self, *args, **kwargs):
        super(NewEmploymentRecordForm, self).__init__(*args, **kwargs)
        self.year.choices = [(u'', u'选择入职年份')] + [(unicode(year), u'%s年' % year) for year in range(int(date.today().year), 1948, -1)]


class NewPreviousAchievementForm(FlaskForm):
    previous_achievement_type = SelectField(u'成绩类型', coerce=unicode, validators=[Required()])
    achievement = StringField(u'成绩', validators=[Length(0, 128)])
    submit = SubmitField(u'添加')

    def __init__(self, *args, **kwargs):
        super(NewPreviousAchievementForm, self).__init__(*args, **kwargs)
        self.previous_achievement_type.choices = [(u'', u'选择成绩类型')] + [(unicode(previous_achievement_type.id), previous_achievement_type.name) for previous_achievement_type in PreviousAchievementType.query.order_by(PreviousAchievementType.id.asc()).all()]


class NewTOEFLTestScoreForm(FlaskForm):
    test = SelectField(u'TOEFL考试', coerce=unicode, validators=[Required()])
    total = IntegerField(u'TOEFL', validators=[Required(), NumberRange(min=0, max=120)])
    reading = IntegerField(u'Reading', validators=[Required(), NumberRange(min=0, max=30)])
    listening = IntegerField(u'Listening', validators=[Required(), NumberRange(min=0, max=30)])
    speaking = IntegerField(u'Speaking', validators=[Required(), NumberRange(min=0, max=30)])
    writing = IntegerField(u'Writing', validators=[Required(), NumberRange(min=0, max=30)])
    submit = SubmitField(u'添加')

    def __init__(self, *args, **kwargs):
        super(NewTOEFLTestScoreForm, self).__init__(*args, **kwargs)
        self.test.choices = [(u'', u'选择TOEFL考试')] + [(unicode(toefl_test.id), toefl_test.name) for toefl_test in TOEFLTest.query.order_by(TOEFLTest.id.asc()).all()]


class NewAdminForm(FlaskForm):
    name = StringField(u'姓名', validators=[Required(), Length(1, 64)])
    id_number = StringField(u'身份证号', validators=[Required(), Length(1, 64)])
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    role = SelectField(u'用户权限', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'新建管理用户')

    def __init__(self, creator, *args, **kwargs):
        super(NewAdminForm, self).__init__(*args, **kwargs)
        if creator.is_developer:
            self.role.choices = [(u'', u'选择权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'志愿者', u'协管员', u'管理员', u'开发人员']]
        else:
            self.role.choices = [(u'', u'选择权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'志愿者', u'协管员', u'管理员']]


class EditNameForm(FlaskForm):
    name = StringField(u'姓名', validators=[Required(), Length(1, 64)])
    submit = SubmitField(u'更新')


class EditIDNumberForm(FlaskForm):
    id_number = StringField(u'身份证号', validators=[Required(), Length(1, 64)])
    submit = SubmitField(u'更新')


class EditEmailForm(FlaskForm):
    email = StringField(u'电子邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    submit = SubmitField(u'更新')


class EditMobileForm(FlaskForm):
    mobile = StringField(u'移动电话', validators=[Required(), Length(1, 64)])
    submit = SubmitField(u'更新')


class EditAddressForm(FlaskForm):
    address = StringField(u'联系地址', validators=[Required(), Length(1, 64)])
    submit = SubmitField(u'更新')


class EditQQForm(FlaskForm):
    qq = StringField(u'QQ', validators=[Length(0, 64)])
    submit = SubmitField(u'更新')


class EditWeChatForm(FlaskForm):
    wechat = StringField(u'微信', validators=[Length(0, 64)])
    submit = SubmitField(u'更新')


class EditEmergencyContactNameForm(FlaskForm):
    emergency_contact_name = StringField(u'紧急联系人姓名', validators=[Required(), Length(1, 64)])
    submit = SubmitField(u'更新')


class EditEmergencyContactRelationshipForm(FlaskForm):
    emergency_contact_relationship = SelectField(u'紧急联系人关系', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'更新')

    def __init__(self, *args, **kwargs):
        super(EditEmergencyContactRelationshipForm, self).__init__(*args, **kwargs)
        self.emergency_contact_relationship.choices = [(u'', u'选择紧急联系人关系')] +  [(unicode(relationship.id), relationship.name) for relationship in Relationship.query.order_by(Relationship.id.asc()).all()]


class EditEmergencyContactMobileForm(FlaskForm):
    emergency_contact_mobile = StringField(u'紧急联系人联系方式', validators=[Required(), Length(1, 64)])
    submit = SubmitField(u'更新')


class EditPurposeForm(FlaskForm):
    purposes = SelectMultipleField(u'研修目的', coerce=unicode)
    other_purpose = StringField(u'其它研修目的', validators=[Length(0, 64)])
    submit = SubmitField(u'更新')

    def __init__(self, *args, **kwargs):
        super(EditPurposeForm, self).__init__(*args, **kwargs)
        self.purposes.choices = [(u'', u'选择研修目的')] + [(unicode(purpose_type.id), purpose_type.name) for purpose_type in PurposeType.query.order_by(PurposeType.id.asc()).all() if purpose_type.name != u'其它']


class EditApplicationAimForm(FlaskForm):
    application_aim = StringField(u'申请方向', validators=[Length(0, 64)])
    submit = SubmitField(u'更新')


class EditReferrerForm(FlaskForm):
    referrers = SelectMultipleField(u'了解渠道', coerce=unicode)
    other_referrer = StringField(u'其它了解渠道', validators=[Length(0, 64)])
    submit = SubmitField(u'更新')

    def __init__(self, *args, **kwargs):
        super(EditReferrerForm, self).__init__(*args, **kwargs)
        self.referrers.choices = [(u'', u'选择了解渠道')] + [(unicode(referrer_type.id), referrer_type.name) for referrer_type in ReferrerType.query.order_by(ReferrerType.id.asc()).all() if referrer_type.name != u'其它']


class NewInviterForm(FlaskForm):
    inviter_email = StringField(u'推荐人（邮箱）', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    invitation_type = SelectField(u'推荐类型', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'添加')

    def __init__(self, *args, **kwargs):
        super(NewInviterForm, self).__init__(*args, **kwargs)
        self.invitation_type.choices = [(u'', u'选择推荐类型')] + [(unicode(invitation_type.id), invitation_type.name) for invitation_type in InvitationType.query.order_by(InvitationType.id.asc()).all()]


class NewPurchaseForm(FlaskForm):
    product = SelectField(u'研修产品', coerce=unicode, validators=[Required()])
    quantity = IntegerField(u'数量', validators=[Required(), NumberRange(min=1)])
    submit = SubmitField(u'添加')

    def __init__(self, *args, **kwargs):
        super(NewPurchaseForm, self).__init__(*args, **kwargs)
        self.product.choices = [(u'', u'选择研修产品')] + [(unicode(product.id), product.alias) for product in Product.query.filter_by(available=True, deleted=False).order_by(Product.id.asc()).all() if product.name not in [u'团报优惠', u'按月延长有效期', u'一次性延长2年有效期']]


class EditStudentRoleForm(FlaskForm):
    role = SelectField(u'用户权限', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'更新')

    def __init__(self, *args, **kwargs):
        super(EditStudentRoleForm, self).__init__(*args, **kwargs)
        self.role.choices = [(u'', u'选择用户权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'单VB', u'Y-GRE 普通', u'Y-GRE VB×2', u'Y-GRE A权限']]


class EditUserRoleForm(FlaskForm):
    role = SelectField(u'用户权限', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'更新')

    def __init__(self, editor, is_self=False, *args, **kwargs):
        super(EditUserRoleForm, self).__init__(*args, **kwargs)
        if editor.is_developer:
            self.role.choices = [(u'', u'选择用户权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all()]
        elif editor.is_administrator:
            self.role.choices = [(u'', u'选择用户权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name not in [u'开发人员']]
        elif editor.is_moderator and is_self:
            self.role.choices = [(u'', u'选择用户权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name not in [u'管理员', u'开发人员']]
        else:
            self.role.choices = [(u'', u'选择用户权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'挂起', u'单VB', u'Y-GRE 普通', u'Y-GRE VB×2', u'Y-GRE A权限', u'志愿者']]


class EditVBCourseForm(FlaskForm):
    vb_course = SelectField(u'VB班', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'更新')

    def __init__(self, *args, **kwargs):
        super(EditVBCourseForm, self).__init__(*args, **kwargs)
        self.vb_course.choices = [(u'', u'选择VB班')] + [(u'0', u'无')] + [(unicode(course.id), course.name) for course in Course.query.filter_by(show=True, deleted=False).order_by(Course.id.desc()).all() if course.type.name == u'VB']


class EditYGRECourseForm(FlaskForm):
    y_gre_course = SelectField(u'Y-GRE班', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'更新')

    def __init__(self, *args, **kwargs):
        super(EditYGRECourseForm, self).__init__(*args, **kwargs)
        self.y_gre_course.choices = [(u'', u'选择Y-GRE班')] +  [(u'0', u'无')] + [(unicode(course.id), course.name) for course in Course.query.filter_by(show=True, deleted=False).order_by(Course.id.desc()).all() if course.type.name == u'Y-GRE']


class EditWorkInSameFieldForm(FlaskForm):
    worked_in_same_field = BooleanField(u'（曾）在培训/留学机构任职')
    submit = SubmitField(u'更新')


class EditDeformityForm(FlaskForm):
    deformity = BooleanField(u'有严重心理或身体疾病')
    submit = SubmitField(u'更新')


class RestoreUserForm(FlaskForm):
    email = StringField(u'电子邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    role = SelectField(u'用户权限', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'恢复')

    def __init__(self, restorer, *args, **kwargs):
        super(RestoreUserForm, self).__init__(*args, **kwargs)
        if restorer.is_developer:
            self.role.choices = [(u'', u'选择用户权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all()]
        elif restorer.is_administrator:
            self.role.choices = [(u'', u'选择用户权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name not in [u'开发人员']]
        else:
            self.role.choices = [(u'', u'选择用户权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'挂起', u'单VB', u'Y-GRE 普通', u'Y-GRE VB×2', u'Y-GRE A权限']]

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'%s已经被注册' % field.data)


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


class NewGroupForm(FlaskForm):
    organizer_email = StringField(u'团报发起人（邮箱）', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    submit = SubmitField(u'提交')


class NewGroupMemberForm(FlaskForm):
    member_email = StringField(u'团报成员（邮箱）', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    submit = SubmitField(u'提交')

    def __init__(self, organizer, *args, **kwargs):
        super(NewGroupMemberForm, self).__init__(*args, **kwargs)
        self.organizer = organizer

    def validate_member_email(self, field):
        if field.data:
            user = User.query.filter_by(email=field.data, created=True, activated=True, deleted=False).first()
            if user is None:
                raise ValidationError(u'团报成员邮箱不存在：%s' % field.data)
            elif user.organized_groups.count():
                raise ValidationError(u'%s已经发起过团报' % (user.name_alias))
            elif user.registered_groups.count():
                raise ValidationError(u'%s已经参加过%s发起的团报' % (user.name_alias, user.registered_groups.first().organizer.name_alias))
            elif self.organizer.organized_groups.count() > 5:
                raise ValidationError(u'%s发起的团报人数已达到上限（5人）' % (self.organizer.name_alias))


class NewiPadForm(FlaskForm):
    alias = StringField(u'编号', validators=[Required(), Length(1, 64)])
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
            raise ValidationError(u'序列号为“%s”的iPad已存在' % field.data)


class EditiPadForm(FlaskForm):
    alias = StringField(u'编号', validators=[Required(), Length(1, 64)])
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
            raise ValidationError(u'序列号为“%s”的iPad已存在' % field.data)


class FilteriPadForm(FlaskForm):
    vb_lessons = SelectMultipleField(u'VB内容', coerce=unicode)
    y_gre_lessons = SelectMultipleField(u'Y-GRE内容', coerce=unicode)
    submit = SubmitField(u'筛选')

    def __init__(self, *args, **kwargs):
        super(FilteriPadForm, self).__init__(*args, **kwargs)
        self.vb_lessons.choices = [(u'', u'选择VB内容')] + [(unicode(lesson.id), lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'VB']
        self.y_gre_lessons.choices = [(u'', u'选择Y-GRE内容')] + [(unicode(lesson.id), lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.type.name == u'Y-GRE']


class NewAnnouncementForm(FlaskForm):
    title = StringField(u'通知标题', validators=[Required(), Length(1, 64)])
    body = TextAreaField(u'通知内容', validators=[Required()])
    announcement_type = SelectField(u'通知类型', coerce=unicode, validators=[Required()])
    show = BooleanField(u'立即发布')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewAnnouncementForm, self).__init__(*args, **kwargs)
        self.announcement_type.choices = [(u'', u'选择通知类型')] + [(unicode(announcement_type.id), announcement_type.name) for announcement_type in AnnouncementType.query.order_by(AnnouncementType.id.asc()).all()]


class EditAnnouncementForm(FlaskForm):
    title = StringField(u'通知标题', validators=[Required(), Length(1, 64)])
    body = TextAreaField(u'通知内容', validators=[Required()])
    announcement_type = SelectField(u'通知类型', coerce=unicode, validators=[Required()])
    show = BooleanField(u'立即发布')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditAnnouncementForm, self).__init__(*args, **kwargs)
        self.announcement_type.choices = [(u'', u'选择通知类型')] + [(unicode(announcement_type.id), announcement_type.name) for announcement_type in AnnouncementType.query.order_by(AnnouncementType.id.asc()).all()]


class NewProductForm(FlaskForm):
    name = StringField(u'产品名称', validators=[Required(), Length(1, 64)])
    price = StringField(u'单价', validators=[Required()])
    available = BooleanField(u'显示为可选')
    submit = SubmitField(u'提交')


class EditProductForm(FlaskForm):
    name = StringField(u'产品名称', validators=[Required(), Length(1, 64)])
    price = StringField(u'单价', validators=[Required()])
    available = BooleanField(u'显示为可选')
    submit = SubmitField(u'提交')


class NewRoleForm(FlaskForm):
    name = StringField(u'角色名称', validators=[Required(), Length(1, 64)])
    booking_permissions = SelectMultipleField(u'预约权限', coerce=unicode)
    manage_permissions = SelectMultipleField(u'管理权限', coerce=unicode)
    is_developer = BooleanField(u'开发权限')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewRoleForm, self).__init__(*args, **kwargs)
        self.booking_permissions.choices = [(u'', u'选择预约权限')] + [(unicode(permission.id), permission.name) for permission in Permission.query.order_by(Permission.id.asc()).all() if permission.name[:2] == u'预约']
        self.manage_permissions.choices = [(u'', u'选择管理权限')] + [(unicode(permission.id), permission.name) for permission in Permission.query.order_by(Permission.id.asc()).all() if permission.name[:2] == u'管理']


class EditRoleForm(FlaskForm):
    name = StringField(u'角色名称', validators=[Required(), Length(1, 64)])
    booking_permissions = SelectMultipleField(u'预约权限', coerce=unicode)
    manage_permissions = SelectMultipleField(u'管理权限', coerce=unicode)
    is_developer = BooleanField(u'开发权限')
    submit = SubmitField(u'提交')

    def __init__(self, role, *args, **kwargs):
        super(EditRoleForm, self).__init__(*args, **kwargs)
        self.booking_permissions.choices = [(u'', u'选择预约权限')] + [(unicode(permission.id), permission.name) for permission in Permission.query.order_by(Permission.id.asc()).all() if permission.name[:2] == u'预约']
        self.manage_permissions.choices = [(u'', u'选择管理权限')] + [(unicode(permission.id), permission.name) for permission in Permission.query.order_by(Permission.id.asc()).all() if permission.name[:2] == u'管理']
        self.role = role

    def validate_name(self, field):
        if field.data != self.role.name and Role.query.filter_by(name=field.data).first():
            raise ValidationError(u'“%s”角色已存在' % field.data)


class NewPermissionForm(FlaskForm):
    name = StringField(u'权限名称', validators=[Required(), Length(1, 64)])
    submit = SubmitField(u'提交')


class EditPermissionForm(FlaskForm):
    name = StringField(u'权限名称', validators=[Required(), Length(1, 64)])
    submit = SubmitField(u'提交')

    def __init__(self, permission, *args, **kwargs):
        super(EditPermissionForm, self).__init__(*args, **kwargs)
        self.permission = permission

    def validate_name(self, field):
        if field.data != self.permission.name and Permission.query.filter_by(name=field.data).first():
            raise ValidationError(u'“%s”权限已存在' % field.data)