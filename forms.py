from flask_wtf import Form
from wtforms import StringField, FloatField, BooleanField, \
    SelectField, IntegerField, SubmitField, HiddenField, RadioField
from wtforms.validators import DataRequired
import utils
import customerrs as cust
import calconstanthandler as calconst
import constanthandler as const


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


class Settings(Form):
    # This is the form on the front page used to pick the reactor to control
    reactor_no = SelectField('Reactor Number',
                             choices=REACTORS,
                             default=REACTORS[0])
    email = StringField('Email Address', default='cogerk@gmail.com')
    IP = StringField('cRIO IP', default='128.208.236.57')
    port = IntegerField('Webservice Port', default=8001)


def build_constant_form(ip, port, reactorno):
    constants = const.get_all_current(ip, port, reactorno)
    class ConstantForm(Form):
        # This generates the constants form
        # TODO: Generalize for all reactors
        constant = SelectField('Signal',
                             choices=cust.CONSTANTS,
                             default=cust.CONSTANTS[0])
    setattr(ConstantForm,
            'value',
            FloatField('Value', default=constants[cust.CONSTANTS[0][0]]))
    return ConstantForm, constants


def build_calconstant_form(ip, port, reactorno):
    slopes, ints = calconst.get_all_current(ip, port, reactorno)
    class CalConstantForm(Form):
        # This generates the calibration constant form
        # TODO: Generalize for all reactors
        signal = SelectField('Signal',
                             choices=cust.SIGNALS,
                             default=cust.SIGNALS[0])
    setattr(CalConstantForm,
            'slope',
            FloatField('Slope', default=slopes[cust.SIGNALS[0][0]]))
    setattr(CalConstantForm,
            'intercept',
            FloatField('intercept', default=ints[cust.SIGNALS[0][0]]))
    return CalConstantForm, slopes, ints


def build_control_forms(reactorno):
    """
    Programatically build dict of dict of forms for the remote control panel
    :param reactorno: int, given reactor number to build forms for
    :return:
    """
    # TODO: Generalize for multiple reactors
    form_dict = {}
    # Loop through all given control loops and manual/setparams/switch actions
    for loop in cust.LOOPS:
        form_dict[loop] = {}

        for action in cust.ACTIONS:
            if action is not 'Status':
                form_dict[loop][action] = {}
                # Define a new form class

                class F(Form):
                    pass
                # Name the form prefix after the loop and action
                prefix = loop+'_'+action
                if action is not 'Switch':
                    # Switching loop on/off happens onclick in the form so
                    # If not building switch form, add a submit button.
                    F.submit = SubmitField('Send')
                    for name in cust.loopdict[loop][action]:
                        # Loop through 'commands' for given loop and action.
                        # i.e. ph_manual -> acid pump & base pump
                        # i.e. do_set params -> do set pt, n2 gain, etc. etc.
                        default = cust.loopdict[loop][action][name]
                        field_type = type(cust.loopdict[loop][action][name])
                        # Use data type of command default to determine field
                        # i.e. boolean -> checkbox, float -> double
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
                    # This is what a switch form looks like, simple huh?
                    label = loop+' Control On?'
                    F.control_on = BooleanField(label)
                # Assign form to appropriate location in form dictionary
                form_dict[loop][action] = F(prefix=prefix)
    return form_dict

