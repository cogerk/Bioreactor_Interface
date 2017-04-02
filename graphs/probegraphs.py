"""
Create a graph of all probes for a given reactor
Written 3/20/17
By: Kathryn Cogert
"""
import warnings
from bokeh.plotting import figure
from bokeh.models.widgets import DataTable, TableColumn
from bokeh.models.widgets import Slider, CheckboxButtonGroup, RadioGroup
from bokeh.models import Legend, ColumnDataSource
from bokeh.layouts import widgetbox, layout
from bokeh.util.warnings import BokehUserWarning
import numpy as np
from reactorhandler import get_probe_snap
import graphs.plotmodels as mods


def probe_graph_builder(ip, port, reactor, signals):
    """
    Builds a function of all reactor signals to serve in the bokeh server
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactor: Reactor class, # of the reactor & description
    :param signals: list str, list of signals available from the reactor
    :return: function(doc)
    """
    def probe_graph(doc):
        """
        Function to generate document for server
        :param doc: bokeh document
        :return:
        """
        # Define and format the figure
        ptitle = 'Reactor #' + str(reactor.idx) + ' Probes: ' + reactor.descrip
        p = figure(plot_width=800,
                   x_axis_type='datetime',
                   plot_height=500,
                   title=ptitle)
        p = mods.format_plot(p, True)
        ax_dict = {0: 'default',
                   1: '2nd'}
        rctprobes = signals

        # Remove non-linear actuator signals, they aren't probes
        rctprobes = [r for r in rctprobes if 'Flowrate' not in r]
        rctprobes = [r for r in rctprobes if 'VFD' not in r]

        # Generate a unique line format for each probe
        line_form_dict = mods.assign_line_format(rctprobes)

        # Initiate data dictionaries, legend label list, and line dictionary
        ss_calcs = {'Analytic': ['Average',
                                 'Standard Deviation',
                                 'Differential']}
        ss_cols = [TableColumn(field='Analytic', title='Analytic', width=450)]
        trace = {}
        ds = {}
        lgls = []
        axis_pickers = []
        # Build the legend, data table columns, and lines
        dat, units = get_probe_snap(ip, port, reactor.idx)  # Get units for leg
        for probe in rctprobes:
            # make the line
            trace[probe] = p.line([], [],
                                  color=line_form_dict[probe][0],
                                  line_width=line_form_dict[probe][1])
            # Define lines's data source
            ds[probe] = trace[probe].data_source
            ds[probe].data['x'] = []
            ds[probe].data['y'] = []

            # Add probe to legend
            if units[probe] is not '':
                probe_label = probe + ', ' + units[probe]
            else:
                probe_label = probe
            lgls.append((probe_label, [trace[probe]]))

            # Make axis picker
            if probe == 'ORP':
                trace[probe].y_range_name = '2nd'
                act = 1
            else:
                act = 0
            axis_pickers.append(RadioGroup(
                labels=[probe + ' on Left Axis',
                        probe + ' on Right Axis'],
                active=act,
                css_classes=['bokeh-radio']))

            # Intialize the table data source
            ss_calcs[probe] = [None]*len(ss_calcs['Analytic'])
            # Define columns in datatable
            ss_cols.append(TableColumn(field=probe,
                                       title=probe))

        # Define a data table for steady state analytics
        ss_data = ColumnDataSource(ss_calcs)
        data_table = DataTable(source=ss_data,
                               columns=ss_cols,
                               width=p.plot_width+100,
                               height=200,
                               row_headers=False)
        # Create widgets
        window_size = Slider(title="Time Frame, secs",
                             value=600,
                             start=5,
                             end=3600,
                             step=1)
        plots_on = CheckboxButtonGroup(labels=rctprobes,
                                       active=list(range(len(rctprobes))))
        diff_size = Slider(title="Differential Time Frame, secs",
                           value=30,
                           start=5,
                           end=300,
                           step=1)

        window_size.css_classes = ['bokeh-labels']
        # Create Legend
        customlegend = Legend(items=lgls,
                              location=(0, -47),
                              label_text_font_size='12pt')
        p.add_layout(customlegend, 'left')
        # Initialize periodic callback vars
        stream_speed = 1000
        df = {}
        length_dt = 30

        # Periodic Callback Function
        def stream():
            # Initialize diff time slider vals
            global last_diff_dt
            global length_diff_dt
            try:
                length_diff_dt
            except NameError:
                length_diff_dt = diff_size.value
            last_diff_dt = length_diff_dt
            length_diff_dt = window_size.value

            # Initialize time slider vals
            global last_dt
            global length_dt
            try:
                length_dt
            except NameError:
                length_dt = window_size.value
            last_dt = length_dt
            length_dt = window_size.value

            # Initialize Plot Selector Vals
            global last_plts
            global current_plts
            try:
                current_plts
            except NameError:
                current_plts = plots_on.active
            last_plts = current_plts
            current_plts = plots_on.active

            # Initialize Axis Picker Vals
            global last_ax
            global current_ax
            try:
                current_ax
            except NameError:
                current_ax = [x.active for x in axis_pickers]
            last_ax = current_ax
            current_ax = [x.active for x in axis_pickers]

            # Get latest snapshot of data
            new_data, u = get_probe_snap(ip, port, reactor.idx)

            # *Manipulate timestamp and dt data*
            # if first time through, assign first data point
            delon = False
            if df == {}:
                df['Timestamp'] = [new_data['Timestamp']]
                df['dt'] = [df['Timestamp'][-1]-df['Timestamp'][0]]
            else:
                # if window size is same or greater than last time
                if length_dt >= last_dt:
                    # Add new timestamp and value to end of frame
                    df['Timestamp'].append(new_data['Timestamp'])
                    # if length of data frame is greater than specified length,
                    # remove last point, recalculate dt values
                    if (df['Timestamp'][-1] -
                            df['Timestamp'][0]).total_seconds() > length_dt:

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
                               (last_dt - x[1].total_seconds()) <= length_dt][0]
                    except IndexError:
                        idx = 0
                    df['Timestamp'] = df['Timestamp'][idx:-1]
                    df['dt'] = [ts-df['Timestamp'][0]
                                for ts in df['Timestamp']]
            # *Manipulate aspects of plot affected by signals*
            idx = 0
            if current_plts != last_plts:
                new_lgls = []
            for no, sig in enumerate(rctprobes):
                # Update which plots are visible and build legend list
                if current_plts != last_plts:
                    if no in current_plts:
                        trace[sig].visible = True
                        if units[sig] is not '':
                            sig_label = sig + ', ' + units[sig]
                        else:
                            sig_label = sig
                        new_lgls.append((sig_label, [trace[sig]]))
                    else:
                        trace[sig].visible = False
                # Update axis ownership of plots
                if current_ax[no] != last_ax[no]:
                    trace[sig].y_range_name = ax_dict[current_ax[no]]
                # if first time through, assign first data point
                try:
                    df[sig]
                except KeyError:
                    df[sig] = [float(new_data[sig])]
                    continue
                # if window size is same or greather than last time
                if length_dt >= last_dt:
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
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=BokehUserWarning)
                    ds[sig].data['x'], ds[sig].data['y'] = df['dt'], df[sig]
                ds[sig].trigger('data', ds[sig].data, ds[sig].data)
                # Perform calcuations
                if len(ds[sig].data['x']) > 1:
                    avg = round(np.mean(ds[sig].data['y']), 4)
                    stdev = round(np.std(ds[sig].data['y']), 4)
                    x1 = ds[sig].data['x'][-1].total_seconds()
                    x2 = x1 - length_diff_dt
                    diff_arr = [np.abs(x.total_seconds() - x2)
                                for x in ds[sig].data['x']]
                    idx = np.argmin(diff_arr)
                    dy = ds[sig].data['y'][-1] - ds[sig].data['y'][idx]
                    diff = round(dy/length_diff_dt, 4)
                else:
                    diff = None
                    avg = None
                    stdev = None
                ss_data.data[sig] = [avg, stdev, diff]
            # Update legend
            if current_plts != last_plts:
                customlegend.items = new_lgls
            # Trigger table data source
            ss_data.trigger('data', ss_data.data, ss_data.data)

        # Build the document to serve
        inputs = widgetbox(window_size, diff_size, width=p.plot_width)
        plot_btns = widgetbox(plots_on)
        table = widgetbox(data_table)
        axis_opts = [widgetbox(x) for x in axis_pickers]
        doc.add_root(layout([[p],
                             [plot_btns],
                             axis_opts,
                             [inputs],
                             [table]],
                            sizing_mode='scale_width'))
        # Add a periodic callback to be run as defined by stream speed
        doc.add_periodic_callback(stream, stream_speed)

    return probe_graph
