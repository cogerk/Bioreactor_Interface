"""
Create a graph of all probes for a given reactor
Written 3/20/17
By: Kathryn Cogert
"""
import warnings
from itertools import groupby
from operator import itemgetter
from bokeh.plotting import figure
from bokeh.models.widgets import DataTable, TableColumn
from bokeh.models.widgets import Slider, CheckboxButtonGroup
from bokeh.models import Legend, ColumnDataSource
from bokeh.layouts import widgetbox, layout
from bokeh.util.warnings import BokehUserWarning
import numpy as np
from reactorhandler import get_probe_snap, get_phases
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
        axis_names = {'default': 'pH/Concentration, mg/L', '2nd': 'ORP, mV'}
        rctprobes = signals


        # Remove non-linear actuator signals, they aren't probes
        rctprobes = [r for r in rctprobes if 'Flowrate' not in r]
        # TODO: CRIO Replace MFC with Flowrate
        # TODO: User will need flowrate or VFD in signal name to make sure it doesn't get included in this graph
        rctprobes = [r for r in rctprobes if 'VFD' not in r]
        try:
            rctprobes.remove('Reactor Status')
        except ValueError:
            pass
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
        # Build the legend, data table columns, and lines
        dat, units = get_probe_snap(ip, port, reactor.idx)  # Get units for leg
        for ax in p.yaxis:
            ax.axis_label = axis_names[ax.y_range_name]
        for probe in rctprobes:
            # Make The Line, if ORP, put on 2nd axis
            if probe == 'ORP':
                trace[probe] = p.line([], [],
                                      name=probe,
                                      color=line_form_dict[probe][0],
                                      line_width=line_form_dict[probe][1],
                                      line_dash='dashed')
                trace[probe].y_range_name = '2nd'
                p.extra_y_ranges['2nd'].names = [probe]
            else:
                p.y_range.names.append(probe)
                trace[probe] = p.line([], [],
                                      name=probe,
                                      color=line_form_dict[probe][0],
                                      line_width=line_form_dict[probe][1])

            # Define lines's data source
            ds[probe] = trace[probe].data_source
            ds[probe].data['x'] = []
            ds[probe].data['y'] = []
            # TODO: No Command Submitted?
            # Add probe to legend
            if units[probe] is not '':
                probe_label = probe + ', ' + units[probe]
            else:
                probe_label = probe
            lgls.append((probe_label, [trace[probe]]))

            # Intialize the table data source
            ss_calcs[probe] = [None]*len(ss_calcs['Analytic'])
            # Define columns in datatable
            ss_cols.append(TableColumn(field=probe,
                                       title=probe))

        # Get phases & generate unique format for each
        phases = get_phases(ip, port, reactor.idx, False)
        phase_ls = list(list(zip(*phases))[0])
        phase_form_dict = mods.assign_line_format(phase_ls)

        # Define phase indicators
        for phase in phase_ls:
            alpha_val = ((phase_form_dict[phase][1] - 2) / 0.5) * .2 + 0.1
            trace[phase] = p.quad(name=phase,
                                  top=[],
                                  bottom=[],
                                  left=[],
                                  right=[],
                                  color=phase_form_dict[phase][0],
                                  alpha=alpha_val,
                                  line_alpha=0)

            ds[phase] = trace[phase].data_source
            ds[phase].data['left'] = []
            ds[phase].data['right'] = []
            ds[phase].data['top'] = []
            ds[phase].data['bottom'] = []
            lgls.append((phase, [trace[phase]]))
        trace['Manual Mode'] = p.quad(name='Manual Mode',
                                      top=[],
                                      bottom=[],
                                      left=[],
                                      right=[],
                                      color='grey',
                                      alpha=0.1,
                                      line_alpha=0)
        ds['Manual Mode'] = trace['Manual Mode'].data_source
        ds['Manual Mode'].data['left'] = []
        ds['Manual Mode'].data['right'] = []
        ds['Manual Mode'].data['top'] = []
        ds['Manual Mode'].data['bottom'] = []
        lgls.append(('Manual Mode', [trace['Manual Mode']]))
        phase_ls.append('Manual Mode')

        # Define a data table for steady state analytics
        ss_data = ColumnDataSource(ss_calcs)
        data_table = DataTable(source=ss_data,
                               columns=ss_cols,
                               width=p.plot_width,
                               height=200,
                               row_headers=False)
        # Create widgets
        window_size = Slider(title="Time Frame, secs",
                             value=600,
                             start=5,
                             end=3600,
                             step=1)
        plot_ls = rctprobes + ['Sequencing Batch Mode Status']
        plots_on = CheckboxButtonGroup(labels=plot_ls,
                                       active=list(range(len(plot_ls))))
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
            length_diff_dt = diff_size.value

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

            # Get latest snapshot of data
            new_data, u = get_probe_snap(ip, port, reactor.idx)
            # *Manipulate timestamp and dt data*
            # if first time through, assign first data point
            delon = False
            if df == {}:
                df['Timestamp'] = [new_data['Timestamp']]
                df['dt'] = [df['Timestamp'][-1]-df['Timestamp'][0]]
                df['Reactor Status'] = [new_data['Reactor Status']]
            else:
                # if window size is same or greater than last time
                # TODO: Debug window size slider
                if length_dt >= last_dt:
                    # Add new timestamp and value to end of frame
                    df['Timestamp'].append(new_data['Timestamp'])
                    df['Reactor Status'].append(new_data['Reactor Status'])
                    # if length of data frame is greater than specified length,
                    # remove last point, recalculate dt values
                    if (df['Timestamp'][-1] -
                            df['Timestamp'][0]).total_seconds() > length_dt:

                        del df['Timestamp'][0]
                        del df['Reactor Status'][0]
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
                    df['Timestamp'] = df['Timestamp'][idx:len(df['Timestamp'])]
                    df['Reactor Status'] = \
                        df['Reactor Status'][idx:len(df['Reactor Status'])]
                    df['dt'] = [ts-df['Timestamp'][0]
                                for ts in df['Timestamp']]

            # Update which plots are visible and build legend list
            if current_plts != last_plts:
                new_lgls = []
                for no, plot in enumerate(plot_ls):
                    if no == len(plot_ls) - 1:
                        for phase in phase_ls:
                            trace[phase].visible = no in current_plts
                            if no in current_plts:
                                new_lgls.append((phase, [trace[phase]]))
                    else:
                        trace[plot].visible = no in current_plts
                        if no in current_plts:
                            if units[plot] is not '':
                                plot_label = plot + ', ' + units[plot]
                            else:
                                plot_label = plot
                            new_lgls.append((plot_label, [trace[plot]]))

            # *Manipulate aspects of plot affected by signals*
            idx = 0
            for sig in rctprobes:
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
                    df[sig] = df[sig][idx:len(df[sig])]
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
            ls = df['Reactor Status']
            # TODO: Remove units from phase ls
            for phase in phase_ls:
                #TODO: Add this functionality to loopsgraph
                if phase == 'Manual Mode':
                    pstr = phase
                else:
                    pstr = 'SBR Control On: ' + phase
                idxs = [idx for idx, x in enumerate(ls) if x == pstr]
                ranges = []
                for k, g in groupby(enumerate(idxs), lambda x:x[0]-x[1]):
                    group = list(map(itemgetter(1), g))
                    ranges.append([group[0], group[-1]])
                if not ranges:
                    l = []
                    r = []
                    t = []
                    b = []
                elif len(ranges) == 1:
                    l = [df['dt'][ranges[0][0]]]
                    r = [df['dt'][ranges[0][1]]]
                    t = [p.y_range.end]
                    b = [p.y_range.start]
                else:
                    l_idx, r_idx = list(zip(*ranges))
                    l, r = [], []
                    for no, each in enumerate(l_idx):
                        l.append((df['dt'][each]))
                        r.append((df['dt'][r_idx[no]]))
                    t = [p.y_range.end] * len(l)
                    b = [p.y_range.start] * len(l)
                # TODO: Why does this report that columns are of diff length?
                ds[phase].data['left'] = l
                ds[phase].data['right'] = r
                ds[phase].data['top'] = t
                ds[phase].data['bottom'] = b
                ds[phase].trigger('data', ds[phase].data, ds[phase].data)
            # Update legend
            if current_plts != last_plts:
                customlegend.items = new_lgls
            # Trigger table data source
            ss_data.trigger('data', ss_data.data, ss_data.data)

        # Build the document to serve
        inputs = widgetbox(window_size, diff_size)
        plot_btns = widgetbox(plots_on)
        table = widgetbox(data_table)
        doc.add_root(layout([[p],
                            [plot_btns],
                            [inputs],
                            [table]], sizing_mode='scale_width'))
        # Add a periodic callback to be run as defined by stream speed
        doc.add_periodic_callback(stream, stream_speed)

    return probe_graph
