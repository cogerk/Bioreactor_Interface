"""
Create a graph of all probes for a given reactor
Written 3/20/17
By: Kathryn Cogert
"""
import numpy as np
from bokeh.plotting import figure
from bokeh.models.widgets import Slider
from bokeh.models import Legend, ColumnDataSource
from bokeh.layouts import widgetbox, layout
from reactorhandler import get_probe_snap
import graphs.plotmodels as mods
from bokeh.models.widgets import DataTable, TableColumn


def probe_graph_builder(ip, port, reactor, signals):
    def probe_graph(doc):
        # Define and format the figure
        ptitle = 'Reactor #' + str(reactor.idx) + ' Probes: ' + reactor.descrip
        p = figure(plot_width=800,
                   x_axis_type='datetime',
                   plot_height=550,
                   title=ptitle)
        p = mods.format_plot(p)
        rctprobes = signals

        # Remove non-linear actuator signals, they aren't probes
        rctprobes = [r for r in rctprobes if 'Flowrate' not in r]
        rctprobes = [r for r in rctprobes if 'VFD' not in r]

        # Generate a unique line format for each probe
        line_form_dict = mods.assign_line_format(rctprobes)

        ss_calcs = {'Analytic': ['Average',
                                 'Standard Deviation',
                                 'Differential']}
        ss_cols = [TableColumn(field='Analytic', title='Analytic', width=250)]
        trace = {}
        ds = {}
        lgls = []
        # Build the legend, data table columns, and lines
        dat, units = get_probe_snap(ip, port, reactor.idx)  # Get units for leg
        for probe in rctprobes:
            trace[probe] = p.line([], [],
                                  color=line_form_dict[probe][0],
                                  line_width=line_form_dict[probe][1])

            # Add probe to legend
            if units[probe] is not '':
                probe_label = probe + ', ' + units[probe]
            else:
                probe_label = probe
            lgls.append((probe_label, [trace[probe]]))

            # Define figure's data source
            ds[probe] = trace[probe].data_source
            ds[probe].data['x'] = []
            ds[probe].data['y'] = []
            # Intialize the table data source
            ss_calcs[probe] = [None]*3
            # Define columns in datatable
            ss_cols.append(TableColumn(field=probe,
                                       title=probe))
        # Define a data table for steady state analytics
        ss_data = ColumnDataSource(ss_calcs)
        data_table = DataTable(source=ss_data,
                               columns=ss_cols,
                               width=p.plot_width,
                               height=200,
                               row_headers=False)
        # Create widgets
        window_size = Slider(title="Time Frame, secs",
                             value=30,
                             start=5,
                             end=300,
                             step=1)
        length = window_size.css_classes = ['bokeh-labels']
        # Create Legend
        customlegend = Legend(items=lgls, location=(0, -45))
        p.add_layout(customlegend, 'right')
        # Initialize periodic callback vars
        stream_speed = 250
        df = {}
        length = 30

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
            new_data, u = get_probe_snap(ip, port, reactor.idx)
            # manipulate timestamp and dt data
            # if first time through, assign first data point
            delon = False
            if df == {}:
                df['Timestamp'] = [new_data['Timestamp']]
                df['dt'] = [df['Timestamp'][-1]-df['Timestamp'][0]]
            else:
                # if window size is same or greather than last time
                if length >= last:
                    # Add new timestamp and value to end of frame
                    df['Timestamp'].append(new_data['Timestamp'])
                    # if length of data frame is greater than specified length,
                    # remove last point, recalculate dt values
                    if (df['Timestamp'][-1] -
                            df['Timestamp'][0]).total_seconds() > length:

                        del df['Timestamp'][0]
                        df['dt'] = [ts-df['Timestamp'][0]
                                    for ts in df['Timestamp']]
                        delon = True
                    # If it's not, just add a new point to the dt
                    else:
                        df['dt'].append(df['Timestamp'][-1]-df['Timestamp'][0])
                # If length is smaller than last time
                else:
                    # Find the part of the data frame described by the new len
                    try:
                        idx = [x[0] for x in enumerate(df['dt']) if
                               (last-x[1].total_seconds()) <= length][0]
                    except IndexError:
                        idx = 0
                    df['Timestamp'] = df['Timestamp'][idx:-1]
                    df['dt'] = [ts-df['Timestamp'][0]
                                for ts in df['Timestamp']]
            idx = 0
            for sig in rctprobes:
                # if first time through, assign first data point
                try:
                    df[sig]
                except KeyError:
                    df[sig] = [float(new_data[sig])]
                    continue
                # if window size is same or greather than last time
                if length >= last:
                    # Add new timestamp and value to end of frame
                    df[sig].append(float(new_data[sig]))
                    # if length of data frame is greater than specified
                    # length, remove last point, recalculate dt values
                    if delon:
                        del df[sig][0]
                # If length is smaller than last time
                else:
                    df[sig] = df[sig][idx:-1]
                # Assign data to graph
                ds[sig].data['x'], ds[sig].data['y'] = df['dt'], df[sig]
                ds[sig].trigger('data', ds[sig].data, ds[sig].data)
                # Perform calcuations
                if len(ds[sig].data['x']) > 1:
                    avg = round(np.mean(ds[sig].data['y']), 4)
                    stdev = round(np.std(ds[sig].data['y']), 4)
                    dy = ds[sig].data['y'][-1] - ds[sig].data['y'][0]
                    x1 = ds[sig].data['x'][-1].total_seconds()
                    x2 = ds[sig].data['x'][0].total_seconds()
                    dx = x1 - x2
                    diff = round(dy/dx, 4)
                else:
                    diff = None
                    avg = None
                    stdev = None
                ss_data.data[sig] = [avg, stdev, diff]
            ss_data.trigger('data', ss_data.data, ss_data.data)
        # Build the document to serve
        inputs = widgetbox(window_size, width=p.plot_width)
        table = widgetbox(data_table)
        doc.add_root(layout([[p], [inputs], [table]],
                            sizing_mode='scale_width'))
        # Add a periodic callback to be run as defined by stream speed
        doc.add_periodic_callback(stream, stream_speed)

    return probe_graph
