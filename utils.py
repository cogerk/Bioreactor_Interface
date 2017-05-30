"""
Supporting utility functions for remote control panel
Written By: Kathryn Cogert
Jan 25 2017
"""
import customerrs

# User will need to ensure that they have the right variable library structure, especially for calibration constants.
#b/c you will need ni.var.psp://cRIO#-WinklerLab/R#Variables/R#CalibrationConstants in calibration constant assignment VI
# TODO: debug Sending cRIO# and Reactor Number to calibration constant setting guy
# >Define Constants
# List of actions you can take on a control Loop
ACTIONS = ['Switch',  # Switch control loop on or off
           'Status',  # Get status of control loop
           'Manual',  # Control Loop Actuators Manually
           'SetParams']  # Set control loop parameters, i.e. gain, set pt, etc.

# ISE Parameter Rules
ISE_RULES = {'Equilibrium': 'Eq',
             'Detection': 'Detect',
             'On?': 'On',
             'Set Point': 'Set',
             'Time': 'Time',
             'Assumed': '',
             'Correction Factor': 'CF',
             'Concentration': 'Conc'}

# TODO: Can I use this?
# Chemical Compounds
CHEMS = {'Sodium': 'Na',
         'Potassium': 'K',
         'Phosphate': 'NH4',
         'Bromide': 'Br',
         'Copper': 'Cu',
         'Mercury': 'Hg',
         'Silver': 'Ag',
         'Cyanide': 'CN',
         'Nitrate': 'NO3',
         'Nitrite': 'NO2',
         'Cadmium': 'Cd',
         'Fluoride': 'Fl',
         'Sulphide': 'S',
         'Calcium': 'Ca',
         'Iodide': 'I',
         'Perchlorate': 'CLO4',
         'Thiocyanate': 'SCN',
         'Chloride': 'Cl',
         'Lead': 'Pb'}

# List of types of on/off actuators that require boolean inputs
BOOL_ACTS = ['Pump', 'Valve', 'Switch', 'On', '?']

TRI_ACTS = ['Steady State?', 'SteadyState?']


# >Utility Functions


def convert_to_localvar(labelstr):
    """
    Remove spaces and units from parameter labels for submission to the cRIO
    :param labelstr:
    :return:
    """
    labelstr = labelstr.split(',')[0]
    varstr = labelstr.replace(' ', '')
    return varstr


def convert_to_datatype(xmlarray):
    """
    Take name/value pair in XML tree and convert to boolean if on/off actuator
    :param xmlarray: array of xml elements, name/value pair
    :return: bool or float, converted value (if conversion was required)
    """
    try:
        value = float(xmlarray[1].text)
    except ValueError:
        value = xmlarray[1].text
    # TODO: Get rid of GetOtherConstants and instead use cRIO umber
    name = convert_to_localvar(xmlarray[0].text)
    for actuator in TRI_ACTS:
        if actuator == name[len(name) - len(actuator):len(name)]:
            if value in [0, 1]:
                value = bool(value)
            else:
                value = None
            return value
    for actuator in BOOL_ACTS:
        # If this is a timer (i.e. pH control system, assign as float)
        if actuator + 'Time' in name:
            return value
        if actuator == name[len(name)-len(actuator):len(name)]:
            if value in [0, 1]:
                value = bool(value)
            else:
                raise customerrs.NonBoolean
            return value
    return value
