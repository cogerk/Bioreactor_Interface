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
import reactorhandler as rctr


def get_submitted(form, current):
    """
    Gets the submitted values sent via a post request and store in dictionary
    :param form: form object, the submitted form via post request
    :return: dict/bool, dictionary of input names and defaults in get_inputs()
        format/if loop switch just a bool
    """

    commands_dict = {}  # Initialize the command dictionary
    for idx, entry in enumerate(form):
        # Get loop and action and command dict of defaults from form prefix
        # default dict will be written over with the submitted commands
        if idx == 0:
            loop = entry[0:entry.index('_')]
            action = entry[entry.index('_')+1:entry.index('-')]
            all_commands_dict = current[loop][loop+'_'+action]
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
    if action == 'Switch':  # If switch, only expecting one parameter, no dict
        if 'control_on' in commands_dict:
            all_commands_dict = True
        else:
            all_commands_dict = False
        return loop, action, all_commands_dict
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
    :param action: str, Status, Switch, Manual, or SetParams (for auto control)
    :param params: dict, parameters to submit to reactor in get_inputs() format
    :return: str or array of str, the get URL(s), plural if loop is SBR
    """
    r_name = 'R'+str(reactorno)  # VIs are prefaced with R#
    vi_to_run = r_name+loop+'Control_'+action  # Builds the name of VI
    if action not in utils.ACTIONS:
        # If action is not in list ACTIONS, throw error
        raise cust.InvalidAction
    command = '?'  # All command strings are prefaced w/ ? in the URL
    # If status, command will be blank string
    if action == 'Switch': # If switch mode, build command and exit func
       command = command+'control_on=' + str(int(params))
       return vi_to_run, command
    if action != 'Status':
        # SBR loop has special rules for cmd str b/c so many inputs
        if loop == 'SBR' and action != 'Switch':
            command = [command+'Label='] * len(params)
            for idx, each in enumerate(params):
                if type(params[each]) is bool:
                        # URL requires booleans to be 1 or 0 not True/False
                        params[each] = int(params[each])
                command[idx] += each+'&ToWrite='+str(params[each])
                # Replace all spaces with %20 so it makes sense as a URL
                command[idx] = command[idx].replace(' ', '%20')
        else:
            for idx, each in enumerate(params):
                if type(params[each]) is bool:
                    # URL requires booleans to be 1 or 0 not True/False
                    val = int(params[each])
                else:
                    val = params[each]
                # Convert command to something cRIO will know and append.
                each = utils.convert_to_localvar(each)
                command = command + each + '=' + str(val) + '&'
                # Replace all spaces with %20 so that it makes sense as URL
                command = command.replace(' ', '%20')
            command = command[:-1]  # get rid of last & in command
    else:
        command = command[:-1]  # get rid of last ? in command if status
    return vi_to_run, command


def submit_to_reactor(ip, port, reactorno, loop, action, params=None):
    """
    Submits new control command as a POST request to reactor and returns status
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :param submitted_form: obj, the form given from the POST request.
    :return: str, the
    """
    # Translate to vi name & command string that cRIO can read
    [vi, cmdstrs] = translate_to_ws(reactorno, loop, action, params)
    # Build the URL to send & send it
    if action != 'Status':
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
                # For SBR see if all vals got written, but only return one stat
                for terminal in root:
                    if terminal.find('Name').text == 'ControlStatus':
                        status = terminal.find('Value').text
                if idx is 0:
                    statuslast = status
                else: # If the status differs from the last stop writing
                    if statuslast != status:
                        status = 'Not all Commands Written: ' + status
                        break
                    else:
                        statuslast = status
    else:
        get_url = utils.build_url(ip, port, reactorno, vi, cmdstrs)
        result = urllib.request.urlopen(get_url).read()
        root = ElementTree.fromstring(result)
        status = {}
        # Convert XML into dict of dicts
        names = []
        vals = []
        for terminal in root:
            if terminal.find('Name').text == loop+'Data':
                names = terminal.find('Value').findall('Name')
                vals = terminal.find('Value').findall('Value')
                break
        data = list(zip(names, vals))
        for each in data:
            if each[1].text:
                value = utils.convert_to_datatype(each)
                status[each[0].text] = value
            else:
                status[each[0].text] = {}
                names2 = each[1].findall('Name')
                vals2 = each[1].findall('Value')
                data2 = list(zip(names2, vals2))
                for each2 in data2:
                    # Special rules for SBR control parameters
                    if each2[0].text == 'Phase Timing Pairs':
                        phase_pair = [x.text for x in each2[1].findall('Value')]
                        phase_pair[1] = int(phase_pair[1])
                        phase_pair = tuple(phase_pair)
                        if status[each[0].text] == {}:
                            status[each[0].text] = [phase_pair]
                        else:
                            temp = status[each[0].text]
                            temp.append(phase_pair)
                            status[each[0].text] = temp
                    else:
                        value = utils.convert_to_datatype(each2)
                        if status[each[0].text] == {}:
                            status[each[0].text] = [(each2[0].text, value)]
                        else:
                            temp = status[each[0].text]
                            temp.append((each2[0].text, value))
                            status[each[0].text] = temp
    return status


def get_current(ip, port, reactorno):
    """
    Loops through reactor signals and return current slopes/ints in two dicts
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :return: dict of slopes, dict of intercepts
    """
    current = {}
    loop_list = rctr.get_loops(ip, port, reactorno)
    for loop in loop_list:
        current[loop] = submit_to_reactor(ip, port, reactorno, loop, 'Status')
    return current, loop_list


