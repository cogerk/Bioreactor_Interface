from flask_wtf import Form
from wtforms import StringField, FloatField, BooleanField, \
    SelectField, IntegerField, SubmitField
from wtforms.validators import DataRequired


# TODO: Make reactor list dynamic & add reactor addition page instead
REACTORS = [('R1', 'Reactor 1'),
            ('R2', 'Reactor 2')]
# TODO: Add email alarms
# TODO: email address validation
# TODO: Build rest of forms
class Settings(Form):
    reactor_no = SelectField('Reactor Number',
                            choices=REACTORS,
                             default=REACTORS[0])
    email = StringField('Email Address', default='cogerk@gmail.com')
    IP = StringField('cRIO IP', default='128.208.236.57')
    port = IntegerField('Webservice Port', default=8001)


class pHSwitch(Form):
    # TODO: Programmatically change label based off of control loop?
    control_on = BooleanField('pH Control On?')
    submit = SubmitField('Send')

class pHManual(Form):
    acid_on = BooleanField('Base Pump On?',
                          default=False)
    base_on = BooleanField('Acid Pump On?',
                          default=False)
    submit = SubmitField('Send')


class pHAuto(Form):
    pH_delay = FloatField('Control Loop Time Delay, s',
                             default=3)
    pH_setpt = FloatField('pH Set Point',
                             default=7)
    pH_tol = FloatField('pH Tolerance',
                             default=0.1)
    submit = SubmitField('Send')