from bokeh.plotting import figure

import numpy
from bokeh.models import ColumnDataSource, LabelSet, Paragraph
from bokeh.layouts import layout
import graphs.plotmodels as mods
from controlcmdhandler import get_loop_snap
from reactorhandler import get_phases
import utils
# TODO: Elapsed cycle time and other parameters
# TODO: Reboot graph server button on flask side


def cycle_graph_builder(r, ip, port, rno):
    phases = get_phases(ip, port, rno, False)
    # Mak a list of phases and assign unique formates
    phase_ls = list(list(zip(*phases))[0])
    phase_form_dict = mods.assign_line_format(phase_ls)
    # Make list of phase colors, phase alphas, and delete 0 length phases
    phase_color_ls = []
    phase_len = []
    phase_alpha = []
    mod_phase_ls = []
    for idx, ph in enumerate(phase_ls):
        phase_color_ls.append(phase_form_dict[ph][0])
        phase_alpha.append(phase_form_dict[ph][1])
        if phases[idx][1][0] != 0:
            phase_len.append(phases[idx][1][0])
            mod_phase_ls.append(phase_ls[idx])

    def cycle_graph(doc):
        cycle_label = Paragraph(text='Hey!')
        phase_label = Paragraph(text='Hello!')
        cycle_label.css_classes = ['bokeh-titles']
        phase_label.css_classes = ['bokeh-titles']
        # Math to determine wedge sizes
        cumsum_phase_len = [0] + list(numpy.cumsum(phase_len))
        perc_phase_len = [x / cumsum_phase_len[-1]
                          for x in cumsum_phase_len]
        starts = [val*2*numpy.pi + numpy.pi/2
                  for val in perc_phase_len[:-1]]
        ends = [val*2*numpy.pi + numpy.pi/2 for val in perc_phase_len[1:]]

        # Math to determine label locations
        label_thetas = [(a+b)/2-.05 for a, b in zip(starts, ends)]
        rs = [r*0.5]*len(phase_len)
        mod_label_thetas = [x + numpy.pi if numpy.pi/2 < x < 3 * numpy.pi/2
                            else x for x in label_thetas]
        label_x, label_y = [list(x) for x in utils.pol2cart(rs,
                                                            label_thetas)]
        # Clock data source
        source = ColumnDataSource(data=dict(label_x=label_x,
                                            label_y=label_y,
                                            names=mod_phase_ls,
                                            angles=mod_label_thetas,
                                            colors=phase_color_ls))
        cycle_labels = LabelSet(x='label_x', y='label_y',
                                text='names', angle='angles',
                                background_fill_color='colors',
                                source=source)
        # a color for each pie piece
        colors = phase_color_ls
        cycle = figure(x_range=(-r-0.05, r + 0.05),
                       y_range=(-r - .05, r + .05),
                       plot_width=400,
                       plot_height=500,
                       title='Cycle Clock',
                       )
        # Pie chart wedges
        cycle.wedge(x=0, y=0, radius=r,
                    start_angle=starts,
                    end_angle=ends,
                    color=colors,
                    alpha=phase_alpha)
        # Status Line
        cycle_line = cycle.line([], [], name='cycle_status', color='black',
                                line_width=3)
        phase_status_ds = cycle_line.data_source
        phase_status_ds.data['x'] = [0, 0]
        phase_status_ds.data['y'] = [0, 0]
        # Make extra junk invisible
        cycle.xaxis.visible = False
        cycle.yaxis.visible = False
        cycle.xgrid.visible = False
        cycle.ygrid.visible = False
        cycle.outline_line_alpha = 0
        cycle.toolbar.logo = None
        cycle.toolbar_location = None
        # Format Title
        cycle.title.text_font_size = '20pt'
        cycle.title.align = 'center'

        # Callback function for streaming
        stream_speed = 500
        denom = cumsum_phase_len[-1]  # This is the denominator
        def stream():
            # Determine fraction through cycle
            data, l, a, bool_acts = get_loop_snap(ip, port, rno, 'SBR')
            for each in data:
                # TODO: User needs to label things with 'Cycle Time' and 'phase time' to get these readouts
                if 'Cycle Time' in each:
                    numer = data[each]
                    cycle_label.text = each + ': ' + str(round(data[each], 2))
                    fract = numer/denom
                elif 'Phase Time' in each:
                    phase_label.text = each + ': ' + str(round(data[each], 2))
            # Determine coordinates of clock hand
            theta = fract*2*numpy.pi + numpy.pi/2
            x, y = utils.pol2cart(r, theta)
            xs = [0, x]
            ys = [0, y]
            phase_status_ds.data['x'], phase_status_ds.data['y'] = xs, ys

        # Add form to document
        cycle.add_layout(cycle_labels)
        doc.add_root(layout([[cycle],
                             [cycle_label],
                             [phase_label]], sizing_mode='scale_width'))
        doc.add_periodic_callback(stream, stream_speed)
        return doc
    return cycle_graph