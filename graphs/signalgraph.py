"""
Create a graph of a signal for a given reactor and signal
H/Ts to:
https://github.com/Corleo/flask_bokeh_app
http://stackoverflow.com/a/37726260/6397884
With BIG Modifications by: Kathryn Cogert
Written On: 3/18/2017
"""
from bokeh.plotting import figure
from reactorhandler import get_signal_snap
from bokeh.models.widgets import Slider
from bokeh.layouts import column, widgetbox
import graphs.plotmodels as mods
import numpy as np


def signal_graph_builder(ip, port, reactorno, signal):
    def signal_graph(doc):
        # Define and format the figure
        p = figure(plot_width=600,
                   x_axis_type='datetime',
                   plot_height=400,
                   title=signal)
        p = mods.format_plot(p)
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
        length = window_size.css_classes = ['bokeh-labels']
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
            if df == {}:
                df['Timestamp'] = [new_data['Timestamp']]
                df['dt'] = [df['Timestamp'][-1]-df['Timestamp'][0]]
                df[signal] = [float(new_data[signal])]
            else:
                if length >= last:
                    df['Timestamp'].append(new_data['Timestamp'])
                    df[signal].append(float(new_data[signal]))
                    if (df['Timestamp'][-1] -
                            df['Timestamp'][0]).total_seconds() > length:
                        del df['Timestamp'][0]
                        del df[signal][0]
                        df['dt'] = [ts-df['Timestamp'][0]
                                    for ts in df['Timestamp']]
                    else:
                        df['dt'].append(df['Timestamp'][-1]-df['Timestamp'][0])
                else:
                    try:
                        idx = [x[0] for x in enumerate(df['dt']) if
                               (last-x[1].total_seconds()) <= length][0]
                    except IndexError:
                        idx = 0
                    df['Timestamp'] = df['Timestamp'][idx:-1]
                    df[signal] = df[signal][idx:-1]
                    df['dt'] = [ts-df['Timestamp'][0]
                                for ts in df['Timestamp']]

            # Assign data to graph
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
            avgl.text = 'Average: ' + str(round(avg, 6))
            stdl.text = 'Standard Deviation: ' + \
                                     str(round(stdev, 6))
            difl.text = 'Differential: ' + str(round(diff, 6))
            # Assign label
            p.yaxis.axis_label = 'Calibrated Signal, ' + units[signal]
            ds.trigger('data', ds.data, ds.data)

        # Build the document to serve
        calcs = column(ctit, avgl, stdl, difl, width=p.plot_width)
        inputs = widgetbox(window_size, width=p.plot_width)
        doc.add_root(column(p, inputs, calcs))

        # Add a periodic callback to be run as defined by stream speed
        doc.add_periodic_callback(stream, stream_speed)

    return signal_graph
