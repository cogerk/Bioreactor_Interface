"""
Create a graph of a signal for a given reactor and signal
H/Ts to:
https://github.com/Corleo/flask_bokeh_app
http://stackoverflow.com/a/37726260/6397884
With BIG Modifications by: Kathryn Cogert
Written On: 3/18/2017
"""
import warnings
from bokeh.plotting import figure
from reactorhandler import get_signal_snap
from bokeh.models.widgets import Slider
from bokeh.layouts import layout, widgetbox
from bokeh.util.warnings import BokehUserWarning
import numpy as np
import graphs.plotmodels as mods


def signal_graph_builder(ip, port, reactorno, signal):
    """
    Builds a function to display a single signal for the bokeh server to serve
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactorno: int, # of the reactor
    :param signal: str, the signal for the graph
    :return: function(doc)
    """
    def signal_graph(doc):
        """
        Function to generate document for server
        :param doc: bokeh document
        :return:
        """
        # Define and format the figure
        p = figure(plot_width=600,
                   x_axis_type='datetime',
                   plot_height=400,
                   title=signal)
        p = mods.format_plot(p, multi=True)
        trace = p.line([], [],
                       color='Navy',
                       line_width=2,
                       legend=signal)
        ctit, avgl, stdl, difl = mods.steady_state_calcs(p.plot_width)
        ctit.text = ctit.text.replace('Signal', signal)

        # Define figure's data source
        ds = trace.data_source
        # Create widgets
        window_size = Slider(title="Time Frame, secs",
                             value=30,
                             start=5,
                             end=300,
                             step=1)
        stream_speed = 250
        df = {}
        window_size.css_classes = ['bokeh-labels']
        ds.data['x'] = []
        ds.data['y'] = []

        # Periodic Callback Function
        def stream():
            global last
            global length
            try:
                length
            except NameError:
                length = window_size.value
            last = length
            length = window_size.value
            # Get latest snapshot of data
            new_data, units = get_signal_snap(ip, port, reactorno)
            # Append to end of existing data
            if df == {}:  # if first time through
                # Assign label to y axis
                p.yaxis.axis_label = 'Calibrated Signal, ' + units[signal]
                # Add first point
                df['Timestamp'] = [new_data['Timestamp']]
                df['dt'] = [df['Timestamp'][-1]-df['Timestamp'][0]]
                df[signal] = [float(new_data[signal])]
            else:  # not first time through
                if length >= last:  # if time window is greater or same
                    # add new point to end
                    df['Timestamp'].append(new_data['Timestamp'])
                    df[signal].append(float(new_data[signal]))
                    # check if current data exceeds specified length
                    if (df['Timestamp'][-1] -
                            df['Timestamp'][0]).total_seconds() > length:
                        # if it does, recalc dt and delete first point
                        del df['Timestamp'][0]
                        del df[signal][0]
                        df['dt'] = [ts-df['Timestamp'][0]
                                    for ts in df['Timestamp']]
                    else:  # if is doesn't, just calcuate latest dt
                        df['dt'].append(df['Timestamp'][-1]-df['Timestamp'][0])
                else:  # if time window is shorter than last time through
                    try:  # cut down the data to new time window
                        idx = [x[0] for x in enumerate(df['dt']) if
                               (last-x[1].total_seconds()) <= length][0]
                    except IndexError:
                        idx = 0
                    df['Timestamp'] = df['Timestamp'][idx:len(df['Timestamp'])]
                    df[signal] = df[signal][idx:len(df[signal])]
                    df['dt'] = [ts-df['Timestamp'][0]
                                for ts in df['Timestamp']]
            # Assign data to graph
            with warnings.catch_warnings():
                # first couple itrs, avoid weird warning
                warnings.simplefilter("ignore", category=BokehUserWarning)
                ds.data['x'], ds.data['y'] = df['dt'], df[signal]
            # Perform calcuations
            if len(ds.data['x']) > 1:
                diff = (ds.data['y'][-1] - ds.data['y'][0])\
                       / (ds.data['x'][-1].total_seconds() -
                          ds.data['x'][0].total_seconds())
                avg = np.mean(ds.data['y'])
                stdev = np.std(ds.data['y'])
            else:
                diff = None
                avg = None
                stdev = None
            try:
                avgl.text = 'Average: ' + str(round(avg, 6))
                stdl.text = 'Standard Deviation: ' + \
                            str(round(stdev, 6))
                difl.text = 'Differential: ' + str(round(diff, 6))
            except TypeError:
                pass
            # Send new data to graph
            ds.trigger('data', ds.data, ds.data)
        # Build the document to serve
        calcs = layout([[ctit], [avgl], [stdl], [difl]],
                       sizing_mode='scale_width')
        inputs = widgetbox(window_size, width=p.plot_width)
        doc.add_root(layout([[p], [inputs], [calcs]],
                            sizing_mode='scale_width'))
        # Add a periodic callback to be run as defined by stream speed
        doc.add_periodic_callback(stream, stream_speed)
    return signal_graph
