import json

from flask import render_template, request, redirect, flash, url_for #Flask
from flask_admin import Admin #Flask-Admin

import calconstanthandler as calconst
import constanthandler as const
import controlcmdhandler as cmd
import utils
from __init__ import app, db, models
from forms import build_calconstant_form, build_control_forms, build_constant_form, create_reactor_form #Flask-WTF
from graphs import streaming

# Setup reactor database for easy query
reactors = models.Reactor.query.order_by(models.Reactor.idx).all()

# Admin Stuff
admin = Admin(app, name='Winkler Lab Reactor Manager', template_mode='bootstrap3')
admin.add_view(models.ReactorModelView(models.Reactor, db.session))
admin.add_view(models.ControllerModelView(models.Controller, db.session))

# Main Page
@app.route('/', methods=['GET', 'POST'])
def select_reactor():
    # TODO: Admin authetification?
    rct_list = []
    for rct in reactors:
        rct_list.append((str(rct.idx), str(rct.idx)+' - '+rct.descrip))
    SelectForm = create_reactor_form(rct_list)
    form = SelectForm()
    if form.validate_on_submit():
        #flash('Redirecting to ' + form.reactor_no.data + ' control panel')
        return redirect(url_for('control_reactor',reactorno=form.reactor_no.data))
    return render_template('index.html', form=form, details=reactors)


@app.route('/reactor/<int:reactorno>/current')
def send_current(reactorno):
    ip, port = utils.get_controller_info(reactorno, True)
    reactorno = reactorno
    print('Updating')
    current, loop_list = cmd.get_current(ip, port, reactorno)
    return json.dumps(current)


@app.route('/reactor/<int:reactorno>', methods=['GET', 'POST'])
def control_reactor(reactorno):
    # TODO: Debug Submission
    #  TODO: Add data visualization
    # TODO: Add Probe and other data display
    ip, port = utils.get_controller_info(1, True)
    status = None
    loop_form_dict, current, loop_list = build_control_forms(ip, port, reactorno)
    json_current = json.dumps(current)
    script, div = 'stuff'
    if request.method == 'POST':
        print('Comparing')
        latest, loop_list = cmd.get_current(ip, port, reactorno)
        [loop, action, params] = cmd.get_submitted(request.form, latest)
        print('old', latest[loop][loop+'_'+action])
        print('new', params)
        status = cmd.submit_to_reactor(ip,
                                       port,
                                       reactorno,
                                       loop,
                                       action,
                                       params,
                                       current)
        flash(status)
    return render_template('reactor.html',
                           loop_form_dict=loop_form_dict,
                           status=status,
                           graphscript=script,
                           graphdiv=div,
                           current=json_current,
                           reactor=(reactorno, ip, port),
                           all_actions=utils.ACTIONS,
                           all_loops=loop_list,
                           update=5000)


@app.route('/reactor/<int:reactorno>/CalConstants', methods=['GET', 'POST'])
def calconstants(reactorno):
    ip, port = utils.get_controller_info(1, True)
    CalConstantForm, slopes, ints = build_calconstant_form(ip, port, reactorno)
    form = CalConstantForm()
    script, div = run.make_graph()
    if form.validate_on_submit():
        signal, values = calconst.get_submitted(form)
        statuses = calconst.submit_to_reactor(ip,
                                              port,
                                              reactorno,
                                              signal,
                                              values)
        for status in statuses[0]:
            flash(status)
    return render_template('CalConstants.html',
                           reactor=reactorno,
                           form=form,
                           graphscript=script,
                           graphdiv=div,
                           slopes=slopes,
                           ints=ints)


@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/reactor/<int:reactorno>/Constants', methods=['GET', 'POST'])
def constants(reactorno):
    ip, port = utils.get_controller_info(1, True)
    ConstantForm, defaults = build_constant_form(ip, port, reactorno)
    form = ConstantForm()
    if form.validate_on_submit():
        name, value = const.get_submitted(form)
        status = const.submit_to_reactor(ip, port, reactorno, name, value)
        flash(status)
    return render_template('OtherConstants.html',
                           reactor=reactorno,
                           form=form,
                           defaults=defaults)