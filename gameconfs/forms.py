from flask.ext.wtf import Form
from wtforms import TextField, HiddenField
from wtforms.validators import InputRequired, ValidationError
from flask.ext.wtf.html5 import URLField, DateField
from datetime import date


class EventForm(Form):
    name = TextField('Name', validators=[InputRequired()])
    start_date = DateField('Start date', validators=[InputRequired()], default=date.today())
    end_date = DateField('End date', validators=[InputRequired()], default=date.today())
    event_url = URLField('URL', validators=[InputRequired()])
    twitter_hashtags = TextField('Hashtags')
    twitter_account = TextField('Twitter account')
    venue = TextField('Venue')
    address = TextField('City')
    series = TextField('Series')
    city_id = HiddenField()

    def validate_end_date(form, field):
        if field.data < form.start_date.data:
            raise ValidationError(u'End date can not be before start date')


class SearchForm(Form):
    search_string = TextField('Query')
