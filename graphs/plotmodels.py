"""
Models and formatters for bokeh graphs
Written By: Kathryn Cogert
Mar 20 2017
"""
from copy import copy
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.models import Paragraph, DataRange1d, LinearAxis
from bokeh.palettes import Dark2_6 as Palette
# TODO: What is range for ORP Probe?

# Assign plot colors to common things
default_form_dict = {}
default_line_width = 2
default_form_dict['pH'] = (Palette[0], default_line_width)
default_form_dict['DO'] = (Palette[1], default_line_width)
default_form_dict['ORP'] = (Palette[2], default_line_width)
default_form_dict['NH4'] = (Palette[3], default_line_width)
default_form_dict['NH4 ISE'] = (Palette[3], default_line_width)
#TODO: WHy doesn't this work?
def assign_line_format(sigs):
    form_dict = {}
    counts = copy(Palette)
    copy_sigs = copy(sigs)
    linewidth = default_line_width
    # Remove default signals from list
    for def_sig in list(default_form_dict.keys()):
        if def_sig in copy_sigs:
            form_dict[def_sig] = default_form_dict[def_sig]
            counts.remove(default_form_dict[def_sig][0])
            copy_sigs.remove(def_sig)
    # Go through the rest of signals and assign unique color/line thickness
    for idx, sig in enumerate(copy_sigs):
        if len(counts) == 0:
            counts = copy(Palette)
            linewidth += 0.5
            form_dict[sig] = (counts[0], linewidth)
        else:
            form_dict[sig] = (counts[0], linewidth)
            del counts[0]
    return form_dict


def steady_state_calcs(width):
    calc_title = Paragraph(text='Steady State Analysis of Signal', width=width)
    avg_label = Paragraph(text='Average:', width=width)
    diff_label = Paragraph(text='Differential:', width=width)
    stdev_label = Paragraph(text='Standard Deviation:', width=width)
    calc_title.css_classes = ['bokeh-titles']
    avg_label.css_classes = ['bokeh-labels']
    diff_label.css_classes = ['bokeh-labels']
    stdev_label.css_classes = ['bokeh-labels']
    return calc_title, avg_label, stdev_label, diff_label


def steady_state_stat():
    status = Paragraph(text='Invalid')
    status.css_classes = ['btn btn-block btn-secondary active']
    return status


def format_plot(p, multi=False):
    p.toolbar_sticky = False
    p.xaxis.formatter = DatetimeTickFormatter(minsec=['%Mm %Ss'],
                                              minutes=['%Mm %Ss'],
                                              hourmin=['%Mm %Ss'],
                                              hours=['%Mm %Ss'],
                                              days=['%Ss'],
                                              months=['%Ss'],
                                              years=['%Ss'])
    p.xaxis.axis_label = 'Time'
    p.yaxis.axis_label = ''
    p.title.text_font_size = '20pt'
    p.title.align = 'center'
    p.xaxis.axis_label_text_font_size = '14pt'
    p.xaxis.major_label_text_font_size = '12pt'
    p.yaxis.axis_label_text_font_size = '14pt'
    p.yaxis.major_label_text_font_size = '12pt'
    if multi:
        p.extra_y_ranges = {'2nd': DataRange1d()}
        p.add_layout(LinearAxis(y_range_name='2nd',
                                axis_label_text_font_size = '14pt',
                                major_label_text_font_size = '12pt',
                                axis_line_dash='dashed'),
                     'right')
    return p
