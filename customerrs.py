# Define Constants
ACTIONS = ['Switch',
           'Status',
           'Manual',
           'SetParams']
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