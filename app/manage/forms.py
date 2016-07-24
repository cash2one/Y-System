# -*- coding: utf-8 -*-

from datetime import date, timedelta
from flask_wtf import Form
from wtforms import StringField, BooleanField, DateField, IntegerField, SelectField, SelectMultipleField, SubmitField
from wtforms.validators import Required, NumberRange
from wtforms import ValidationError
from ..models import Period, iPadCapacity, iPadState, Room, Lesson


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
        self.date.choices = [(NextDayString(x, short=True), NextDayString(x), ) for x in range(10)]
        self.period.choices = [(period.id, period.alias) for period in Period.query.order_by(Period.id).all()]


class NewiPadForm(Form):
    alias = StringField(u'编号')
    serial = StringField(u'序列号', validators=[Required()])
    capacity = SelectField(u'容量', coerce=int)
    room = SelectField(u'房间', coerce=int)
    state = SelectField(u'状态', coerce=int)
    vb_lessons = SelectMultipleField(u'VB内容', coerce=int)
    y_gre_lessons = SelectMultipleField(u'Y-GRE内容', coerce=int)
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(NewiPadForm, self).__init__(*args, **kwargs)
        self.capacity.choices = [(capacity.id, capacity.name) for capacity in iPadCapacity.query.order_by(iPadCapacity.id).all()]
        self.room.choices = [(room.id, room.name) for room in Room.query.order_by(Room.id).all()]
        self.state.choices = [(state.id, state.name) for state in iPadState.query.order_by(iPadState.id).all()]
        self.vb_lessons.choices = [(lesson.id, lesson.name) for lesson in Lesson.query.order_by(Lesson.id).all() if lesson.type.name == u'VB']
        self.y_gre_lessons.choices = [(lesson.id, lesson.name) for lesson in Lesson.query.order_by(Lesson.id).all() if lesson.type.name == u'Y-GRE']
