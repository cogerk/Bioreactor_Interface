"""
Create a graph of all probes for a given reactor
Written 3/20/17
By: Kathryn Cogert
"""
# TODO: fix buttons
import warnings
from bokeh.plotting import figure
from bokeh.models.widgets import Slider, CheckboxButtonGroup
from bokeh.models import Legend, Range1d, LinearAxis
from bokeh.layouts import widgetbox, layout
from bokeh.util.warnings import BokehUserWarning
import numpy as np
from isehandler import get_ise_snap
import graphs.plotmodels as mods


def ise_graph_builder(ip, port, reactor, ise_sigs):
    """
    Builds a function of all reactor signals to serve in the bokeh server
    :param ip: str, the cRIO IP address
    :param port: int, the port of the webservice
    :param reactor: Reactor class, # of the reactor & description
    :param ise_sigs: list str, list of signals associated with the ISE
    :return: function(doc)
    """
    def ise_graph(doc):
        """
        Function to generate document for server
        :param doc: bokeh document
        :return:
        """
        # Define and format the figuree
        ise = ise_sigs[0]
        ptitle = 'Reactor #' + str(reactor) + ' ' + ise + ' Graph'
        p = figure(plot_width=800,
                   x_axis_type='datetime',
                   plot_height=500,
                   title=ptitle)
        p = mods.format_plot(p)
        p.extra_y_ranges = {'Raw': Range1d(start=0, end=.01),
                            'Eq': Range1d(start=0, end=1)}
        p.add_layout(LinearAxis(y_range_name='Raw',
                                axis_label='Raw Value, mol/L',
                                axis_label_text_font_size='14pt',
                                axis_line_dash='dotted',
                                major_label_text_font_size='12pt'), 'right')
        p.add_layout(LinearAxis(y_range_name='Eq',
                                axis_label='Equilibrium Approach, mV/s',
                                axis_label_text_font_size='14pt',
                                axis_line_dash='dashdot',
                                major_label_text_font_size='12pt'), 'right')

        # Generate a unique line format for each probe
        line_form_dict = mods.assign_line_format(ise_sigs)

        # Initiate data dictionaries and line dictionary
        trace = {}
        ds = {}
        all_plots = []

        # Define Lines and list all plots
        for sig in ise_sigs:
            # make the line
            # Make axis picker
            if 'ISE' in sig:
                # If it's an ISE signal, make corrected raw and signal graphs
                ise_correct = sig + ' Corrected Value, mg/L'
                ise_raw = sig + ' Raw Value, mol/L'
                ise_eq = sig + ' Equilibrium Approach, mV/s'

                # Corrected Graphs
                # Build Graph
                trace[ise_correct] = p.line([],
                                            [],
                                            color=line_form_dict[sig][0],
                                            line_width=line_form_dict[sig][1])
                # Assign data dict
                ds[ise_correct] = trace[ise_correct].data_source
                ds[ise_correct].data['x'] = []
                ds[ise_correct].data['y'] = []

                # Raw Graph
                trace[ise_raw] = p.line([],
                                        [],
                                        color=line_form_dict[sig][0],
                                        line_width=line_form_dict[sig][1],
                                        line_dash='dotted',
                                        y_range_name='Raw')
                ds[ise_raw] = trace[ise_raw].data_source
                ds[ise_raw].data['x'] = []
                ds[ise_raw].data['y'] = []

                # Equilibrium Graph
                trace[ise_eq] = p.line([],
                                       [],
                                       color=line_form_dict[sig][0],
                                       line_width=line_form_dict[sig][1],
                                       line_dash='dashdot',
                                       y_range_name='Eq')
                ds[ise_eq] = trace[ise_eq].data_source
                ds[ise_eq].data['x'] = []
                ds[ise_eq].data['y'] = []

                # Add graphs to legend
                all_plots.append(ise_correct)
                all_plots.append(ise_raw)
                all_plots.append(ise_eq)

            else:
                # Build Graph
                trace[sig] = p.line([],
                                    [],
                                    color=line_form_dict[sig][0],
                                    line_width=line_form_dict[sig][1])
                # Assign data dict
                ds[sig] = trace[sig].data_source
                ds[sig].data['x'] = []
                ds[sig].data['y'] = []

                # Add graphs to legend

                all_plots.append(sig)
        # Build Legend
        dat, units = get_ise_snap(ip, port, reactor, ise)
        lgls = []
        for each in all_plots:
            lgls.append((each, [trace[each]]))
        # TODO: Show if steady state, data is valid, etc.


        # Create widgets
        window_size = Slider(title="Time Frame, secs",
                             value=600,
                             start=5,
                             end=3600,
                             step=1)
        plots_on = CheckboxButtonGroup(labels=all_plots,
                                       active=list(range(len(all_plots))))
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
        length_diff_dt = 30

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
            new_data, u = get_ise_snap(ip, port, reactor, ise)

            # *Manipulate timestamp and dt data*
            # If first time through, assign first data point
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
                               (last_dt - x[1].total_seconds()) <=
                               length_dt][0]
                    except IndexError:
                        idx = 0
                    df['Timestamp'] = df['Timestamp'][idx:-1]
                    df['dt'] = [ts-df['Timestamp'][0]
                                for ts in df['Timestamp']]
            # *Manipulate aspects of plot affected by signals*
            idx = 0
            if current_plts != last_plts:
                new_lgls = []
            for no, sig in enumerate(all_plots):
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



            # Update legend
            if current_plts != last_plts:
                customlegend.items = new_lgls

        # Build the document to serve
        inputs = widgetbox(window_size, width=p.plot_width)

        plot_btns = widgetbox(plots_on)
        doc.add_root(layout([[p],
                             [plot_btns],
                             [inputs]],
                            sizing_mode='scale_width'))
        # Add a periodic callback to be run as defined by stream speed
        doc.add_periodic_callback(stream, stream_speed)

    return ise_graph

