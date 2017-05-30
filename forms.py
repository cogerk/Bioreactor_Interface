from flask_wtf import Form
from wtforms import StringField, FloatField, BooleanField, \
    SelectField, IntegerField
import utils
import customerrs as cust
import controlcmdhandler as cmd
import isehandler as isehnd
# TODO: Unit Tests Labview
# TODO: Unit Tests Python
# TODO: Fake Reactor

def create_reactor_form(rct_list):
    class SelectReactor(Form):
        # This is the form on the front page used to pick the reactor
        reactor_no = SelectField('Reactor Number',
                                 choices=rct_list,
                                 default=rct_list[0])
    return SelectReactor


def build_constant_form(constants):
    constant_list = list(zip(constants.keys(), constants.keys()))

    class ConstantForm(Form):
        # This generates the constants form for a given reactor
        constant = SelectField('Constant',
                             choices=constant_list,
                             default=constant_list)
    setattr(ConstantForm,
            'value',
            FloatField('Value', default=constants[constant_list[0][0]][1]))
    return ConstantForm


def build_calconstant_form(signal_list, slopes, ints):
    signal_zip = list(zip(signal_list, signal_list))
    class CalConstantForm(Form):
        # This generates the calibration constant form for a given reactor

        signal = SelectField('Signal',
                             choices=signal_zip,
                             default=signal_zip[0])
    setattr(CalConstantForm,
            'slope',
            FloatField('Slope', default=slopes[signal_zip[0][0]]))
    setattr(CalConstantForm,
            'intercept',
            FloatField('Intercept', default=ints[signal_zip[0][0]]))
    return CalConstantForm


def build_control_forms(ip, port, reactorno):
    """
    Programatically build dict of dict of forms for the remote control panel
    :param reactorno: int, given reactor number to build forms for
    :return:
    """
    print('Building Form')
    current, loops = cmd.get_current(ip, port, reactorno)
    if loops is None:
        # TODO: Replace this with error handling
        return None, None, None
    form_dict = {}
    # Loop through all given control loops and manual/setparams/switch actions
    for loop in loops:
        if 'Unable to access' in current[loop]:
            continue
        elif not current[loop]:
            print(current[loop])
            current[loop] = loop + ' Status was blank, is R' + str(reactorno) \
                            + loop + 'Control_status.vi wired properly?'
            continue
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
            try:
                current[loop][loop+'_'+action]
            except KeyError:
                current[loop][loop+'_'+action] = 'Could not find ' + loop + \
                     '_' + action + ' in cluster given from R' + \
                     str(reactorno)+loop+'Control_status.vi'
                continue
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
                    setattr(F
                            , name, IntegerField(name))
            # Assign form to appropriate location in form dictionary
            form_dict[loop][action] = F(prefix=prefix)
    return form_dict, current, loops


def build_ise_control_forms(ip, port, reactorno, ise):
    """
    Programatically build dict of dict of forms for the remote control panel
    :param reactorno: int, given reactor number to build forms for
    :return:
    """
    print('Building ISE Form')
    param_dict = isehnd.get_ise_setparams(ip, port, reactorno, ise)
    form_dict = {}
    # Loop through all given control loops and manual/setparams/switch actions
    for each in param_dict:
        class F(Form):
            pass
        # Name the form prefix after the parameter set category
        prefix = each
        for param in param_dict[each]:
            # Loop through 'commands' for given loop and action.
            # i.e. ph_manual -> acid pump & base pump
            # i.e. do_set params -> do set pt, n2 gain, etc. etc.
            name = param[0].replace('?', '')
            default = param[1]
            field_type = type(default)
            # Use data type of command to determine field
            # i.e. boolean -> checkbox, float -> double
            if field_type is bool or None: # Default value assigned w/ jquery
                # It it's ternary controlled, also make it a boolean Field
                setattr(F, name, BooleanField(name))
            if field_type is float:
                setattr(F, name, FloatField(name))
            if field_type is str:
                setattr(F, name, StringField(name))
            if field_type is int:
                setattr(F, name, IntegerField(name))
        # Assign form to appropriate location in form dictionary
        form_dict[each] = F(prefix=prefix)
    return form_dict, param_dict
