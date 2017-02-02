## Define Custom Errors
class InvalidAction(Exception):
    """
    Error if an action not in ACTIONS constant is passed.
    """
    pass


class InvalidLoop(Exception):
    """
    Error if a control loop that the reactor does not have is passed.
    """
    pass


class InvalidValue(Exception):
    """
    Error if control parameters passed are not in the expected format/data type
    """
    pass


## Define Constants
# List of actions you can take on a control Loop
ACTIONS = ['Switch',  # Switch control loop on or off
           'Status',  # Get status of control loop
           'Manual',  # Control Loop Actuators Manually
           'SetParams']  # Set control loop parameters, i.e. gain, set pt, etc.
"""
Maybe switch to this format?
SBR_PUMPS = {'Effluent Pump': False,
             'Gas Pump': False,
             'Water Pump': False,
             'Media Pump': False}
SBR_PHASES = {'Anaerobic Feed': 50.0,
              'Purge': 5.0,
              'Aerated Feed': 0.0,
              'Aerate': 100.0,
              'Settle': 10.0,
              'Decant': 5.0,
              'Idle': 1.0}
"""
# List of actuating pumps for Sequencing Batch Reactor (SBR) mode control
SBR_PUMPS = [('Effluent%20Pump', 'Effluent Pump'),
             ('Gas%20Pump', 'Gas Pump'),
             ('Water%20Pump', 'Water Pump'),
             ('Media%20Pump', 'Media Pump')]

# List of phases associated SBR mode
SBR_PHASES = [('Anaerobic%20Feed', 'Anaerobic Feed'), # Media + Water pumps on
              ('Purge', 'Purge'),  # N2 MFC at full blast to purge air
              ('Aerated%20Feed', 'Aerated Feed'),  # Media + Water + Gas on
              ('Aerate', 'Aerate'),  # Gas pump on
              ('Settle', 'Settle'),  # All pumps off, biomass is settling
              ('Decant', 'Decant'),  # Effluent pump on
              ('Idle', 'Idle')]  # All pumps off

# List of signals being measured in cRIO
SIGNALS = [('pH', 'pH'),
           ('DO', 'DO'),
           ('NH4', 'NH4'),
           ('ORP', 'ORP'),
           ('VFD%20Signal', 'VFD Signal'),
           ('VFD%20RPM', 'VFD RPM'),
           ('Air', 'Air'),
           ('N2', 'N2')]
CONSTANTS = [('Data Smooth Time', 'Data Smooth Time'),
             ('ISE Na Correction Factor', 'ISE Na Correction Factor'),
             ('Na Concentration', 'Na Concentration')]
# TODO: How to add units to form label?
# List of control loops
LOOPS = ['pH', 'DO', 'NH4', 'SBR']

# Dictionaries of loop actuators and default values
PH_MANUAL = {'AcidPump': False, 'BasePump': False}
DO_MANUAL = {'Air': 0.0, 'N2': 0.0}
NH4_MANUAL = {'VFDFlowrate': 0.0}
SBR_MANUAL = {'CommandToPump': False,
              'Pump': SBR_PUMPS}

# Dictionaries of control loop parameters and default values
PH_SETPARAMS = {'pHDelay_In': 3.0, 'pHTol_In': 0.1, 'pHSetPt_In': 7.0}
DO_SETPARAMS = {'R1DOTol_In': 0.05, 'R1AirGain_In': 5000.0,
                'R1N2Gain_In': 1000.0, 'R1DOSetPt_In': 0.35}
NH4_SETPARAMS = {'VFDGain_In': 100.0, 'NH4Tol_In': 0.14,
                 'NH4SetPt_In': 0.01}
SBR_SETPARAMS = {'TimeToWrite': 0.0,
                 'Phase': SBR_PHASES}


def create_masterdict():
    """
    Creates a dictionary of dictionaries with following format:
    Level one: names of all the control loops
    Level two/Three: {'Manual': {Dictionary of actuators: Default Values}}
                     {'SetParams': {Dictionary of control parameters:
                                    Default Values}}
                     {'Switch': {control_on: Default is false}}
    :return:
    """
    dynamic_loopdict = {}
    for loop in LOOPS:
        dynamic_loopdict[loop] = {}
        for action in ACTIONS:
            if action == 'Status':
                dynamic_loopdict[loop][action] = None
            elif action == 'Switch':
                dynamic_loopdict[loop][action] = {'control_on': False}
            else:
                add_dict = (eval(str.upper(loop+'_'+action)))
                dynamic_loopdict[loop][action] = add_dict
    return dynamic_loopdict


loopdict = create_masterdict()
