from flask.ext.wtf import Form, TextField, TextAreaField, Required, ValidationError
from flask.ext.wtf.html5 import URLField, DateField
from datetime import date

class EventForm(Form):
    name = TextField('Name', validators=[Required()])
    start_date = DateField('Start date', validators=[Required()], format='%d/%m/%Y', default=date.today())
    end_date = DateField('End date', format='%d/%m/%Y', default=date.today())
    main_url = URLField('URL')
    twitter_hashtags = TextField('Hashtags')
    twitter_account = TextField('Twitter account')
    location = TextField('Location')
    address = TextAreaField('City')

    def validate_end_date(form, field):
        if field.data < form.start_date.data:
            raise ValidationError(u'End date can not be before start date')
