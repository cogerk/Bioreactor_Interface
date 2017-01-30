from flask_wtf import Form
from wtforms import StringField, FloatField, BooleanField, \
    SelectField, IntegerField, SubmitField, HiddenField
from wtforms.validators import DataRequired
import utils
import customerrs as cust


# TODO: Make reactor list dynamic & add reactor addition page instead
REACTORS = [('R1', 'Reactor 1'),
            ('R2', 'Reactor 2')]
# TODO: Add email alarms
# TODO: email address validation
# TODO: Fix Labels
# TODO: Rework how SBR forms are generated <-
# TODO: Change so that defaults populate from reactor on build_forms <-
# TODO: Build validators
# TODO: When you write something new show it hasn't been submitted yet somehow.

def build_forms(reactorno=1):
    form_dict = {}
    for loop in cust.LOOPS:
        form_dict[loop] = {}
        for action in cust.ACTIONS:
            if action is not 'Status':
                form_dict[loop][action] = {}

                class F(Form):
                    pass
                prefix = loop+'_'+action
                if action is not 'Switch':
                    F.submit = SubmitField('Send')
                    for name in cust.loopdict[loop][action]:
                        default = cust.loopdict[loop][action][name]
                        field_type = type(cust.loopdict[loop][action][name])
                        if field_type is bool:
                            setattr(F, name, BooleanField(name+'_on',
                                                          default=default))
                        if field_type is float \
                                or field_type is str \
                                or field_type is int:
                            setattr(F, name, FloatField(name,
                                                        default=default))
                        if type(cust.loopdict[loop][action][name]) is list:
                            setattr(F, name, SelectField(name,
                                                         choices=default,
                                                         default=default[0]))
                else:
                    label = loop+' Control On?'
                    F.control_on = BooleanField(label)
                form_dict[loop][action] = F(prefix=prefix)
    return form_dict


class Settings(Form):
    reactor_no = SelectField('Reactor Number',
                             choices=REACTORS,
                             default=REACTORS[0])
    email = StringField('Email Address', default='cogerk@gmail.com')
    IP = StringField('cRIO IP', default='128.208.236.57')
    port = IntegerField('Webservice Port', default=8001)