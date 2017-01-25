## Code to dynamically generate a GET request to control a reactor
## Written By: Kathryn Cogert
## Jan 25 2017

# TODO: cRIO side- Preface w/ Reactor No?
# TODO: cRIO side- multiply delay by 1000 in labview
# TODO: cRIO side- switch to _Status


# Define Constants
ACTIONS = {'Switch': [],
           'Status': [],
           'Manual': [],
           'SetParams': []}

SBR_PUMPS = ['Effluent Pump', 'Gas Pump', 'Water Pump', 'Media Pump']

SBR_PHASES = ['Anaerobic Feed', 'Purge', 'Aerated Feed', 'Aerate', 'Settle',
              'Decant', 'Idle']

LOOPS = {'pH': [['AcidPump', 'BasePump'],
                ['pHDelay_In', 'pH4Tol_In', 'pH4SetPt_In']],
         'DO': [['Air', 'N2'],
                ['R1DOTol_In', 'R1AirGain_In', 'R1N2Gain_In', 'R1DOSetPt_In']],
         'NH4': [['VFDFlowrate'],
                 ['VFDGain_In', 'NH4Tol_In', 'NH4SetPt_In']],
         'SBR': [['Write', 'CommandToPump''Pump'],
                 ['Write', 'TimeToWrite', 'Phase']]}

LOOP_DEFAULTS = {'pH': [[False, False],
                        [3.0, 0.1, 7.0]],
                 'DO': [[0.0, 0.0],
                        [0.05, 5000.0, 1000.0, 0.35]],
                 'NH4': [[0.0],
                         [100.0, 0.14, 0.01]],
                 'SBR': [[False, False, SBR_PUMPS[0]],
                         [False, 0, 'Aerate']]}


class InvalidAction(Exception):
    pass


class InvalidLoop(Exception):
    pass


class InvalidValue(Exception):
    pass


def build_url(ip, port, reactorno, loop, action, values=[]):
    if loop not in LOOPS.keys():
        raise InvalidAction
    else:
        r_name = 'R'+str(reactorno)
        vi_to_run = r_name+loop+'Control_'+action
        if action not in ACTIONS.keys():
            raise InvalidAction
        elif action is 'Manual':
            params = LOOPS[loop][0]
        elif action is 'SetParams':
            params = LOOPS[loop][1]
        elif action is 'Switch':
            params=[loop+'ControlOn']
        else:
            params = []
        if len(params) is not len(values):
            raise InvalidValue
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
