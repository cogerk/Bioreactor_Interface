"""
On Server initiation, finds all the graphs needed and generates them
H/T to: https://github.com/Corleo/flask_bokeh_app
Modified By: Kathryn Cogert on 3/15/17
"""
from tornado.ioloop import IOLoop
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.server.server import Server
from graphs.signalgraph import signal_graph_builder
from graphs.probegraphs import probe_graph_builder
from isehandler import get_ise_rel_sigs
from graphs.isegraph import ise_graph_builder
from graphs.examples.streaming import stream_ex

# TODO: More efficient way to get data? fewer requests
# TODO: For control loops too
# TODO: Buttons aren't working
import reactorhandler as rctr
from views import reactors
import utils
all_ip = {}
all_port = {}
all_signals = {}
all_loops = {}
server_dict = {}
ise_rel_sigs = {}
for rct in reactors:
    ip, port = utils.get_controller_info(rct.idx, True)
    all_ip[rct] = ip
    all_port[rct] = port
    signals = rctr.get_signal_list(ip, port, rct.idx)
    loops = rctr.get_loops(all_ip[rct], all_port[rct], rct.idx)
    all_signals[rct] = signals
    print(signals)
    all_loops[rct] = loops
    appname = '/R' + str(rct.idx) + '_probes'
    # Generate all probe graphs
    server_dict[appname] = Application(
                FunctionHandler(
                    probe_graph_builder(ip, port, rct, all_signals[rct])))
    ise_rel_sigs ={}
    for sig in signals:
        # Generate ISE Graph Servers
        if 'ISE' in sig:
            ise = sig.replace(' ISE', '')
            appname, ise_rel_sigs = \
                get_ise_rel_sigs(ip, port, rct.idx, ise, signals)
            server_dict[appname] = Application(FunctionHandler(
                ise_graph_builder(ip, port, rct.idx, ise_rel_sigs)))
        # Generate specific signal graph
        if 'VFD' in sig:
            split_sig = sig.split(' ')
            joined_sig = split_sig[0]+' '+split_sig[1]+' Flowrate'
            if joined_sig not in list(server_dict.keys()):
                appname = '/R' + str(rct.idx)+'_' + \
                          joined_sig.replace(' ', '_')
                server_dict[appname] = Application(FunctionHandler(
                        signal_graph_builder(ip, port, rct.idx, joined_sig)))
        else:
            appname = '/R' + str(rct.idx)+'_' + sig.replace(' ', '_')
            server_dict[appname] = Application(
                FunctionHandler(
                    signal_graph_builder(ip, port, rct.idx, sig)))

server_dict['/stream_ex'] = Application(FunctionHandler(stream_ex))


def bokeh_init():
    io_loop = IOLoop.current()
    server = Server(server_dict, io_loop=io_loop,
                    allow_websocket_origin=["localhost:8002"])
    server.start()
    io_loop.start()
    return server, io_loop

# Start bokeh server
if __name__ == '__main__':
    print('Starting Bokeh Server')
    bokeh_init()
