"""
Code to dynamically generate a GET request to control a reactor
Written By: Kathryn Cogert
Jan 25 2017
"""

# TODO: cRIO side- Preface w/ Reactor No?
# TODO: cRIO side- multiply delay by 1000 in labview
# TODO: cRIO side- switch to _Status
import customerrs as cust


def build_url(ip, port, reactorno, loop, action, values=[]):
    if loop not in cust.LOOPS.keys():
        raise cust.InvalidAction
    else:
        r_name = 'R'+str(reactorno)
        vi_to_run = r_name+loop+'Control_'+action
        if action not in cust.ACTIONS.keys():
            raise cust.InvalidAction
        elif action is 'Manual':
            params = cust.LOOPS[loop][0]
        elif action is 'SetParams':
            params = cust.LOOPS[loop][1]
        elif action is 'Switch':
            params=[loop+'ControlOn']
        else:
            params = []
        if len(params) is not len(values):
            raise cust.InvalidValue
        # TODO: Do values match types?
        else:
            command = '?'
            for idx, param in enumerate(params):
                print(type(values[idx]))
                if type(values[idx]) is bool:
                    values[idx] = str(int(values[idx]))
                command = command + param + '=' + str(values[idx]) +'&'
            command = command[:-1]
    # TODO: cRIO side- All reactor references to R1 instead of reactor 1
    webservice = 'Reactor'+str(reactorno)+'_Webservice'
    url = 'http://'+ip+':'+str(port)+'/'+webservice+'/'+vi_to_run+command
    return url

# test = build_url('128.208.236.57', 8001, 1, 'pH', 'Status')
