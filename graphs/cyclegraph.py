import warnings
from itertools import compress, groupby
from operator import itemgetter
from bokeh.plotting import figure
from bokeh.charts import Donut
from bokeh.models.widgets import DataTable, TableColumn
from bokeh.models.widgets import Slider, CheckboxButtonGroup
from bokeh.models import Legend, ColumnDataSource
from bokeh.layouts import widgetbox, layout
from bokeh.util.warnings import BokehUserWarning
import numpy as np
from reactorhandler import get_probe_snap
import graphs.plotmodels as mods


def probe_graph_builder(ip, port, reactor, signals, phases):
    p = figure(plot_width=400, plot_height=400)
    p.wedge(x=[0], y=[0], radius=1, start_angle=0.4, end_angle=4.8,
            color="firebrick", alpha=0.6, direction="clock")
    def probe_graph(doc):


        ss_calcs = {'Time': ['Cycle Time Elapsed, min',
                             'Phase Time Elapsed, min']}