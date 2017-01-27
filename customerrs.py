# Define Constants
import collections
class InvalidAction(Exception):
    pass


class InvalidLoop(Exception):
    pass


class InvalidValue(Exception):
    pass

ACTIONS = ['Switch',
           'Status',
           'Manual',
           'SetParams']

SBR_PUMPS = [('Effluent', 'Effluent Pump'),
             ('Gas', 'Gas Pump'),
             ('Water', 'Water Pump'),
             ('Media', 'Media Pump')]
SBR_PHASES = [('Anaerobic', 'Anaerobic Feed'),
              ('Purge', 'Purge'),
              ('Aerated_Feed', 'Aerated Feed'),
              ('Aerate', 'Aerate'),
              ('Settle', 'Settle'),
              ('Decant', 'Decant'),
              ('Idle', 'Idle')]
LOOPS = ['pH', 'DO', 'NH4', 'SBR']
PH_MANUAL = {'AcidPump': False, 'BasePump': False}
PH_SETPARAMS = {'pHDelay_In': 3.0, 'pHTol_In': 0.1, 'pHSetPt_In': 7.0}
DO_MANUAL = {'Air': 0.0, 'N2': 0.0}
DO_SETPARAMS = {'R1DOTol_In': 0.05, 'R1AirGain_In': 5000.0,
                'R1N2Gain_In': 1000.0, 'R1DOSetPt_In': 0.35}
NH4_MANUAL = {'VFDFlowrate': 0.0}
NH4_SETPARAMS = {'VFDGain_In': 100.0, 'NH4Tol_In': 0.14,
                 'NH4SetPt_In': 0.01}
SBR_MANUAL = {'Write': False, 'CommandToPump': False,
              'Pump': SBR_PUMPS}
SBR_SETPARAMS = {'Write': False, 'TimeToWrite': 0.0,
                               'Phase': SBR_PHASES}

def create_masterdict():
    loopdict={}
    for loop in LOOPS:
        loopdict[loop]={}
        for action in ACTIONS:
            if action == 'Status':
                loopdict[loop][action] = None
            elif action == 'Switch':
                loopdict[loop][action] = False
            else:
                add_dict=(eval(str.upper(loop+'_'+action)))
                loopdict[loop][action] = add_dict

    return loopdict

loopdict = create_masterdict()
