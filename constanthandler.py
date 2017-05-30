"""
Functions to accept form submitted from /Constant page,
translate to commands that the webservice will understand,
passing those commands to the cRIO,
and reading current calibration constants into a dictionary
Written By: Kathryn Cogert
Feb 1 2017
"""
import urllib.request
from xml.etree import ElementTree

import rutils
import utils
import reactorhandler as rctr


def get_submitted(form):
    """
    Gets the submitted values sent via a post request and store in dictionary
    :param reactorno: int, # of the reactor
    :param form: form object, the submitted form via post request
    :return: dictionary of constant(s) and value(s)
    """
    name = form.constant.data
    value = form.value.data
    return name, value


def translate_to_ws(crio,
                    reactorno,
                    name,
                    value=None):
    """
    Translate singal, slope and intercept to VI and command strs to pass as GET
    :param reactorno: int, # of the reactor
    :param name: str, name of the constant
    :param value: int, (optional) value to write to constant, if none read mode
    :return: name of the VI and command string that cRIO can understand
    """
    r_name = 'R'+str(reactorno)
    vi_name = r_name + 'SetOtherConstants'
    cmd_str = ''
    cmd_str = cmd_str.join(['?ReactorNo=', str(reactorno),
                            '&cRIONo=', str(crio),
                            '&Constant=', name,
                            '&Write='])
    if value is not None:
        cmd_str += '1&Value=' + str(value)
    else:
        cmd_str += '0'
    # Replace all spaces with %20 so that it makes sense as a URL
    vi_name = vi_name.replace(' ', '%20')
    cmd_str = cmd_str.replace(' ', '%20')
    return vi_name, cmd_str


def submit_to_reactor(ip, port, reactorno, crio, name, value=None):
    """
    Submits new constant as a POST request to reactor and returns status/values
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :param name: str, the name of the constant to write to
    :param value: float, value to write, if None, read mode
    :return: str/int, returns status back from cRIO/if read mode, returns vals
    """
    # Translate to vi name & command string that cRIO can read
    [vi, cmdstr] = translate_to_ws(crio,
                                   reactorno,
                                   name,
                                   value)
    # Build the URL to send & send it
    get_url = rutils.build_url(ip, port, reactorno, vi, cmdstr)
    print(get_url)
    result = urllib.request.urlopen(get_url).read()
    # Result is an XML tree, parse this to see if command was sent successfully
    root = ElementTree.fromstring(result)
    status = 'No Command Submitted'
    new_or_old = 'OldValue' if value is None else 'NewValue'
    for terminal in root:
        if terminal.find('Name').text == 'Status':
            status = terminal.find('Value').text  # Returns status
        if terminal.find('Name').text == new_or_old:
            value = terminal.find('Value').text
    return status, value


def get_all_current(ip, port, crio, reactorno):
    """
    Loops through all reactor's constants and returns current vals in dict
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :return: dict, dictionary of current values
    """
    all_current = {}
    constant_list = rctr.get_other_constants(ip, port, crio, reactorno)
    for const in constant_list:
        status, value = submit_to_reactor(ip,
                                          port,
                                          crio,
                                          reactorno,
                                          const,
                                          None)  # None means Read Mode
        all_current[const] = status, value
    return all_current
