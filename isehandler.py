"""
Functions to accept send and receive information about the ISEs
Written By: Kathryn Cogert
Mar 21 2017
"""
import re
import urllib.request
import warnings
import dateutil.parser
from xml.etree import ElementTree
from datetime import datetime
from pytz import timezone

import rutils
import utils
import customerrs


def get_submitted(form, command_dict):
    """
    Gets the submitted values sent via a post request and store in dictionary
    :param form: form object, the submitted form via post request
    :param command_dict: dict, The previous ISE parameters
    :return: dict, the new parameters to send
    """
    submitted_param = []
    for idx, entry in enumerate(form):
        # Get name and previous info of the submitted form
        if idx == 0:
            submitted_form = entry[0:entry.index('-')]
            command_list = command_dict[submitted_form]
        submitted_param.append(entry[entry.index('-')+1:len(entry)])
    # Loop through previous info data types
    for command in command_list:
        # if boolean, check if present in form, if not submit false

        if type(command[1]) is bool:
            # Trim Questionmark
            command[1] = command[0][0:-1] in submitted_param
        else:
            # Assign form value to command list
            command[1] = form[submitted_form+'-'+command[0]]
    command_dict[submitted_form] = command_list
    return command_dict


def translate_to_ws(reactorno, ise, command_dict, write=True):
    """
    Translate ISE command dictionary to a vi and command for web service
    :param reactorno: int, reactor number
    :param ise: str, name of ise to send commands to
    :param command_dict: dict, commands to send
    :param write: bool, if true write mode
    :return:
    """
    vi = 'R'+str(reactorno)+ise+'ISE_SetParams'
    # turn write mode on or off
    command = '?Write=' + str(int(write))
    root = '&R' + str(reactorno) + 'ISE' + ise
    for form in command_dict:
        for each in command_dict[form]:
            # Use the ISE dict to translate name of input to local var
            each_no_units = each[0].split(',')[0]
            for rule in list(utils.ISE_RULES.keys()):
                if rule in each_no_units:
                    each_no_units = each_no_units.replace(rule,
                                                          utils.ISE_RULES[
                                                              rule])
            each_no_units = each_no_units.replace('Correction', '')
            for chem in list(utils.CHEMS.keys()):
                if chem in each_no_units:
                    each_no_units = each_no_units.replace(chem,
                                                          utils.CHEMS[chem])
            each_no_units = each_no_units.replace(' ', '')
            localvar = root + each_no_units + '='
            if type(each[1]) is bool:
                localvar += str(int(each[1]))
            else:
                localvar += str(each[1])
            command += localvar
    return vi, command


def send_to_reactor(ip, port, reactorno, ise, command_dict, write=True):
    """
    Send commands to reactor and get status back
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: Reactor class, # of the reactor & description
    :param ise: str, name of ise
    :param command_dict: dict, commands to send
    :param write: bool, if true write mode
    :return:
    """
    vi, command = translate_to_ws(reactorno, ise, command_dict, write)
    get_url = rutils.build_url(ip, port, reactorno, vi, command)
    result = urllib.request.urlopen(get_url).read()
    root = ElementTree.fromstring(result)
    status = 'No Command Submitted'
    for terminal in root:
        if terminal.find('Name').text == 'ControlStatus':
            status = terminal.find('Value').text  # Returns status
    # If command sent specified read mode, get the value of constant returned
    if status == 'Read Mode':
        for terminal in root:
            status = terminal.find('Value').text  # Returns value
    return status


def get_ise(ip, port, reactorno, ise):
    ise_vi = 'R'+str(reactorno) + ise + 'ISE_Status'
    ise_url = rutils.build_url(ip, port, reactorno, ise_vi)
    try:
        result = urllib.request.urlopen(ise_url).read()
        root = ElementTree.fromstring(result)
        ise_stat = root[0][1]
    except urllib.error.HTTPError:
        warnings.warn(
            'While searching for signals, cannot find Reactor #' +
            str(reactorno),
            customerrs.CannotReachController)
        ise_stat = None
    return ise_stat


def get_ise_setparams(ip, port, reactorno, ise):
    ise_data = get_ise(ip, port, reactorno, ise)
    ise_ele_tree = list(zip(ise_data.findall('Name'),
                            ise_data.findall('Value')))
    ise_setparams = {}
    searchstr = ise + '_ISE_(.+?)_SetParams'
    for each in ise_ele_tree:
        if 'SetParams' in each[0].text:
            if each[0].text == ise + '_ISE_SetParams':
                param_key = ise + ' ISE Parameters'
            else:
                try:
                    found = re.search(searchstr, each[0].text).group(1)
                    param_key = found + ' Parameters for ' + ise + ' ISE'
                except AttributeError:
                    param_key = 'Error Generating Name'
                    warnings.warn(customerrs.NotProperlyFormatted)

            setparams_ele_tree = list(zip(each[1].findall('Name'),
                                          each[1].findall('Value')))
            ise_setparams[param_key] = []
            for each2 in setparams_ele_tree:
                ise_setparams[param_key].append([each2[0].text,
                                                 utils.convert_to_datatype(
                                                     each2)])
    return ise_setparams


def get_ise_rel_sigs(ip, port, reactorno, ise, signal_list):
    ise_dict = get_ise_setparams(ip, port, reactorno, ise)
    sig_list = list(ise_dict.keys())
    ise_rel_sigs = [ise + ' ISE']
    for each in sig_list:
        if each != ise + ' ISE Parameters':
            isestr = each.split(' ')[0]
            if isestr + ' ISE' in signal_list:
                ise_rel_sigs.append(isestr + ' ISE')
            else:
                ise_rel_sigs.append(isestr)
    appname = '/R' + str(reactorno) + '_' + ise + '_ISE_rel_sigs'
    return appname, ise_rel_sigs


def get_ise_snap(ip, port, reactorno, ise):
    if ' ISE' in ise:
        ise = ise.replace(' ISE', '')
    ise_data = get_ise(ip, port, reactorno, ise)
    ise_ele_tree = list(zip(ise_data.findall('Name'),
                            ise_data.findall('Value')))
    data = {}
    units = {}
    for each in ise_ele_tree:
        if 'Timestamp' in each[0].text:
            stamp = dateutil.parser.parse(each[1].text)
            stamp = stamp.astimezone(timezone('US/Pacific'))
            data[each[0].text] = stamp
        elif '_Probe' in each[0].text:
            param_key = each[0].text.replace('_Probe', '')
            probe_ele_tree = list(zip(each[1].findall('Name'),
                                      each[1].findall('Value')))
            if len(probe_ele_tree) > 2:
                param_key += ' ISE '
            for each2 in probe_ele_tree:
                un = each2[0].text.split(', ')
                label = param_key + each2[0].text
                data[label] = (utils.convert_to_datatype(each2))
                try:
                    units[label] = un[1]
                except IndexError:
                    units[label] = ''

    return data, units