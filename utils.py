"""
Supporting utility functions for remotecontrol panel
Written By: Kathryn Cogert
Jan 25 2017
"""
import urllib.request
import customerrs as cust
from xml.etree import ElementTree


def get_inputs(loop, action):
    """
    Gets the defatult inputs of a given control loop and action
    :param loop: str, Control loop requested
    :param action: str, Switch, Manual, or SetParams (for automated control)
    :return: dictionary of input names and their default values
    """
    return cust.loopdict[loop][action]


def get_submitted_commands(form):
    """
    Gets the submitted values sent via a post request and store in dictionary
    :param form: form object, the submitted form via post request
    :return: dictionary of input names and defaults in get_inputs() format
    """
    commands_dict = {}  # Initialize the command dictionary
    for idx, entry in enumerate(form):
        # Get loop and action and command dict of defaults from form prefix
        # default dict will be written over with the submitted commands
        if idx == 0:
            loop = entry[0:entry.index('_')]
            action = entry[entry.index('_')+1:entry.index('-')]
            all_commands_dict = get_inputs(loop, action)
        if 'submit' not in entry and 'csrf_token' not in entry:
            # Store each command in a seperate command dictionary
            command = entry[entry.index('-')+1:]
            commands_dict[command] = form[entry]
    for each in all_commands_dict:
        # Checkboxes don't get passed to form if unchecked, therefore if a
        # boolean input is expected check to see if that input was submitted w/
        # the form. If it isn't, set that input as false. Else, set it as true.
        if type(all_commands_dict[each]) == bool:
            if each not in commands_dict:
                all_commands_dict[each] = False
            else:
                all_commands_dict[each] = True
        else:
            all_commands_dict[each] = commands_dict[each]
    return loop, action, all_commands_dict


def translate_commands_to_ws(reactorno, loop, action, params={}):
    """
    Translates control loop command to VI name and command str to pass as GET
    A VI is a labview script that exists in a labview webservice (ws) on cRIO
    :param reactorno: int, # of the reactor
    :param loop: str, Control loop requested
    :param action: str, Switch, Manual, or SetParams (for automated control)
    :param params: dict, parameters to submit to reactor in get_inputs() format
    :return: str, the get URL
    """
    # If reactor does not have loop, throw error
    if loop not in cust.loopdict.keys():
        raise cust.InvalidLoop
    else:
        r_name = 'R'+str(reactorno)  # VIs are prefaced with R#
        vi_to_run = r_name+loop+'Control_'+action  # Builds the name of VI
        if action not in cust.ACTIONS:
            # If action is not in list ACTIONS, throw error
            raise cust.InvalidAction
        else:
            # Start with a list of the default params for the action/loop
            default_params = cust.loopdict[loop][action]
        command = '?'  # All command strings are prefaced w/ ? in the URL
        if params:
            # Error if not enough/too many parameters passed for loop/action
            if len(default_params) is not len(params):
                raise cust.InvalidValue('Expected '+str(len(default_params)) +
                                        ' inputs but got '+str(len(params)))
            for idx, each in enumerate(default_params):
                # Loop throw the deftauls
                if isinstance(params[each], type(default_params[each])):
                    if type(params[each]) is bool:
                        # URL requires booleans to be 1 or 0 not True/False
                        val = int(params[each])
                    else:
                        val = params[each]
                    # Append command to comand string
                    command = command + each + '=' + str(val) + '&'
                else:
                    # Error if params are not the same type as default
                    raise cust.InvalidValue('Expected ' + each +
                                            ' to be datatype ' +
                                            type(default_params[each]) +
                                            ' got ' +
                                            type(params[each]))
        command = command[:-1]  # get rid of last & in command string
    return vi_to_run, command


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


def submit_command_to_reactor(ip, port, reactorno, submitted_form):
    """
    Submits new control command as a POST request to reactor and returns status
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :param submitted_form: obj, the form given from the POST request.
    :return: str, the
    """
    [loop, action, params] = get_submitted_commands(submitted_form)
    [vi, cmdstr] = translate_commands_to_ws(reactorno,
                                            loop,
                                            action,
                                            params)
    get_url = build_url(ip, port, reactorno, vi, cmdstr)
    print(get_url)
    result = urllib.request.urlopen(get_url).read()
    root = ElementTree.fromstring(result)
    status = 'No Command Submitted'
    for terminal in root:
        if terminal.find('Name').text == 'ControlStatus':
            status = terminal.find('Value').text
    return status





"""
http://128.208.236.57:8001/R1/R1SetCalibrateConstant?ToWrite=1&Write=0&Constant=R1%20N2%20Slope
def get_current_vals(ip, port, reactorno, loop):
    get_url = build_url(ip, port, reactorno, loop, 'Status')
    print(get_url)
    result = urllib.request.urlopen(get_url).read()
    return result


ip = '128.208.236.57'
port = 8001
print(get_current_vals(ip, port, 1, 'pH'))
"""
