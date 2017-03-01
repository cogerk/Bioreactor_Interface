"""
Supporting utility functions for remotecontrol panel
Written By: Kathryn Cogert
Jan 25 2017
"""

# >Define Constants
# List of actions you can take on a control Loop
ACTIONS = ['Switch',  # Switch control loop on or off
           'Status',  # Get status of control loop
           'Manual',  # Control Loop Actuators Manually
           'SetParams']  # Set control loop parameters, i.e. gain, set pt, etc.

# List of types of on/off actuators that require boolean inputs
BOOL_ACTS = ['Pump', 'Valve', 'Switch']


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


def convert_to_datatype(xmlarray):
    """
    Take name/value pair in XML tree and convert to boolean if on/off actuator
    :param xmlarray: array of xml elements, name/value pair
    :return: bool or float, converted value (if conversion was required)
    """
    try:
        value = float(xmlarray[1].text)
        for actuator in BOOL_ACTS:
            if actuator in xmlarray[0].text:
                value = bool(value)
    except:
        value = xmlarray[1].text
    return value


def convert_to_localvar(labelstr):
    """
    Remove spaces and units from parameter labels for submission to the cRIO
    :param labelstr:
    :return:
    """
    labelstr = labelstr.split(',')[0]
    varstr = labelstr.replace(' ', '')
    return varstr


