from bokeh.plotting import figure, curdoc
from bokeh.driving import linear
from bokeh.models import Paragraph
from bokeh.layouts import column
from bokeh.models import Legend

import random

p = figure(plot_width=300, plot_height=300)
r1 = p.line([], [], color="firebrick", line_width=2)
r2 = p.line([], [], color="navy", line_width=2)
ds1 = r1.data_source
ds2 = r2.data_source
avg1 = Paragraph(text='Average Val #1 is:')
avg2 = Paragraph(text='Average Val #2 is:')

@linear()
def update(step):
    ds1.data['x'].append(step)
    ds1.data['y'].append(random.randint(0, 100))
    ds2.data['x'].append(step)
    ds2.data['y'].append(random.randint(0, 100))
    ds1.trigger('data', ds1.data, ds1.data)
    ds2.trigger('data', ds2.data, ds2.data)
    mean1 = sum(ds1.data['x'])/float(len(ds1.data['x']))
    mean2 = sum(ds2.data['x'])/float(len(ds2.data['x']))
    avg1.text = 'Average Val #2 is: ' + str(mean1)
    avg2.text = 'Average Val #2 is: ' + str(mean2)
curdoc().add_root(column(p,avg1,avg2))

# Add a periodic callback to be run every 500 milliseconds
curdoc().add_periodic_callback(update, 500)

