"""
Functions to accept form submitted from /CalConstant page,
translate to commands that the webservice will understand,
passing those commands to the cRIO,
and reading current calibration constants into a dictionary <Todo
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
    :param reactorno: int, # of the reactor
    :param form: form object, the submitted form via post request
    :return: dictionary of constant(s) and value(s)
    """
    loop = form.signal.data
    slope_int = [form.slope.data, form.intercept.data]
    return loop, slope_int


def translate_to_ws(reactorno,
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
    slopeint_strs = ['%20Slope', '%20Intercept']
    r_name = 'R'+str(reactorno)
    vi_name = r_name + 'SetCalibrateConstant'
    # Both cmd strings will start wih
    cmd_strs = ['?Constant=' + r_name + '%20' + signal] * 2
    # First iteration builds slope cmd string, second builds intercept cmd str
    for idx, strs in enumerate(cmd_strs):
        strs += slopeint_strs[idx] + '&Write='
        if to_write is not None:  # Write Mode
            strs += '1&ToWrite=' + str(to_write[idx])
        else:  # Read Mode
            strs += '0&ToWrite=0'
        cmd_strs[idx] = strs
    return vi_name, cmd_strs


def submit_to_reactor(ip, port, reactorno, signal, values):
    """
    Submits new constant as a POST request to reactor and returns status
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :param signal: str, the name of the signal to affected
    :param to_write: float list, [Slope, Intercept], if None, read mode
    :return: array of str/int, return status from cRIO/if read mode return vals
    """
    # Translate to vi name & command string that cRIO can read
    [vi, cmdstrs] = translate_to_ws(reactorno,
                                    signal,
                                    values)
    # Statuses will start with this (if write mode)
    statuses = ['Slope: ', 'Intercept: ']
    # First iteration sends slope command, second intercept command
    for idx, cmd in enumerate(cmdstrs):
        # Build the URL to send & send it
        get_url = utils.build_url(ip, port, reactorno, vi, cmd)
        result = urllib.request.urlopen(get_url).read()
        # Result is an XML tree, parse this to see if command was sent
        root = ElementTree.fromstring(result)
        status = 'No Command Submitted'
        for terminal in root:
            if terminal.find('Name').text == 'ControlStatus':
                status = terminal.find('Value').text  # Returns status
        # If command sent specified read mode, get the value returned
        if status == 'Read Mode':
            for terminal in root:
                status = terminal.find('Value').text
            statuses[idx] = status  # Replace existing string in read mode
        else:
            statuses[idx] += status  # Append tostring above in write mode
    return statuses


def get_all_current(ip, port, reactorno):
    """
    Loops through reactor signals and return current slopes/ints in two dicts
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :return: dict of slopes, dict of intercepts
    """
    all_slopes = {}
    all_ints = {}
    for signal in cust.SIGNALS:
        vals = submit_to_reactor(ip, port, reactorno, signal[0], None)
        all_slopes[signal[0]] = vals[0]
        all_ints[signal[0]] = vals[1]
    return all_slopes, all_ints
