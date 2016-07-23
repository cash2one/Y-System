# -*- coding: utf-8 -*-

from datetime import date, timedelta
from flask_wtf import Form
from wtforms import StringField, BooleanField, DateField, IntegerField, SelectField, SelectMultipleField, SubmitField
from wtforms.validators import Required, NumberRange
from wtforms import ValidationError
from ..models import Period


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
