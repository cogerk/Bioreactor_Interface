import http.client
import urllib.error
import urllib.request
from xml.etree import ElementTree

import customerrs
import models


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
    print(url)
    return url


def call_reactor(ip, port, reactorno, url, status=False):
    """

    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :param url: str, url to be requested
    :param status: if just reading status, this is True
    :return:
    """
    try:
        result = urllib.request.urlopen(url).read()
        root = ElementTree.fromstring(result)
        return root
    except urllib.error.HTTPError:
        if status:
            raise customerrs.UnfoundStatus('Could not access ' + url)
        else:
            raise customerrs.CannotReachReactor(
                'While attempting to access ' + url +
                ', cannot find Reactor #' + str(reactorno))
    except urllib.error.URLError:
        raise customerrs.CannotReachReactor(
            'While attempting to access ' + url +
            'cRIO could not be found at' + str(ip) + ':' + str(port))
    except http.client.RemoteDisconnected:
        raise customerrs.CannotReachReactor(
            'While attempting to access ' + url +
            'cRIO disconnected during query IP:' + str(ip) + ':' + str(port))


def get_controller_info(reactorno, debug=False, crio=False):
    reactor = models.Reactor.query.filter_by(idx=reactorno).first()
    ip = reactor.controller.ip
    # If debug mode, return debug port. Else, return application port.
    if debug:
        port = reactor.controller.debug_port
    else:
        port = reactor.controller.port
    # If requested crio ID return that.
    if crio:
        crio = reactor.controller.idx
        return ip, port, crio
    else:
        return ip, port