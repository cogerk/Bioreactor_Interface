"""
Supporting utility to get reactor control loops, signals, & constants
Written By: Kathryn Cogert
Feb 27 2017
"""
import urllib.request
from xml.etree import ElementTree
from utils import build_url


def get_signals(ip, port, reactorno):
    """
    Get all signals in an element tree
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :return: element tree of signal data
    """
    signal_vi = 'R'+str(reactorno)+'GetSignals'
    signal_url = build_url(ip, port, reactorno, signal_vi)
    result = urllib.request.urlopen(signal_url).read()
    root = ElementTree.fromstring(result)
    return root[0][1]


def get_signal_list(ip, port, reactorno):
    """
    Gets a list of names of all calibratable signals in a reactor
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :return: list of calibratable signals in reactor
    """
    signals = get_signals(ip, port, reactorno)
    signal_ele_tree = signals.findall('Name')
    signal_list = []
    for signal in signal_ele_tree:
        if 'VFD' in signal.text:
           signal_list.append(signal.text+ ' RPM')
           signal_list.append(signal.text+ ' Signal')
        else:
            signal_list.append(signal.text)
    return signal_list


def get_loops(ip, port, reactorno):
    """
    Gets a list of names of all calibratable signals in a reactor
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :return: list of control loops in reactor
    """
    loops_vi = 'R'+str(reactorno)+'GetLoops'
    loops_url = build_url(ip, port, reactorno, loops_vi)
    result = urllib.request.urlopen(loops_url).read()
    root = ElementTree.fromstring(result)
    loops =[]
    for loop in root[0][1].findall('Value'):
        loops.append(loop.text)
    return loops


def get_other_constants(ip, port, reactorno):
    """
    Gets a list of names of other reactor specific constants
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :return: list of other constants
    """
    # TODO: Constant vs. dynamic control of Na+ correction
    other_vi = 'R'+str(reactorno)+'GetOtherConstants'
    other_url = build_url(ip, port, reactorno, other_vi)
    result = urllib.request.urlopen(other_url).read()
    root = ElementTree.fromstring(result)
    other = []
    for constant in root[0][1].findall('Value'):
        other.append(constant.text)
    return other


def get_phases(ip, port, reactorno):
    """
    Given a reactor get list of SBR phases.
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :return: List of phases in SBR cycle
    """
    sbr_vi = 'R'+str(reactorno)+'SBRControl_Status'
    sbr_url = build_url(ip, port, reactorno, sbr_vi)
    result = urllib.request.urlopen(sbr_url).read()
    root = ElementTree.fromstring(result)
    sbr_phases = []
    for terminal in root:
        if terminal.find('Name').text == 'SBRData':
            names = terminal.find('Value').findall('Name')
            vals = terminal.find('Value').findall('Value')
            break
    data = list(zip(names, vals))
    for category in data:
        phase_tree = []
        if category[0].text == 'SBR_SetParams':
            phase_tree = category[1].findall('Value')
            sbr_phases = []
            for pair in phase_tree:
                names = pair.findall('Name')
                vals = pair.findall('Value')
                phase_info = list(zip(names, vals))
                for each in phase_info:
                    if each[0].text == 'Phase':
                         sbr_phases.append(each[1].text)
            break
    return sbr_phases
