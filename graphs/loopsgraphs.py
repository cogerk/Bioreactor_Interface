"""
Create a graph of all probes for a given reactor
Written 3/20/17
By: Kathryn Cogert
"""
import warnings
from itertools import compress, groupby
from operator import itemgetter
from bokeh.plotting import figure
from bokeh.models.widgets import Slider, CheckboxButtonGroup
from bokeh.models import Legend, Paragraph
from bokeh.layouts import widgetbox, layout
from bokeh.util.warnings import BokehUserWarning
from controlcmdhandler import get_loop_snap
import graphs.plotmodels as mods

# TODO: Double check the rest of the graphs
# TODO: Add switching to reactor page
# TODO: Error between set and actual actuators
# TODO: cRIO Side: turn off gas pump reporting to loops
# TODO: cRIO Side: Remove Purge
# TODO: crio side: Check SBR Control Program Reactor Status Writing


def loop_graph_builder(ip, port, reactor, loop):
    """
    Builds a function of all reactor signals to serve in the bokeh server
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactor: Reactor class, # of the reactor & description
    :param loop: str, the control loop to build graph for
    :return: function(doc)
    """
    def loop_graph(doc):
        """
        Function to generate document for server
        :param doc: bokeh document
        :return:
        """
        # Define and format the figure
        ptitle = 'Reactor #' + str(reactor.idx) + ': ' + reactor.descrip + \
                 ' Control Status: '+ loop +' Control Loop'
        p = figure(plot_width=800,
                   x_axis_type='datetime',
                   x_axis_label='Time',
                   plot_height=500,
                   title=ptitle)
        data, lines, acts, bool_acts = get_loop_snap(ip, port, reactor.idx, loop)
        # Generate a unique line format for each probe
        if bool_acts:
            line_form_dict = mods.assign_line_format(lines)
            act_form_dict = mods.assign_line_format(acts)
            p = mods.format_plot(p, False)
        else:
            # Find variable acuators that don't send their status back to cRIO
            no_out_acts = []
            for act in acts[1::]:
                if act.replace('Set ', '') not in lines:
                    no_out_acts.append(act)
            # Assign unique line formats to those acutators
            line_form_dict = mods.assign_line_format(lines+no_out_acts)
            # If there are actuators that send their status back,
            # display if setpoint = actuator output
            # This is handy i.e. when back pressure on
            # MFC causes it to have low flow despite a high set point
            if not no_out_acts:
                var_act_stat = Paragraph(text='Actuators meeting setpoints')
            p = mods.format_plot(p, True)

        # Initiate data dictionaries, legend label list, and line dictionary
        trace = {}
        ds = {}
        lgls = []
        axis_names = {}
        axis_belongs = {'default': [], '2nd': []}
        axis_name = []
        for line in lines:
            if line.split(', ')[0] == loop:
                axis_names['default'] = line

            # make the line
            if 'Set ' + line in acts:
                trace[line] = p.line([], [],
                                     name=line,
                                     color=line_form_dict[line][0],
                                     line_width=line_form_dict[line][1],
                                     line_dash='dashed',
                                     y_range_name='2nd')
                axis_belongs['2nd'].append(line)
            else:
                trace[line] = p.line([], [],
                                     name=line,
                                     color=line_form_dict[line][0],
                                     line_width=line_form_dict[line][1])
                axis_belongs['default'].append(line)
            # Define lines's data source
            ds[line] = trace[line].data_source
            ds[line].data['x'] = []
            ds[line].data['y'] = []

            # Add probe to legend
            lgls.append((line, [trace[line]]))

            # If set point, add quad graph to show set point tolerance
            if 'Set Point' in line:
                tol = line.replace('Set Point', 'Tolerance')
                trace[tol] = p.quad(name=line,
                                    top=[],
                                    bottom=[],
                                    left=[],
                                    right=[],
                                    color=line_form_dict[line][0],
                                    alpha=0.1,
                                    line_alpha=0)
                axis_belongs['default'].append(tol)
                # Define lines's data source
                ds[tol] = trace[tol].data_source
                ds[tol].data['top'] = []
                ds[tol].data['bottom'] = []
                ds[tol].data['right'] = []
                ds[tol].data['left'] = []
        for act in acts:
            if act == 'Manual Control On':
                trace['Manual Control On'] = p.quad(name=act,
                                                    top=[],
                                                    bottom=[],
                                                    right=[],
                                                    left=[],
                                                    color='gray',
                                                    alpha=0.1)
                ds[act] = trace[act].data_source
                ds[act].data['top'] = []
                ds[act].data['bottom'] = []
                ds[act].data['right'] = []
                ds[act].data['left'] = []
            elif bool_acts:
                # make the bar graph
                trace[act] = p.quad(name=act,
                                    top=[],
                                    bottom=[],
                                    right=[],
                                    left=[],
                                    color=act_form_dict[act][0],
                                    alpha=.25)
                axis_belongs['default'].append(act)
                # Define Data source
                ds[act] = trace[act].data_source
                ds[act].data['top'] = []
                ds[act].data['bottom'] = []
                ds[act].data['right'] = []
                ds[act].data['left'] = []

            else:
                # make the line
                line_act = act.replace('Set ', '')

                # Get 2nd axis label
                if not axis_name:
                    axis_name = line_act.split(' ')
                else:
                    axis_name = [word for word in axis_name if word in line_act.split(' ')]
                axis_names['2nd'] = ' '.join(axis_name)

                # Draw actuator lines
                try: # If there is output, assign both lines to 2nd axis
                    # make set point identical but thinner
                    trace[act] = p.line([], [],
                                        name=act,
                                        color=line_form_dict[line_act][0],
                                        line_width=
                                            line_form_dict[line_act][1]-0.5,
                                        line_dash='dashed')
                except KeyError: # Else just draw a dashed line for 2nd axis
                    trace[act] = p.line([], [],
                                        name=act,
                                        color=line_form_dict[act][0],
                                        line_width=line_form_dict[act][1],
                                        line_dash='dashed')

                # Assign actual and set pont of actuator to 2nd axis
                trace[act].y_range_name = '2nd'
                axis_belongs['2nd'].append(act)
                # Define lines's data source
                ds[act] = trace[act].data_source
                ds[act].data['x'] = []
                ds[act].data['y'] = []

            # Add to legend
            lgls.append((act, [trace[act]]))

        # Label Axis


        for ax in p.yaxis:
            ax.axis_label = axis_names[ax.y_range_name]
            if ax.y_range_name == 'default':
                p.y_range.names = axis_belongs[ax.y_range_name]
            else:
                p.extra_y_ranges[ax.y_range_name].names = \
                    axis_belongs[ax.y_range_name]
        # Create widgets
        window_size = Slider(title="Time Frame, secs",
                             value=3600,
                             start=5,
                             end=3600,
                             step=1)
        plots_on = CheckboxButtonGroup(labels=lines + acts,
                                       active=list(range(len(lines+acts))))

        window_size.css_classes = ['bokeh-labels']
        # Create Legend
        customlegend = Legend(items=lgls,
                              location=(0, -47),
                              label_text_font_size='12pt')
        p.add_layout(customlegend, 'left')
        # Initialize periodic callback vars
        stream_speed = 500
        df = {}
        length_dt = 30
        # Periodic Callback Function
        def stream():
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
            data, l, a, bool_acts = get_loop_snap(ip, port, reactor.idx, loop)
            # *Manipulate timestamp and dt data*
            # if first time through, assign first data point
            delon = False
            if df == {}:
                df['Timestamp'] = [data['Timestamp']]
                df['dt'] = [0]
            else:
                # if window size is same or greater than last time
                if length_dt >= last_dt:
                    # Add new timestamp and value to end of frame
                    df['Timestamp'].append(data['Timestamp'])

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
                    df['Timestamp'] = df['Timestamp'][idx:len(df['Timestamp'])]
                    df['dt'] = [ts-df['Timestamp'][0]
                                for ts in df['Timestamp']]
            # *Manipulate aspects of plot affected by signals*
            idx = 0
            if current_plts != last_plts:
                new_lgls = []
            for no, lin in enumerate(lines+acts):
                if 'Set Point' in lin:
                    tol_name = lin.replace('Set Point', 'Tolerance')
                # Update which plots are visible and build legend list
                if current_plts != last_plts:
                    if no in current_plts:
                        if 'Set Point' in lin:
                            trace[tol_name].visible = True
                        trace[lin].visible = True
                        sig_label = lin
                        new_lgls.append((sig_label, [trace[lin]]))
                    else:
                        if 'Set Point' in lin:
                            trace[tol_name].visible = False
                        trace[lin].visible = False
                # if first time through, assign first data point
                try:
                    df[lin]
                except KeyError:
                    df[lin] = [data[lin]]
                    if 'Set Point' in lin:
                        df[tol_name] = [data[tol_name]]
                    continue
                # if window size is same or greather than last time
                if length_dt >= last_dt:
                    # Add new timestamp and value to end of frame
                    df[lin].append(data[lin])
                    if 'Set Point' in lin:
                        df[tol_name].append(data[tol_name])
                    # if length of data frame is greater than specified
                    # length, remove last point, recalculate dt values
                    if delon:
                        del df[lin][0]
                        if 'Set Point' in lin:
                            del df[tol_name][0]
                # If length is smaller than last time
                else:
                    df[lin] = df[lin][idx:len(df[lin])]
                    if 'Set Point' in lin:
                        df[tol_name] = df[tol_name][idx:len(df[tol_name])]
                # Assign data to graph
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=BokehUserWarning)
                    if type(df[lin][0]) is float:
                        ds[lin].data['x'] = df['dt']
                        ds[lin].data['y'] = df[lin]
                        if 'Set Point' in lin:
                            tols = set(df[tol_name])
                            l = []
                            r = []
                            t = []
                            b = []
                            for toler in tols:
                                setpt = df[lin][df[tol_name].index(toler)]
                                l_idx = df[tol_name].index(toler)
                                l.append(df['dt'][l_idx])
                                r_idx = (len(df[tol_name]) - 1 -
                                         df[tol_name][::-1].index(toler))
                                r.append(df['dt'][r_idx])
                                t.append(setpt + toler)
                                b.append(setpt - toler)
                            ds[tol_name].data['left'] = l
                            ds[tol_name].data['right'] = r
                            ds[tol_name].data['top'] = t
                            ds[tol_name].data['bottom'] = b
                            ds[tol_name].trigger('data',
                                                 ds[tol_name].data,
                                                 ds[tol_name].data)
                    else:  # Parse the boolean actuator data
                        truths = list(compress(range(len(df[lin])), df[lin]))
                        ranges = []
                        for k, g in groupby(enumerate(truths),
                                            lambda x:x[0]-x[1]):
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
                            try:
                                t = [p.y_range.end] * len(l)
                                b = [p.y_range.start] * len(l)
                            except TypeError:
                                continue
                        ds[lin].data['left'] = l
                        ds[lin].data['right'] = r
                        ds[lin].data['top'] = t
                        ds[lin].data['bottom'] = b
                ds[lin].trigger('data', ds[lin].data, ds[lin].data)
            # Update legend
            if current_plts != last_plts:
                customlegend.items = new_lgls


        # Build the document to serve
        inputs = widgetbox(window_size)
        plot_btns = widgetbox(plots_on)
        if 'var_act_stat' not in locals():
            doc.add_root(layout([[p],
                                 [plot_btns],
                                 [inputs]],
                                sizing_mode='scale_width'))
        else:
            doc.add_root(layout([[p],
                                 [plot_btns],
                                 [inputs],
                                 [var_act_stat]],
                                sizing_mode='scale_width'))
        # Add a periodic callback to be run as defined by stream speed
        doc.add_periodic_callback(stream, stream_speed)
    return loop_graph
