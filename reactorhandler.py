"""
Supporting utility to get reactor control loops, signals, & constants from rct
Written By: Kathryn Cogert
Feb 27 2017
"""
# TODO: Refresh loops options
import dateutil.parser
import warnings

from datetime import datetime

import customerrs
from utils import call_reactor
from rutils import build_url, call_reactor


def get_probe_snap(ip, port, reactorno):
    signals = get_signals(ip, port, reactorno)
    if signals is None:
        return None
    signal_ele_tree = list(zip(signals.findall('Name'),
                               signals.findall('Value')))
    data = {}
    units = {}
    for signal in signal_ele_tree:
        if 'Timestamp' in signal[0].text:
            stamp = dateutil.parser.parse(signal[1].text)
            data[signal[0].text] = stamp
        elif 'Reactor Status' in signal[0].text:
            data[signal[0].text] = signal[1].text
        else:
            signal_val_tree = list(zip(signal[1].findall('Name'),
                                   signal[1].findall('Value')))
            for sig_val in signal_val_tree:
                if 'VFD' in signal[0].text or 'Flowrate' in signal[0].text:
                    pass
                elif 'ISE' in signal[0].text:
                    if 'Corrected Value' in sig_val[0].text:
                        data[signal[0].text] = sig_val[1].text
                        un = sig_val[0].text.split(', ')
                        units[signal[0].text] = un[1]
                else:
                    if 'Value' in sig_val[0].text:
                        data[signal[0].text] = sig_val[1].text
                        un = sig_val[0].text.split(', ')
                        if len(un) == 1:
                            units[signal[0].text] = ''
                        else:
                            units[signal[0].text] = un[1]
    if data == {}:
        currenttime = str(datetime.now())
        warnstr = 'At' + \
                  currenttime + \
                  'data from Reactor #' + \
                  reactorno + \
                  'could not be collected.'
        warnings.warn(warnstr, customerrs.DataNotCollected)
    return data, units


def get_signal_snap(ip, port, reactorno):
    signals = get_signals(ip, port, reactorno)
    signal_ele_tree = list(zip(signals.findall('Name'),
                               signals.findall('Value')))
    data = {}
    units = {}

    for signal in signal_ele_tree:
        if 'Timestamp' in signal[0].text:
            stamp = dateutil.parser.parse(signal[1].text)
            data[signal[0].text] = stamp
        elif 'Reactor Status' in signal[0].text:
            data[signal[0].text] = signal[1].text
        else:
            signal_val_tree = list(zip(signal[1].findall('Name'),
                                   signal[1].findall('Value')))
            for sig_val in signal_val_tree:
                if 'VFD' in signal[0].text:
                    if 'Flowrate' in sig_val[0].text:
                        data[signal[0].text+' Flowrate'] = sig_val[1].text
                        un = sig_val[0].text.split(', ')
                        units[signal[0].text+' Flowrate'] = un[1]
                else:
                    # User needs to format signals in get signals cluster as Cluster(Signal Name: [Signal, mA], [Value, units]) otherwise no units will be detected
                    if 'Signal' in sig_val[0].text:
                        data[signal[0].text] = sig_val[1].text
                        un = sig_val[0].text.split(', ')
                        try:
                            units[signal[0].text] = un[1]
                        except IndexError:
                            units[signal[0].text] = None
    if data == {}:
        currenttime = str(datetime.now())
        warnstr = 'At' + \
                  currenttime + \
                  'data from Reactor #' + \
                  reactorno + \
                  'could not be collected.'
        warnings.warn(warnstr, customerrs.DataNotCollected)
    return data, units


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
    root = call_reactor(ip, port, reactorno, signal_url)
    signals = root[0][1]
    return signals


def get_signal_list(ip, port, reactorno):
    """
    Gets a list of names of all calibratable signals in a reactor
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :return: list of calibratable signals in reactor
    """
    signals = get_signals(ip, port, reactorno)
    if signals is None:
        return []
    signal_ele_tree = signals.findall('Name')
    signal_list = []
    for signal in signal_ele_tree:
        if 'Timestamp' in signal.text or 'Reactor Status' in signal.text:
            continue
        if 'VFD' in signal.text:
            signal_list.append(signal.text + ' RPM')
            signal_list.append(signal.text + ' Signal')
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
    root = call_reactor(ip, port, reactorno, loops_url)
    loops =[]
    for loop in root[0][1].findall('Value'):
        loops.append(loop.text)
    # Filter out any None values
    loops = [x for x in loops if x is not None]
    return loops

def get_other_constants(ip, port, crio, reactorno):
    """
    Gets a list of names of other reactor specific constants
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :return: list of other constants
    """
    other_vi = 'R'+str(reactorno)+'GetOtherConstants'
    other_cmd = '?cRIONo=' + str(crio) + '&ReactorNo=' + str(reactorno)
    other_url = build_url(ip, port, reactorno, other_vi, other_cmd)
    root = call_reactor(ip, port, reactorno, other_url)
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
    root = call_reactor(ip, port, reactorno, sbr_url)
    sbr_phases = []
    names = []
    vals = []
    for terminal in root:
        if terminal.find('Name').text == 'SBRData':
            names = terminal.find('Value').findall('Name')
            vals = terminal.find('Value').findall('Value')
            break
        else:
            continue
    data = list(zip(names, vals))
    for category in data:
        if category[0].text == 'SBR_SetParams':
            phase_tree = category[1].findall('Value')
            sbr_phases = []
            for pair in phase_tree:
                names = pair.findall('Name')
                vals = pair.findall('Value')
                phase_info = list(zip(names, vals))
                phase_name, time, units = '', 0, ''
                for each in phase_info:
                    if each[0].text == 'Phase':
                        phase_name = each[1].text
                    if 'Time' in each[0].text:
                        time = float(each[1].text)
                        try:
                            units = ', ' + each[0].text.split(', ')[1]
                        except IndexError:
                            units = ', '
                sbr_phases.append((phase_name + units, [time]))
            break
    return sbr_phases
