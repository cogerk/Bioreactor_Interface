"""
Functions to accept form submitted from /CalConstant page,
translate to commands that the webservice will understand,
passing those commands to the cRIO,
and reading current calibration constants into a dictionary
Written By: Kathryn Cogert
Feb 1 2017
"""
import urllib.request
from xml.etree import ElementTree

import dbhandler
import utils
import reactorhandler as rctr

def get_submitted(form):
    """
    Gets the submitted values sent via a post request and store in dictionary
    :param form: form object, the submitted form via post request
    :return: dictionary of constant(s) and value(s)
    """
    loop = form.signal.data
    slope_int = [form.slope.data, form.intercept.data]
    return loop, slope_int


def translate_to_ws(reactorno,
                    crio,
                    signal,
                    to_write=None):
    """
    Translate singal, slope and intercept to VI and command strs to pass as GET
    :param reactorno: int, # of the reactor
    :param signal: str, the name of the signal to affected
    :param to_write: float list, [Slope, Intercept], if None, read mode
    :return: str, array of str, vi name and cmd string cRIO will understand
        Array of strings is [GET Request for slope, GET request for intercept]
    """
    # To eventually append to command strings
    r_name = 'R'+str(reactorno)
    vi_name = r_name + 'SetCalibrateConstant'
    # Both cmd strings will start wih
    cmd_str = ''
    cmd_str = cmd_str.join(['?ReactorNo=', str(reactorno),
                            '&cRIONo=', str(crio),
                            '&Signal=', signal,
                            '&Write='])
    cmd_str = cmd_str.replace(' ', '%20')
    # First iteration builds slope cmd string, second builds intercept cmd str
    if to_write is not None:  # Write Mode
        cmd_str += '1&Slope=' + str(to_write[0]) \
                   + '&Intercept=' + str(to_write[1])
    else:  # Read Mode
        cmd_str += '0'
    return vi_name, cmd_str


def submit_to_reactor(ip, port, crio, reactorno, signal, values):
    """
    Submits new constant as a POST request to reactor and returns status
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :param signal: str, the name of the signal to affected
    :param values: float list, [Slope, Intercept], if None, read mode
    :return: (float, float), slope & intercept.  If
    """
    # Translate to vi name & command string that cRIO can read
    vi, cmdstr = translate_to_ws(reactorno, crio, signal, values)
    # Statuses will start with this (if write mode)
    # Build the URL to send & send it
    get_url = utils.build_url(ip, port, reactorno, vi, cmdstr)
    result = urllib.request.urlopen(get_url).read()
    # Result is an XML tree, parse this to see if command was sent
    root = ElementTree.fromstring(result)
    status = [None, None]
    intercept = None
    slope = None
    for terminal in root:
        if 'Status' in terminal.find('Name').text:
            status_xml = terminal.find('Value')
            status_vals_xml = status_xml.findall('Value')
            for idx, each in enumerate(status_vals_xml):
                status[idx] = each.text
        if 'NewIntercept' in terminal.find('Name').text:
            intercept = terminal.find('Value').text
        if 'NewSlope' in terminal.find('Name').text:
            slope = terminal.find('Value').text
    # If command sent specified read mode, get the value returned
    if status[0] == status[-1]:
        status = [status[0]]
    return status, slope, intercept


def get_all_current(ip, port, crio, reactorno):
    """
    Loops through reactor signals and return current slopes/ints in two dicts
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :return: dict of slopes, dict of intercepts
    """
    all_slopes = {}
    all_ints = {}
    all_stats = {}
    signal_list = rctr.get_signal_list(ip, port, reactorno)
    for signal in signal_list:
        stats, slope, intercept = submit_to_reactor(ip,
                                                    port,
                                                    crio,
                                                    reactorno,
                                                    signal, None)
        all_stats[signal] = stats
        all_slopes[signal] = slope
        all_ints[signal] = intercept
    return signal_list, all_slopes, all_ints, all_stats


