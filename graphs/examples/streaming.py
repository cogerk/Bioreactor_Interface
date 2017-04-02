from bokeh.plotting import figure, curdoc
from bokeh.driving import linear
from bokeh.models import Paragraph
from bokeh.layouts import column, widgetbox
from bokeh.models.widgets import CheckboxButtonGroup
from bokeh.models import Legend
# TODO: Report bug when legend is on right side
import random


def stream_ex(doc):
    plot_list = ['Signal 1', 'Signal 2']
    plot_cols = ['firebrick', 'navy']
    length = 10
    p = figure(plot_width=300, plot_height=300)
    r={}
    ds={}
    for no, each in enumerate(plot_list):
        r[each] = p.line([], [], color=plot_cols[no], line_width=2)
        ds[each] = r[each].data_source

    plots_on = CheckboxButtonGroup(labels=plot_list, active=list(range(len(plot_list))))


    @linear()
    def update(step):
        # Initialize Plot Selector Vals
        global last_plts
        global current_plts
        try:
            current_plts
        except NameError:
            current_plts = plots_on.active
        last_plts = current_plts
        current_plts = plots_on.active
        # Add New Data
        for no, each in enumerate(plot_list):
            ds[each].data['x'].append(step)
            ds[each].data['y'].append(random.randint(0, 100))
            ds[each].trigger('data', ds[each].data, ds[each].data)
            # update plot visiblity
            if current_plts != last_plts:
                if no in current_plts:
                    r[each].visible = True
                else:
                    r[each].visible = False

    wids = widgetbox(plots_on)
    curdoc().add_root(column(p, wids))

    # Add a periodic callback to be run every 500 milliseconds
    curdoc().add_periodic_callback(update, 500)

