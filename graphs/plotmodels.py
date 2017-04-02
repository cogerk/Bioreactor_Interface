"""
Models and formatters for bokeh graphs
Written By: Kathryn Cogert
Mar 20 2017
"""
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.models import Paragraph, Range1d, LinearAxis
from bokeh.palettes import Dark2_6 as Palette
# TODO: What is range for ORP Probe?

# Assign plot colors to common things
default_form_dict = {}
default_line_width = 2
default_form_dict['DO'] = (Palette[0], default_line_width)
default_form_dict['pH'] = (Palette[1], default_line_width)
default_form_dict['ORP'] = (Palette[2], default_line_width)
default_form_dict['NH4'] = (Palette[3], default_line_width)


def assign_line_format(sigs):
    form_dict = {}
    count = len(list(default_form_dict.keys()))
    linewidth = default_line_width
    for idx, sig in enumerate(sigs):
        if sig in list(default_form_dict.keys()):
            form_dict[sig] = default_form_dict[sig]
        else:
            if count == 5:
                count = 0
                linewidth += 0.5
            else:
                count += 1
            form_dict[sig] = (Palette[count], linewidth)
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
        p.extra_y_ranges = {'2nd': Range1d(start=0, end=1000)}
        p.add_layout(LinearAxis(y_range_name='2nd',
                                axis_label_text_font_size = '14pt',
                                major_label_text_font_size = '12pt'),
                     'right')
    return p
