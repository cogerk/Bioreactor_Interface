"""
On Server initiation, finds all the graphs needed and generates them
H/T to: https://github.com/Corleo/flask_bokeh_app
Modified By: Kathryn Cogert on 3/15/17
"""

# TODO: Get rid of front panel (last thing)
# TODO: SBR Manual + Set Params
# TODO: Diasble Form Command Resubmission!
# TODO: Protocol for how to add a new control loop (be sure to remove special chars from input/output names), make NH4 Control Loop to do this.
# TODO: Note that SBR array should not have special characters in the phase name
import warnings
from tornado.ioloop import IOLoop
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.server.server import Server
import customerrs
import dbhandler
from graphs.signalgraph import signal_graph_builder
from graphs.probegraphs import probe_graph_builder
from graphs. cyclegraph import cycle_graph_builder
from reactorhandler import get_phases
from isehandler import get_ise_rel_sigs
from graphs.isegraph import ise_graph_builder
from graphs.loopsgraphs import loop_graph_builder
from graphs.examples.streaming import stream_ex
# TODO: Plot Old Data when we open the graph
# TODO: More efficient way to get data? fewer requests
from views import reactors

all_ip = {}
all_port = {}
all_signals = {}
all_loops = {}
server_dict = {}
ise_rel_sigs = {}
try:
    for rct in reactors:
        ip, port = dbhandler.get_controller_info(rct.idx, True)
        all_ip[rct] = ip
        all_port[rct] = port
        signals = [str(x) for x in rct.signals]
        if not signals:
            continue
        phases = get_phases(ip, port, str(rct.idx), include_units=False)
        loops = [str(x) for x in rct.loops]
        all_signals[rct] = signals
        all_loops[rct] = loops
        if 'SBR' in loops:
            appname = '/R' + str(rct.idx) + '_cycle'
            cycle_graph = cycle_graph_builder(1, ip, port, rct.idx)
            server_dict[appname] = Application(
                            FunctionHandler(
                                cycle_graph))
        # Generate all probes graph
        appname = '/R' + str(rct.idx) + '_probes'
        server_dict[appname] = Application(
            FunctionHandler(
                probe_graph_builder(ip,
                                    port,
                                    rct,
                                    all_signals[rct])))

        if loops is not None:
            # Generate control loop graph
            for loop in loops:
                if loop != 'SBR':
                    appname = '/R' + str(rct.idx) + '_' + loop + '_loop'
                    server_dict[appname] = Application(FunctionHandler(
                            loop_graph_builder(ip, port, rct, loop)))
            ise_rel_sigs ={}
            for sig in signals:
                # Generate ISE graphs
                if 'ISE' in sig:
                    ise = sig.replace(' ISE', '')
                    appname, ise_rel_sigs = \
                        get_ise_rel_sigs(ip, port, rct.idx, ise, signals)
                    server_dict[appname] = Application(FunctionHandler(
                        ise_graph_builder(ip, port, rct.idx, ise_rel_sigs)))
                # Generate specific signal graph
                if 'VFD' in sig:
                    split_sig = sig.split(' ')
                    join_sig = split_sig[0]+' '+split_sig[1]+' Flowrate'
                    if join_sig not in list(server_dict.keys()):
                        appname = '/R' + str(rct.idx)+'_' + \
                                  join_sig.replace(' ', '_')
                        server_dict[appname] = Application(FunctionHandler(
                                signal_graph_builder(ip, port, rct.idx, join_sig)))
                else:
                    appname = '/R' + str(rct.idx)+'_' + \
                              str(sig).replace(' ', '_')
                    server_dict[appname] = Application(
                        FunctionHandler(
                            signal_graph_builder(ip, port, rct.idx, sig)))

    server_dict['/stream_ex'] = Application(FunctionHandler(stream_ex))
except customerrs.CannotReachReactor:
    warnings.warn('Could not reach Reactor #' + str(rct.idx),
                  customerrs.CannotReachReactorWarn)
except customerrs.CannotReachController:
    warnings.warn('Could not reach crio at IPL' + ip,
                  customerrs.CannotReachControllerWarn)


def bokeh_init():
    io_loop = IOLoop.current()
    server = Server(server_dict, io_loop=io_loop,
                    allow_websocket_origin=['localhost:8002',
                                            'localhost:5006'])
    server.start()
    io_loop.start()
    return server, io_loop
# Start bokeh server
if __name__ == '__main__':
    bokeh_init()
