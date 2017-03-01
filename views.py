import json
from flask import Flask, render_template, request, redirect, flash, url_for #Flask
from forms import Settings, build_calconstant_form, build_control_forms, build_constant_form #Flask-WTF
from flask_admin import Admin #Flask-Admin
from flask_admin.contrib.sqla import ModelView #Flask-SQLAlchemy
from __init__ import app, db, models
import utils
import constanthandler as const
import calconstanthandler as calconst
import controlcmdhandler as cmd
import graph

# TODO: How to put secret key in a configs file
# Admin Stuff
admin = Admin(app, name='Winkler Lab Reactor Manager', template_mode='bootstrap3')
#admin.add_view(ModelView(models.Reactor, db.session))
#admin.add_view(ModelView(Post, db.session))

@app.route('/', methods=['GET', 'POST'])
def select_reactor():
    form = Settings()
    if form.validate_on_submit():
        #TODO: How to keep email, IP, and port to reactor control page
        #flash('Redirecting to ' + form.reactor_no.data + ' control panel')
        return redirect(url_for(form.reactor_no.data))
    return render_template('index.html', form=form)


@app.route('/R1/Current', methods=['GET', 'POST'])
def send_current():
    ip = '128.208.236.57'
    port = 8001
    reactorno = 1
    current, loop_list = cmd.get_current(ip, port, reactorno)
    return json.dumps(current)

@app.route('/R1', methods=['GET', 'POST'])
def R1():
    # TODO: generalize for all reactors
    #  TODO: Add data visualization
    # TODO: Add Probe and other data display
    # TODO: Do we need current in this function?
    ip = '128.208.236.57'
    port = 8001
    reactorno = 1
    loop_form_dict, current, loop_list = build_control_forms(ip, port, reactorno)
    script, div = graph.make_graph()
    if request.method == 'POST':
        [loop, action, params] = cmd.get_submitted(request.form, current)
        status = cmd.submit_to_reactor(ip,
                                       port,
                                       reactorno,
                                       loop,
                                       action,
                                       params)
    return render_template('R1.html',
                           loop_form_dict=loop_form_dict,
                           graphscript=script,
                           graphdiv=div,
                           current=current,
                           all_actions=utils.ACTIONS,
                           all_loops=loop_list,
                           update=10000)


@app.route('/R1/CalConstants', methods=['GET', 'POST'])
def calconstants():
    reactorno = 1
    ip = '128.208.236.57'
    port = 8001
    CalConstantForm, slopes, ints = build_calconstant_form(ip, port, reactorno)
    form = CalConstantForm()
    if form.validate_on_submit():
        signal, values = calconst.get_submitted(form)
        statuses = calconst.submit_to_reactor(ip,
                                              port,
                                              reactorno,
                                              signal,
                                              values)
        for status in statuses:
            flash(status)
    return render_template('CalConstants.html',
                           form=form,
                           slopes=slopes,
                           ints=ints)


@app.route('/R1/Constants', methods=['GET', 'POST'])
def constants():
    reactorno = 1
    ip = '128.208.236.57'
    port = 8001
    ConstantForm, defaults = build_constant_form(ip, port, reactorno)
    print(defaults)
    form = ConstantForm()
    if form.validate_on_submit():
        name, value = const.get_submitted(reactorno, form)
        status = const.submit_to_reactor(ip, port, reactorno, name, value)
        flash(status)
    return render_template('OtherConstants.html',
                           form=form,
                           defaults=defaults)