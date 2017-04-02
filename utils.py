"""
Supporting utility functions for remote control panel
Written By: Kathryn Cogert
Jan 25 2017
"""
from __init__ import models
import customerrs

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
         'Lead': 'Pb' }

# List of types of on/off actuators that require boolean inputs
BOOL_ACTS = ['Pump', 'Valve', 'Switch', 'On', '?']

TRI_ACTS =['Steady State?', 'SteadyState?']

# >Utility Functions
def build_url(ip, port, reactorno, vi_to_run, command=''):
    """
    Builds a GET request url that the cRIO will understand
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :param vi_to_run: str, the name of the vi in the cRIO webservice
    :param command: str, the command to pass to the GET request
    :return:
    """
    r_name = 'R'+str(reactorno)
    url = 'http://'+ip+':'+str(port)+'/'+r_name+'/'+vi_to_run+command
    return url


def get_controller_info(reactorno, debug=False):
    reactor = models.Reactor.query.filter_by(idx=reactorno).first()
    ip = reactor.controller.ip
    if debug:
        port = reactor.controller.debug_port
    else:
        port = reactor.controller.port
    return ip, port


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

    name = convert_to_localvar(xmlarray[0].text)
    for actuator in TRI_ACTS:
        if actuator == name[len(name) - len(actuator):len(name)]:
            if value in [0, 1]:
                value = bool(value)
            else:
                value = None
            return value
    for actuator in BOOL_ACTS:
        if actuator == name[len(name)-len(actuator):len(name)]:
            if value in [0, 1]:
                value = bool(value)
            else:
                raise customerrs.NonBoolean
            return value
    return value