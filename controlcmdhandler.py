"""
Functions to accept form submitted from control panel page,
translate to commands that the webservice will understand,
passing those commands to the cRIO,
and reading current values into a dictionary
Written By: Kathryn Cogert
Feb 1 2017
"""
import urllib.request
from xml.etree import ElementTree
import utils
import customerrs as cust


def get_submitted(form):
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
            all_commands_dict = utils.get_inputs(loop, action)
        if 'submit' not in entry and 'csrf_token' not in entry:
            # Store each command in a seperate command dictionary
            command = entry[entry.index('-')+1:]
            commands_dict[command] = form[entry]
    # Special rules for SBR set params
    if isinstance(all_commands_dict, list):
        sbr_dict = {}
        for phase, length in all_commands_dict:
            sbr_dict.setdefault(phase, []).append(length)
        all_commands_dict = sbr_dict
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


def translate_to_ws(reactorno, loop, action, params=None):
    """
    Translates control loop command to VI name and command str to pass as GET
    A VI is a labview script that exists in a labview webservice (ws) on cRIO
    :param reactorno: int, # of the reactor
    :param loop: str, Control loop requested
    :param action: str, Status, Switch, Manual, or SetParams (for automated control)
    :param params: dict, parameters to submit to reactor in get_inputs() format
    :return: str or array of str, the get URL(s), plural if loop is SBR
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
        # If status, command will be blank string
        if action is not 'Status':
            # SBR loop has special rules for cmd str b/c so many inputs
            if loop == 'SBR' and action != 'Switch':
                command = [command+'Write=1'] * len(params)
                if action is 'Manual':
                    pump_or_phase = '&Pump='
                    com = '&CommandToPump=' #TODO: crio side - Make this smoother on cRIO side
                else:
                    pump_or_phase = '&Phase='
                    com = '&TimeToWrite='
                for idx, each in enumerate(params):
                    if type(params[each]) is bool:
                            # URL requires booleans to be 1 or 0 not True/False
                            params[each] = int(params[each])
                    command[idx] += pump_or_phase+each+com+str(params[each])
                    # Replace all spaces with %20 so that it makes sense as a URL
                    command[idx] = command[idx].replace(' ', '%20')
            else:
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
                    # Replace all spaces with %20 so that it makes sense as a URL
                    command = command.replace(' ', '%20')
                    command = command[:-1]  # get rid of last & in command string
        vi_to_run = vi_to_run.replace(' ', '%20')
    return vi_to_run, command


def submit_to_reactor(ip, port, reactorno, submitted_form):
    """
    Submits new control command as a POST request to reactor and returns status
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :param submitted_form: obj, the form given from the POST request.
    :return: str, the
    """
    # Translate to vi name & command string that cRIO can read
    [loop, action, params] = get_submitted(submitted_form)
    [vi, cmdstrs] = translate_to_ws(reactorno, loop, action, params)
    # Build the URL to send & send it
    if not isinstance(cmdstrs, list):
        get_url = utils.build_url(ip, port, reactorno, vi, cmdstrs)
        print(get_url)
        result = urllib.request.urlopen(get_url).read()
        root = ElementTree.fromstring(result)
        status = 'No Command Submitted'
        for terminal in root:
            if terminal.find('Name').text == 'ControlStatus':
                status = terminal.find('Value').text
    else:  # Special rules for SBR forms, loop through each param to submit
        for idx, cmd in enumerate(cmdstrs):
            get_url = utils.build_url(ip, port, reactorno, vi, cmd)
            print(get_url)
            result = urllib.request.urlopen(get_url).read()
            root = ElementTree.fromstring(result)
            status = 'No Command Submitted'
            # For SBR see if all values got written, but only return one status
            for terminal in root:
                if terminal.find('Name').text == 'ControlStatus':
                    status = terminal.find('Value').text
            if idx is 0:
                statuslast = status
            else: # If the status differs from the last, stop writing to cRIO
                if statuslast != status: # TODO: crio side, dbl check sbr manual mode control status writing
                    status = 'Not all Commands Written: ' + status
                    break
                else:
                    statuslast = status
    return status

"""
def get_all_current(ip, port, reactorno):

    Loops through reactor signals and return current slopes/ints in two dicts
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :return: dict of slopes, dict of intercepts

    all_slopes = {}
    all_ints = {}
    for signal in cust.SIGNALS:
        vals = submit_to_reactor(ip, port, reactorno, signal[0], None)
        all_slopes[signal[0]] = vals[0]
        all_ints[signal[0]] = vals[1]
    return all_slopes, all_ints
    """
