from flask.ext.wtf import Form
from wtforms import StringField, HiddenField, BooleanField
from wtforms.validators import InputRequired, ValidationError
from flask.ext.wtf.html5 import URLField, DateField
from datetime import date


class EventForm(Form):
    name = StringField('Name', validators=[InputRequired()])
    start_date = DateField('Start date', validators=[InputRequired()], default=date.today())
    end_date = DateField('End date', validators=[InputRequired()], default=date.today())
    event_url = URLField('URL', validators=[InputRequired()])
    twitter_hashtags = StringField('Hashtags')
    twitter_account = StringField('Twitter account')
    venue = StringField('Venue')
    address = StringField('City')
    series = StringField('Series')
    city_id = HiddenField()
    is_published = BooleanField('Is published')

    def validate_end_date(form, field):
        if field.data < form.start_date.data:
            raise ValidationError(u'End date can not be before start date')


class SearchForm(Form):
    search_string = StringField('Query')
