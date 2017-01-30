"""
Code to dynamically generate a GET request to control a reactor
Written By: Kathryn Cogert
Jan 25 2017
"""

import customerrs as cust


def get_inputs(loop, action):
    return cust.loopdict[loop][action]


def get_submitted_vals(form):
    commands_forms_dict = {}
    for idx, entry in enumerate(form):
        if idx == 0:
            loop = entry[0:entry.index('_')]
            action = entry[entry.index('_')+1:entry.index('-')]
            all_commands_dict = get_inputs(loop,action)
        if 'submit' not in entry and 'csrf_token' not in entry:
            command = entry[entry.index('-')+1:]
            commands_forms_dict[command] = form[entry]
    for each in commands_forms_dict:
        if type(all_commands_dict[each]) == bool:
            if each not in all_commands_dict:
                all_commands_dict[each] = False
            else:
                all_commands_dict[each] = True
        if type(all_commands_dict[each]) == list:
            all_commands_dict[each] = commands_forms_dict[each]
        else:
            all_commands_dict[each] = all_commands_dict[each]
    return loop, action, all_commands_dict


def build_url(ip, port, reactorno, loop, action, params=[]):
    if loop not in cust.loopdict.keys():
        raise cust.InvalidAction
    else:
        r_name = 'R'+str(reactorno)
        vi_to_run = r_name+loop+'Control_'+action
        if action not in cust.ACTIONS:
            raise cust.InvalidAction
        else:
            default_params = cust.loopdict[loop][action]
        if len(default_params) is not len(params):
            raise cust.InvalidValue('Expected '+str(len(default_params)) +
                                    ' inputs but got '+str(len(params)))
        command = '?'
        for idx, each in enumerate(default_params):
            if isinstance(params[each], type(default_params[each])):
                if type(params[each]) is bool:
                    val = int(params[each])
                else:
                    val = params[each]
                command = command + each + '=' + str(val) + '&'
            else:
                raise cust.InvalidValue('Expected ' + each +
                                        ' to be datatype ' +
                                        type(default_params[each]) + ' got ' +
                                        type(params[each]))

        command = command[:-1]
    url = 'http://'+ip+':'+str(port)+'/'+r_name+'/'+vi_to_run+command
    return url
