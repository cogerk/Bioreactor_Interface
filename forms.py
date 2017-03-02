import sqlite3
from flask_wtf import Form
from wtforms import StringField, FloatField, BooleanField, \
    SelectField, IntegerField, SubmitField
import utils
import calconstanthandler as calconst
import constanthandler as const
import controlcmdhandler as cmd
from __init__ import models
# TODO: Add email alarms
# TODO: email address validation
# TODO: Build validators
# TODO: When you write something new show it hasn't been submitted yet somehow.

def create_reactor_form(rct_list):
    class SelectReactor(Form):
        # This is the form on the front page used to pick the reactor to control
        print(rct_list)
        reactor_no = SelectField('Reactor Number',
                                 choices=rct_list,
                                 default=rct_list[0])
    return SelectReactor


def build_constant_form(ip, port, reactorno):
    constants, constant_list = const.get_all_current(ip, port, reactorno)
    class ConstantForm(Form):
        # This generates the constants form
        constant_list = zip(constant_list,constant_list)
        constant = SelectField('Signal',
                             choices=constant_list,
                             default=constant_list)
    setattr(ConstantForm,
            'value',
            FloatField('Value', default=constants[constant_list[0][0]]))
    return ConstantForm, constants


def build_calconstant_form(ip, port, reactorno):
    signal_list, slopes, ints = calconst.get_all_current(ip, port, reactorno)
    signal_list = zip(signal_list, signal_list)
    class CalConstantForm(Form):
        # This generates the calibration constant form

        signal = SelectField('Signal',
                             choices=signal_list,
                             default=signal_list)
    setattr(CalConstantForm,
            'slope',
            FloatField('Slope', default=slopes[signal_list[0][0]]))
    setattr(CalConstantForm,
            'intercept',
            FloatField('intercept', default=ints[signal_list[0][0]]))
    return CalConstantForm, slopes, ints


def build_control_forms(ip, port, reactorno):
    """
    Programatically build dict of dict of forms for the remote control panel
    :param reactorno: int, given reactor number to build forms for
    :return:
    """
    current, loops = cmd.get_current(ip, port, reactorno)
    form_dict = {}
    # Loop through all given control loops and manual/setparams/switch actions
    for loop in loops:
        form_dict[loop] = {}
        for action in utils.ACTIONS:
            if action is 'Status':
                continue
            form_dict[loop][action] = {}
            # Define a new form class

            class F(Form):
                pass
            # Name the form prefix after the loop and action
            prefix = loop+'_'+action
            if action == 'Switch':
                # This is what a switch form looks like, simple huh?
                label = loop+' Control On?'
                F.control_on = BooleanField(label)
                form_dict[loop][action] = F(prefix=prefix)
                continue
            # Switching loop on/off happens onclick in the form so
            # If not building switch form, add a submit button.
            F.submit = SubmitField('Send')
            for param in current[loop][loop+'_'+action]:
                # Loop through 'commands' for given loop and action.
                # i.e. ph_manual -> acid pump & base pump
                # i.e. do_set params -> do set pt, n2 gain, etc. etc.
                name = param[0]
                default = param[1]
                field_type = type(default)
                # Use data type of command to determine field
                # i.e. boolean -> checkbox, float -> double
                if field_type is bool: # Default value assigned w/ jquery
                    setattr(F, name, BooleanField(name+' On?'))
                if field_type is float:
                    setattr(F, name, FloatField(name))
                if field_type is str:
                    setattr(F, name, StringField(name))
                if field_type is int:
                    setattr(F, name, IntegerField(name))
            # Assign form to appropriate location in form dictionary
            form_dict[loop][action] = F(prefix=prefix)
    return form_dict, current, loops

