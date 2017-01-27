"""
Code to dynamically generate a GET request to control a reactor
Written By: Kathryn Cogert
Jan 25 2017
"""

# TODO: cRIO side- Preface w/ Reactor No?
# TODO: cRIO side- multiply delay by 1000 in labview
# TODO: cRIO side- switch to _Status
# TODO: cRIO side- ditch the "write?" command in get requests
import customerrs as cust


def get_inputs(loop, action):
    return cust.loopdict[loop][action]



def get_submitted_vals(form):
    for entry in form:
        if entry is not 'submit':
            print(entry)
    return


def build_url(ip, port, reactorno, loop, action, values=[]):
    if loop not in cust.loopdict.keys():
        raise cust.InvalidAction
    else:
        r_name = 'R'+str(reactorno)
        vi_to_run = r_name+loop+'Control_'+action
        if action not in cust.ACTIONS:
            raise cust.InvalidAction
        else:
            params = cust.LOOPS[loop][action]
            print(params)
        if len(params) is not len(values):
            raise cust.InvalidValue('Expected '+str(len(params))+
                                    ' inputs but got '+str(len(values)))
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

#test = build_url('128.208.236.57', 8001, 1, 'pH', 'Switch', )
