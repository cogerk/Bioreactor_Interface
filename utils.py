"""
Supporting utility functions for remotecontrol panel
Written By: Kathryn Cogert
Jan 25 2017
"""
import customerrs as cust


def get_inputs(loop, action):
    """
    Gets the defatult inputs of a given control loop and action
    :param loop: str, Control loop requested
    :param action: str, Switch, Manual, or SetParams (for automated control)
    :return: dictionary of input names and their default values
    """
    return cust.loopdict[loop][action]


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
