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


def get_submitted_vals(form):
    """
    Gets the submitted values sent via a post request
    :param form: form object, the submitted form via post request
    :return: dictionary of input names and defaults in get_inputs() format
    """
    commands_forms_dict = {}
    for idx, entry in enumerate(form):
        if idx == 0:
            loop = entry[0:entry.index('_')]
            action = entry[entry.index('_')+1:entry.index('-')]
            all_commands_dict = get_inputs(loop, action)
        if 'submit' not in entry and 'csrf_token' not in entry:
            command = entry[entry.index('-')+1:]
            commands_forms_dict[command] = form[entry]
    for each in commands_forms_dict:
        if type(all_commands_dict[each]) == bool:
            if each not in all_commands_dict:
                all_commands_dict[each] = False
            else:
                all_commands_dict[each] = True
        if type(all_commands_dict[each]) == list:
            all_commands_dict[each] = commands_forms_dict[each]
        else:
            all_commands_dict[each] = all_commands_dict[each]
    return loop, action, all_commands_dict


def build_url(ip, port, reactorno, loop, action, params={}):
    """
    Builds a get url request to send to the reactor
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :param loop: str, Control loop requested
    :param action: str, Switch, Manual, or SetParams (for automated control)
    :param params: dict, parameters to submit to reactor in get_inputs() format
    :return: str, the get URL
    """
    if loop not in cust.loopdict.keys():
        raise cust.InvalidAction
    else:
        r_name = 'R'+str(reactorno)
        vi_to_run = r_name+loop+'Control_'+action
        if action not in cust.ACTIONS:
            raise cust.InvalidAction
        else:
            default_params = cust.loopdict[loop][action]
        command = '?'
        if params:
            if len(default_params) is not len(params):
                raise cust.InvalidValue('Expected '+str(len(default_params)) +
                                        ' inputs but got '+str(len(params)))
            for idx, each in enumerate(default_params):
                if isinstance(params[each], type(default_params[each])):
                    if type(params[each]) is bool:
                        val = int(params[each])
                    else:
                        val = params[each]
                    command = command + each + '=' + str(val) + '&'
                else:
                    raise cust.InvalidValue('Expected ' + each +
                                            ' to be datatype ' +
                                            type(default_params[each]) +
                                            ' got ' +
                                            type(params[each]))

        command = command[:-1]
    url = 'http://'+ip+':'+str(port)+'/'+r_name+'/'+vi_to_run+command
    return url


def submit_to_reactor(ip, port, reactorno, submitted_form):
    """
    Submits get request to reactor and returns status
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :param submitted_form: obj, the form given from the POST request.
    :return: str, the
    """
    [loop, action, params] = get_submitted_vals(submitted_form)
    get_url = build_url(ip, port, reactorno, loop, action, params)
    print(get_url)
    result = urllib.request.urlopen(get_url).read()
    root = ElementTree.fromstring(result)
    status = 'No Command Submitted'
    for terminal in root:
        if terminal.find('Name').text == 'ControlStatus':
            status = terminal.find('Value').text
    return status

def get_current_vals(ip, port, reactorno, loop):
    get_url = build_url(ip, port, reactorno, loop, 'Status')
    print(get_url)
    result = urllib.request.urlopen(get_url).read()
    return result


ip = '128.208.236.57'
port = 8001
print(get_current_vals(ip, port, 1, 'pH'))
