# -*- coding: utf-8 -*-

from datetime import date, time, timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, IntegerField, FloatField, DateField, SelectField, SelectMultipleField, SubmitField
from wtforms.validators import Required, NumberRange, Length, Email, Optional
from wtforms import ValidationError
from ..models import Color
from ..models import Permission, Role, User, Tag
from ..models import IDType, Gender
from ..models import Relationship, PurposeType, ReferrerType, InvitationType, EducationType, ScoreType
from ..models import Period
from ..models import Lesson, Section
from ..models import Assignment, AssignmentScoreGrade
from ..models import Test, GREAWScore, ScoreLabel
from ..models import iPad, iPadCapacity, iPadState, Room
from ..models import Course, CourseType
from ..models import NotaBene
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


class SearchForm(FlaskForm):
    keyword = StringField(u'关键字')
    submit = SubmitField(u'搜索')


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

    def __init__(self, user, *args, **kwargs):
        super(EditPunchLessonForm, self).__init__(*args, **kwargs)
        if user.can_access_advanced_vb:
            self.lesson.choices = [(u'', u'选择课程进度')] + [(unicode(lesson.id), lesson.alias) for lesson in Lesson.query.filter(Lesson.order >= 1).order_by(Lesson.id.asc()).all()]
        else:
            self.lesson.choices = [(u'', u'选择课程进度')] + [(unicode(lesson.id), lesson.alias) for lesson in Lesson.query.filter(Lesson.order >= 1).filter(Lesson.advanced == False).order_by(Lesson.id.asc()).all()]


class EditPunchSectionForm(FlaskForm):
    section = SelectField(u'视频进度', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'下一步')

    def __init__(self, lesson, *args, **kwargs):
        super(EditPunchSectionForm, self).__init__(*args, **kwargs)
        self.section.choices = [(u'', u'选择视频进度')] + [(unicode(section.id), section.alias2) for section in Section.query.filter_by(lesson_id=lesson.id).order_by(Section.id.asc()).all()]


class BookingTokenForm(FlaskForm):
    token = StringField(u'预约码', validators=[Required()])
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


class PunchSectionForm(FlaskForm):
    section = SelectField(u'研修进度', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'下一步')

    def __init__(self, user, *args, **kwargs):
        super(PunchSectionForm, self).__init__(*args, **kwargs)
        self.section.choices = [(u'', u'选择研修进度')] + [(unicode(section.id), section.alias2) for section in user.next_punch]


class ConfirmPunchForm(FlaskForm):
    submit = SubmitField(u'确认并提交')


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
        self.test.choices = [(u'', u'选择VB考试')] + [(unicode(test.id), test.alias) for test in Test.query.order_by(Test.id.asc()).all() if test.lesson.type.name == u'VB']


class EditVBTestScoreForm(FlaskForm):
    test = SelectField(u'考试', coerce=unicode, validators=[Required()])
    score = StringField(u'成绩', validators=[Required()])
    retrieved = BooleanField(u'已回收试卷')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditVBTestScoreForm, self).__init__(*args, **kwargs)
        self.test.choices = [(u'', u'选择VB考试')] + [(unicode(test.id), test.alias) for test in Test.query.order_by(Test.id.asc()).all() if test.lesson.type.name == u'VB']


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
        self.test.choices = [(u'', u'选择Y-GRE考试')] + [(unicode(test.id), test.alias) for test in Test.query.order_by(Test.id.asc()).all() if test.lesson.type.name == u'Y-GRE']
        self.aw_score.choices = [(u'', u'选择AW成绩')] + [(unicode(aw_score.id), aw_score.name) for aw_score in GREAWScore.query.order_by(GREAWScore.id.desc()).all()]


class EditYGRETestScoreForm(FlaskForm):
    test = SelectField(u'考试', coerce=unicode, validators=[Required()])
    v_score = IntegerField(u'Verbal Reasoning', validators=[Required(), NumberRange(min=130, max=170)])
    q_score = StringField(u'Quantitative Reasoning')
    aw_score = SelectField(u'Analytical Writing', coerce=unicode)
    retrieved = BooleanField(u'已回收试卷')
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditYGRETestScoreForm, self).__init__(*args, **kwargs)
        self.test.choices = [(u'', u'选择Y-GRE考试')] + [(unicode(test.id), test.alias) for test in Test.query.order_by(Test.id.asc()).all() if test.lesson.type.name == u'Y-GRE']
        self.aw_score.choices = [(u'', u'选择AW成绩')] + [(unicode(aw_score.id), aw_score.name) for aw_score in GREAWScore.query.order_by(GREAWScore.id.desc()).all()]


class NewGRETestScoreForm(FlaskForm):
    email = StringField(u'用户（邮箱）', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    v_score = IntegerField(u'Verbal Reasoning', validators=[Required(), NumberRange(min=130, max=170)])
    q_score = IntegerField(u'Quantitative Reasoning', validators=[Required(), NumberRange(min=130, max=170)])
    aw_score = SelectField(u'Analytical Writing', coerce=unicode, validators=[Required()])
    test_date = DateField(u'考试日期', validators=[Required()])
    score_label = SelectField(u'标签', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'添加')

    def __init__(self, *args, **kwargs):
        super(NewGRETestScoreForm, self).__init__(*args, **kwargs)
        self.aw_score.choices = [(u'', u'选择AW成绩')] + [(unicode(aw_score.id), aw_score.name) for aw_score in GREAWScore.query.order_by(GREAWScore.id.desc()).all()]
        self.score_label.choices = [(u'', u'选择标签')] + [(u'0', u'无')] + [(unicode(score_label.id), score_label.name) for score_label in ScoreLabel.query.filter_by(category=u'GRE').order_by(ScoreLabel.id.asc()).all() if score_label.name not in [u'目标']]


class EditGRETestScoreForm(FlaskForm):
    v_score = IntegerField(u'Verbal Reasoning', validators=[Required(), NumberRange(min=130, max=170)])
    q_score = IntegerField(u'Quantitative Reasoning', validators=[Required(), NumberRange(min=130, max=170)])
    aw_score = SelectField(u'Analytical Writing', coerce=unicode, validators=[Required()])
    test_date = DateField(u'考试日期', validators=[Required()])
    score_label = SelectField(u'标签', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditGRETestScoreForm, self).__init__(*args, **kwargs)
        self.aw_score.choices = [(u'', u'选择AW成绩')] + [(unicode(aw_score.id), aw_score.name) for aw_score in GREAWScore.query.order_by(GREAWScore.id.desc()).all()]
        self.score_label.choices = [(u'', u'选择标签')] + [(u'0', u'无')] + [(unicode(score_label.id), score_label.name) for score_label in ScoreLabel.query.filter_by(category=u'GRE').order_by(ScoreLabel.id.asc()).all() if score_label.name not in [u'目标']]


class NewTOEFLTestScoreForm(FlaskForm):
    email = StringField(u'用户（邮箱）', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    total = IntegerField(u'TOEFL总分', validators=[Required(), NumberRange(min=0, max=120)])
    reading = IntegerField(u'Reading', validators=[Required(), NumberRange(min=0, max=30)])
    listening = IntegerField(u'Listening', validators=[Required(), NumberRange(min=0, max=30)])
    speaking = IntegerField(u'Speaking', validators=[Required(), NumberRange(min=0, max=30)])
    writing = IntegerField(u'Writing', validators=[Required(), NumberRange(min=0, max=30)])
    test_date = DateField(u'考试日期', validators=[Required()])
    score_label = SelectField(u'标签', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'添加')

    def __init__(self, *args, **kwargs):
        super(NewTOEFLTestScoreForm, self).__init__(*args, **kwargs)
        self.score_label.choices = [(u'', u'选择标签')] + [(u'0', u'无')] + [(unicode(score_label.id), score_label.name) for score_label in ScoreLabel.query.filter_by(category=u'TOEFL').order_by(ScoreLabel.id.asc()).all() if score_label.name not in [u'目标']]


class EditTOEFLTestScoreForm(FlaskForm):
    total = IntegerField(u'TOEFL总分', validators=[Required(), NumberRange(min=0, max=120)])
    reading = IntegerField(u'Reading', validators=[Required(), NumberRange(min=0, max=30)])
    listening = IntegerField(u'Listening', validators=[Required(), NumberRange(min=0, max=30)])
    speaking = IntegerField(u'Speaking', validators=[Required(), NumberRange(min=0, max=30)])
    writing = IntegerField(u'Writing', validators=[Required(), NumberRange(min=0, max=30)])
    test_date = DateField(u'考试日期', validators=[Required()])
    score_label = SelectField(u'标签', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditTOEFLTestScoreForm, self).__init__(*args, **kwargs)
        self.score_label.choices = [(u'', u'选择标签')] + [(u'0', u'无')] + [(unicode(score_label.id), score_label.name) for score_label in ScoreLabel.query.filter_by(category=u'TOEFL').order_by(ScoreLabel.id.asc()).all() if score_label.name not in [u'目标']]


class NewUserForm(FlaskForm):
    # basic
    name = StringField(u'姓名', validators=[Required(), Length(1, 64)])
    id_type = SelectField(u'证件类型', coerce=unicode, validators=[Required()])
    id_number = StringField(u'证件号码', validators=[Required(), Length(1, 64)])
    gender = SelectField(u'性别', coerce=unicode, validators=[Required()])
    birthdate = DateField(u'出生日期', validators=[Required()])
    residence = StringField(u'归属地')
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
    high_school_year = StringField(u'入学年份', validators=[Length(0, 16)])
    # bachelor
    bachelor_school = StringField(u'本科学校', validators=[Length(0, 64)])
    bachelor_major = StringField(u'院系（专业）', validators=[Length(0, 64)])
    bachelor_gpa = StringField(u'GPA', validators=[Length(0, 64)])
    bachelor_full_gpa = StringField(u'GPA满分', validators=[Length(0, 64)])
    bachelor_year = StringField(u'入学年份', validators=[Length(0, 16)])
    # master
    master_school = StringField(u'研究生学校（硕士）', validators=[Length(0, 64)])
    master_major = StringField(u'院系（专业）', validators=[Length(0, 64)])
    master_gpa = StringField(u'GPA', validators=[Length(0, 64)])
    master_full_gpa = StringField(u'GPA满分', validators=[Length(0, 64)])
    master_year = StringField(u'入学年份', validators=[Length(0, 16)])
    # doctor
    doctor_school = StringField(u'研究生学校（博士）', validators=[Length(0, 64)])
    doctor_major = StringField(u'院系（专业）', validators=[Length(0, 64)])
    doctor_gpa = StringField(u'GPA', validators=[Length(0, 64)])
    doctor_full_gpa = StringField(u'GPA满分', validators=[Length(0, 64)])
    doctor_year = StringField(u'入学年份', validators=[Length(0, 16)])
    # job 1
    employer_1 = StringField(u'工作单位', validators=[Length(0, 64)])
    position_1 = StringField(u'职务', validators=[Length(0, 64)])
    job_year_1 = StringField(u'入职年份', validators=[Length(0, 16)])
    # job 2
    employer_2 = StringField(u'工作单位', validators=[Length(0, 64)])
    position_2 = StringField(u'职务', validators=[Length(0, 64)])
    job_year_2 = StringField(u'入职年份', validators=[Length(0, 16)])
    # scores
    cee_total = StringField(u'高考总分', validators=[Length(0, 64)])
    cee_total_full = StringField(u'高考总分满分', validators=[Length(0, 64)])
    cee_math = StringField(u'高考数学', validators=[Length(0, 64)])
    cee_math_full = StringField(u'高考数学满分', validators=[Length(0, 64)])
    cee_english = StringField(u'高考英语', validators=[Length(0, 64)])
    cee_english_full = StringField(u'高考英语满分', validators=[Length(0, 64)])
    cet_4 = StringField(u'CET-4', validators=[Length(0, 64)])
    cet_6 = StringField(u'CET-6', validators=[Length(0, 64)])
    tem_4 = StringField(u'TEM-4', validators=[Length(0, 64)])
    tem_8 = StringField(u'TEM-8', validators=[Length(0, 64)])
    competition = StringField(u'竞赛成绩', validators=[Length(0, 128)])
    other_score = StringField(u'其它成绩', validators=[Length(0, 128)])
    # registration
    purposes = SelectMultipleField(u'研修目的', coerce=unicode)
    other_purpose = StringField(u'其它研修目的', validators=[Length(0, 64)])
    referrers = SelectMultipleField(u'了解渠道', coerce=unicode)
    other_referrer = StringField(u'其它了解渠道', validators=[Length(0, 64)])
    inviter_email = StringField(u'同学推荐（邮箱）', validators=[Length(0, 64)])
    application_aim = StringField(u'申请方向', validators=[Length(0, 128)])
    application_agency = StringField(u'留学中介', validators=[Length(0, 128)])
    products = SelectMultipleField(u'研修产品', coerce=unicode, validators=[Required()])
    role = SelectField(u'用户权限', coerce=unicode, validators=[Required()])
    vb_course = SelectField(u'VB班', coerce=unicode, validators=[Required()])
    y_gre_course = SelectField(u'Y-GRE班', coerce=unicode, validators=[Required()])
    # submit
    submit = SubmitField(u'下一步')

    def __init__(self, *args, **kwargs):
        super(NewUserForm, self).__init__(*args, **kwargs)
        self.id_type.choices = [(u'', u'选择证件类型')] + [(unicode(id_type.id), id_type.name) for id_type in IDType.query.order_by(IDType.id.asc()).all()]
        self.gender.choices = [(u'', u'选择性别')] + [(unicode(gender.id), gender.name) for gender in Gender.query.order_by(Gender.id.asc()).all()]
        self.emergency_contact_relationship.choices = [(u'', u'选择关系')] +  [(unicode(relationship.id), relationship.name) for relationship in Relationship.query.order_by(Relationship.id.asc()).all()]
        self.purposes.choices = [(u'', u'选择研修目的')] + [(unicode(purpose_type.id), purpose_type.name) for purpose_type in PurposeType.query.order_by(PurposeType.id.asc()).all() if purpose_type.name != u'其它']
        self.referrers.choices = [(u'', u'选择了解渠道')] + [(unicode(referrer_type.id), referrer_type.name) for referrer_type in ReferrerType.query.order_by(ReferrerType.id.asc()).all() if referrer_type.name != u'其它']
        self.products.choices = [(u'', u'选择研修产品')] + [(unicode(product.id), u'%s（%g元）' % (product.name, product.price)) for product in Product.query.filter_by(available=True, deleted=False).order_by(Product.id.asc()).all() if product.name not in [u'团报优惠']]
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
    paid_in_full = BooleanField(u'已缴纳齐全款')
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
    year = StringField(u'入学年份', validators=[Required(), Length(1, 16)])
    submit = SubmitField(u'添加')

    def __init__(self, *args, **kwargs):
        super(NewEducationRecordForm, self).__init__(*args, **kwargs)
        self.education_type.choices = [(u'', u'选择学历类型')] + [(unicode(education_type.id), education_type.name) for education_type in EducationType.query.order_by(EducationType.id.asc()).all()]


class NewEmploymentRecordForm(FlaskForm):
    employer = StringField(u'工作单位', validators=[Required(), Length(1, 64)])
    position = StringField(u'职务', validators=[Required(), Length(1, 64)])
    year = StringField(u'入职年份', validators=[Required(), Length(1, 16)])
    submit = SubmitField(u'添加')


class NewScoreRecordForm(FlaskForm):
    score_type = SelectField(u'成绩类型', coerce=unicode, validators=[Required()])
    score = StringField(u'成绩', validators=[Length(0, 128)])
    full_score = StringField(u'满分', validators=[Length(0, 128)])
    submit = SubmitField(u'添加')

    def __init__(self, *args, **kwargs):
        super(NewScoreRecordForm, self).__init__(*args, **kwargs)
        self.score_type.choices = [(u'', u'选择成绩类型')] + [(unicode(score_type.id), score_type.name) for score_type in ScoreType.query.order_by(ScoreType.id.asc()).all()]


class NewAdminForm(FlaskForm):
    name = StringField(u'姓名', validators=[Required(), Length(1, 64)])
    id_type = SelectField(u'证件类型', coerce=unicode, validators=[Required()])
    id_number = StringField(u'证件号码', validators=[Required(), Length(1, 64)])
    gender = SelectField(u'性别', coerce=unicode, validators=[Required()])
    birthdate = DateField(u'出生日期', validators=[Required()])
    residence = StringField(u'归属地')
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email(message=u'请输入一个有效的电子邮箱地址')])
    role = SelectField(u'用户权限', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'新建管理用户')

    def __init__(self, creator, *args, **kwargs):
        super(NewAdminForm, self).__init__(*args, **kwargs)
        self.id_type.choices = [(u'', u'选择证件类型')] + [(unicode(id_type.id), id_type.name) for id_type in IDType.query.order_by(IDType.id.asc()).all()]
        self.gender.choices = [(u'', u'选择性别')] + [(unicode(gender.id), gender.name) for gender in Gender.query.order_by(Gender.id.asc()).all()]
        if creator.is_developer:
            self.role.choices = [(u'', u'选择权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'志愿者', u'协管员', u'管理员', u'开发人员']]
        else:
            self.role.choices = [(u'', u'选择权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'志愿者', u'协管员', u'管理员']]


class EditNameForm(FlaskForm):
    name = StringField(u'姓名', validators=[Required(), Length(1, 64)])
    submit = SubmitField(u'更新')


class EditGenderForm(FlaskForm):
    gender = SelectField(u'性别', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'更新')

    def __init__(self, *args, **kwargs):
        super(EditGenderForm, self).__init__(*args, **kwargs)
        self.gender.choices = [(u'', u'选择性别')] + [(unicode(gender.id), gender.name) for gender in Gender.query.order_by(Gender.id.asc()).all()]


class EditBirthdateForm(FlaskForm):
    birthdate = DateField(u'出生日期', validators=[Required()])
    submit = SubmitField(u'更新')


class EditIDNumberForm(FlaskForm):
    id_type = SelectField(u'证件类型', coerce=unicode, validators=[Required()])
    id_number = StringField(u'证件号码', validators=[Required(), Length(1, 64)])
    submit = SubmitField(u'更新')

    def __init__(self, *args, **kwargs):
        super(EditIDNumberForm, self).__init__(*args, **kwargs)
        self.id_type.choices = [(u'', u'选择证件类型')] + [(unicode(id_type.id), id_type.name) for id_type in IDType.query.order_by(IDType.id.asc()).all()]


class EditUserTagForm(FlaskForm):
    tags = SelectMultipleField(u'用户标签', coerce=unicode)
    submit = SubmitField(u'更新')

    def __init__(self, *args, **kwargs):
        super(EditUserTagForm, self).__init__(*args, **kwargs)
        self.tags.choices = [(u'', u'选择用户标签')] + [(unicode(tag.id), tag.name) for tag in Tag.query.order_by(Tag.id.asc()).all()]


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


class EditApplicationForm(FlaskForm):
    application_aim = StringField(u'申请方向', validators=[Length(0, 128)])
    application_agency = StringField(u'留学中介', validators=[Length(0, 128)])
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
        self.product.choices = [(u'', u'选择研修产品')] + [(unicode(product.id), product.alias) for product in Product.query.filter_by(available=True, deleted=False).order_by(Product.id.asc()).all() if product.name not in [u'团报优惠']]


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
            self.role.choices = [(u'', u'选择用户权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name not in [u'挂起']]
        elif editor.is_administrator:
            self.role.choices = [(u'', u'选择用户权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name not in [u'挂起', u'开发人员']]
        elif editor.is_moderator and is_self:
            self.role.choices = [(u'', u'选择用户权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name not in [u'挂起', u'管理员', u'开发人员']]
        else:
            self.role.choices = [(u'', u'选择用户权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'单VB', u'Y-GRE 普通', u'Y-GRE VB×2', u'Y-GRE A权限', u'志愿者']]


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
    reset_due_time = BooleanField(u'重置有效期')
    submit = SubmitField(u'恢复')

    def __init__(self, restorer, *args, **kwargs):
        super(RestoreUserForm, self).__init__(*args, **kwargs)
        if restorer.is_developer:
            self.role.choices = [(u'', u'选择用户权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name not in [u'挂起']]
        elif restorer.is_administrator:
            self.role.choices = [(u'', u'选择用户权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name not in [u'挂起', u'开发人员']]
        else:
            self.role.choices = [(u'', u'选择用户权限')] + [(unicode(role.id), role.name) for role in Role.query.order_by(Role.id.asc()).all() if role.name in [u'单VB', u'Y-GRE 普通', u'Y-GRE VB×2', u'Y-GRE A权限']]

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'%s已经被注册' % field.data)


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


class NewTagForm(FlaskForm):
    name = StringField(u'用户标签名称', validators=[Required(), Length(1, 64)])
    color = SelectField('标签颜色', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewTagForm, self).__init__(*args, **kwargs)
        self.color.choices = [(u'', u'选择标签颜色')] + [(unicode(color.id), color.name) for color in Color.query.order_by(Color.id.asc()).all()]


class EditTagForm(FlaskForm):
    name = StringField(u'用户标签名称', validators=[Required(), Length(1, 64)])
    color = SelectField('标签颜色', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'提交')

    def __init__(self, tag, *args, **kwargs):
        super(EditTagForm, self).__init__(*args, **kwargs)
        self.color.choices = [(u'', u'选择标签颜色')] + [(unicode(color.id), color.name) for color in Color.query.order_by(Color.id.asc()).all()]
        self.tag = tag

    def validate_name(self, field):
        if field.data != self.tag.name and Tag.query.filter_by(name=field.data).first():
            raise ValidationError(u'“%s”标签已存在' % field.data)


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
        self.vb_lessons.choices = [(u'', u'选择VB内容')] + [(unicode(lesson.id), lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.include_video and lesson.type.name == u'VB']
        self.y_gre_lessons.choices = [(u'', u'选择Y-GRE内容')] + [(unicode(lesson.id), lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.include_video and lesson.type.name == u'Y-GRE']

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
        self.vb_lessons.choices = [(u'', u'选择VB内容')] + [(unicode(lesson.id), lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.include_video and lesson.type.name == u'VB']
        self.y_gre_lessons.choices = [(u'', u'选择Y-GRE内容')] + [(unicode(lesson.id), lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.include_video and lesson.type.name == u'Y-GRE']
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
        self.vb_lessons.choices = [(u'', u'选择VB内容')] + [(unicode(lesson.id), lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.include_video and lesson.type.name == u'VB']
        self.y_gre_lessons.choices = [(u'', u'选择Y-GRE内容')] + [(unicode(lesson.id), lesson.name) for lesson in Lesson.query.order_by(Lesson.id.asc()).all() if lesson.include_video and lesson.type.name == u'Y-GRE']


class EditStudyPlanForm(FlaskForm):
    # GRE aim
    gre_aim_v = IntegerField(u'Verbal Reasoning', validators=[Required(), NumberRange(min=130, max=170)])
    gre_aim_q = IntegerField(u'Quantitative Reasoning', validators=[Required(), NumberRange(min=130, max=170)])
    gre_aim_aw = SelectField(u'Analytical Writing', coerce=unicode, validators=[Required()])
    # TOEFL aim
    toefl_aim_total = IntegerField(u'TOEFL总分', validators=[Required(), NumberRange(min=0, max=120)])
    toefl_aim_reading = IntegerField(u'Reading', validators=[Required(), NumberRange(min=0, max=30)])
    toefl_aim_listening = IntegerField(u'Listening', validators=[Required(), NumberRange(min=0, max=30)])
    toefl_aim_speaking = IntegerField(u'Speaking', validators=[Required(), NumberRange(min=0, max=30)])
    toefl_aim_writing = IntegerField(u'Writing', validators=[Required(), NumberRange(min=0, max=30)])
    # study plan
    speed = StringField(u'时间系数', validators=[Required(), Length(0, 64)])
    deadline = DateField(u'Deadline')
    vb_intro_start_date = DateField(u'开始日期', validators=[Optional()])
    vb_intro_end_date = DateField(u'结束日期', validators=[Optional()])
    vb_intro_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    vb_1_start_date = DateField(u'开始日期', validators=[Optional()])
    vb_1_end_date = DateField(u'结束日期', validators=[Optional()])
    vb_1_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    vb_2_start_date = DateField(u'开始日期', validators=[Optional()])
    vb_2_end_date = DateField(u'结束日期', validators=[Optional()])
    vb_2_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    vb_3_start_date = DateField(u'开始日期', validators=[Optional()])
    vb_3_end_date = DateField(u'结束日期', validators=[Optional()])
    vb_3_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    vb_4_start_date = DateField(u'开始日期', validators=[Optional()])
    vb_4_end_date = DateField(u'结束日期', validators=[Optional()])
    vb_4_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    vb_5_start_date = DateField(u'开始日期', validators=[Optional()])
    vb_5_end_date = DateField(u'结束日期', validators=[Optional()])
    vb_5_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    vb_6_start_date = DateField(u'开始日期', validators=[Optional()])
    vb_6_end_date = DateField(u'结束日期', validators=[Optional()])
    vb_6_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    vb_7_start_date = DateField(u'开始日期', validators=[Optional()])
    vb_7_end_date = DateField(u'结束日期', validators=[Optional()])
    vb_7_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    vb_8_start_date = DateField(u'开始日期', validators=[Optional()])
    vb_8_end_date = DateField(u'结束日期', validators=[Optional()])
    vb_8_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    vb_9_start_date = DateField(u'开始日期', validators=[Optional()])
    vb_9_end_date = DateField(u'结束日期', validators=[Optional()])
    vb_9_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    y_gre_intro_start_date = DateField(u'开始日期', validators=[Optional()])
    y_gre_intro_end_date = DateField(u'结束日期', validators=[Optional()])
    y_gre_intro_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    y_gre_1_start_date = DateField(u'开始日期', validators=[Optional()])
    y_gre_1_end_date = DateField(u'结束日期', validators=[Optional()])
    y_gre_1_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    y_gre_2_start_date = DateField(u'开始日期', validators=[Optional()])
    y_gre_2_end_date = DateField(u'结束日期', validators=[Optional()])
    y_gre_2_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    y_gre_3_start_date = DateField(u'开始日期', validators=[Optional()])
    y_gre_3_end_date = DateField(u'结束日期', validators=[Optional()])
    y_gre_3_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    y_gre_4_start_date = DateField(u'开始日期', validators=[Optional()])
    y_gre_4_end_date = DateField(u'结束日期', validators=[Optional()])
    y_gre_4_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    y_gre_5_start_date = DateField(u'开始日期', validators=[Optional()])
    y_gre_5_end_date = DateField(u'结束日期', validators=[Optional()])
    y_gre_5_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    y_gre_6_start_date = DateField(u'开始日期', validators=[Optional()])
    y_gre_6_end_date = DateField(u'结束日期', validators=[Optional()])
    y_gre_6_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    y_gre_7_start_date = DateField(u'开始日期', validators=[Optional()])
    y_gre_7_end_date = DateField(u'结束日期', validators=[Optional()])
    y_gre_7_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    y_gre_8_start_date = DateField(u'开始日期', validators=[Optional()])
    y_gre_8_end_date = DateField(u'结束日期', validators=[Optional()])
    y_gre_8_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    y_gre_9_start_date = DateField(u'开始日期', validators=[Optional()])
    y_gre_9_end_date = DateField(u'结束日期', validators=[Optional()])
    y_gre_9_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    y_gre_prep_start_date = DateField(u'开始日期', validators=[Optional()])
    y_gre_prep_end_date = DateField(u'结束日期', validators=[Optional()])
    y_gre_prep_notate_bene = SelectMultipleField(u'N.B.', coerce=unicode)
    gre_0_date = DateField(u'G<sub>0</sub>', validators=[Optional()])
    gre_1_date = DateField(u'G<sub>1</sub>', validators=[Optional()])
    gre_2_date = DateField(u'G<sub>2</sub>', validators=[Optional()])
    gre_3_date = DateField(u'G<sub>3</sub>', validators=[Optional()])
    supervisor_email = StringField(u'设计人（邮箱）', validators=[Length(0, 64)])
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditStudyPlanForm, self).__init__(*args, **kwargs)
        self.vb_intro_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'VB']
        self.vb_1_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'VB']
        self.vb_2_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'VB']
        self.vb_3_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'VB']
        self.vb_4_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'VB']
        self.vb_5_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'VB']
        self.vb_6_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'VB']
        self.vb_7_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'VB']
        self.vb_8_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'VB']
        self.vb_9_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'VB']
        self.y_gre_intro_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'Y-GRE']
        self.y_gre_1_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'Y-GRE']
        self.y_gre_2_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'Y-GRE']
        self.y_gre_3_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'Y-GRE']
        self.y_gre_4_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'Y-GRE']
        self.y_gre_5_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'Y-GRE']
        self.y_gre_6_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'Y-GRE']
        self.y_gre_7_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'Y-GRE']
        self.y_gre_8_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'Y-GRE']
        self.y_gre_9_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'Y-GRE']
        self.y_gre_prep_notate_bene.choices = [(u'', u'选择N.B.')] + [(unicode(nota_bene.id), nota_bene.body) for nota_bene in NotaBene.query.order_by(NotaBene.id.asc()).all() if nota_bene.type.name == u'Y-GRE']

    def validate_supervisor_email(self, field):
        if field.data and User.query.filter_by(email=field.data, created=True, activated=True, deleted=False).first() is None:
            raise ValidationError(u'设计人邮箱不存在：%s' % field.data)


class NewNotaBeneForm(FlaskForm):
    body = StringField(u'Nota Bene', validators=[Required(), Length(1, 128)])
    nota_bene_type = SelectField(u'N.B.类型', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewNotaBeneForm, self).__init__(*args, **kwargs)
        self.nota_bene_type.choices = [(u'', u'选择N.B.类型')] + [(unicode(course_type.id), course_type.name) for course_type in CourseType.query.order_by(CourseType.id.asc()).all()]


class EditNotaBeneForm(FlaskForm):
    body = StringField(u'Nota Bene', validators=[Required(), Length(1, 128)])
    nota_bene_type = SelectField(u'N.B.类型', coerce=unicode, validators=[Required()])
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(EditNotaBeneForm, self).__init__(*args, **kwargs)
        self.nota_bene_type.choices = [(u'', u'选择N.B.类型')] + [(unicode(course_type.id), course_type.name) for course_type in CourseType.query.order_by(CourseType.id.asc()).all()]


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
    check_overdue = BooleanField(u'逾期失效')
    submit = SubmitField(u'提交')


class EditPermissionForm(FlaskForm):
    name = StringField(u'权限名称', validators=[Required(), Length(1, 64)])
    check_overdue = BooleanField(u'逾期失效')
    submit = SubmitField(u'提交')

    def __init__(self, permission, *args, **kwargs):
        super(EditPermissionForm, self).__init__(*args, **kwargs)
        self.permission = permission

    def validate_name(self, field):
        if field.data != self.permission.name and Permission.query.filter_by(name=field.data).first():
            raise ValidationError(u'“%s”权限已存在' % field.data)