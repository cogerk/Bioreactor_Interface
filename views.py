import json
from flask import render_template, request, redirect, flash, url_for #Flask
from forms import build_calconstant_form, build_control_forms, build_constant_form, create_reactor_form #Flask-WTF
from flask_admin import Admin, BaseView, expose #Flask-Admin
from __init__ import app, db, models
import utils
import constanthandler as const
import calconstanthandler as calconst
import controlcmdhandler as cmd
import graph

# Admin Stuff
admin = Admin(app, name='Winkler Lab Reactor Manager', template_mode='bootstrap3')
admin.add_view(models.ReactorModelView(models.Reactor, db.session))
admin.add_view(models.ControllerModelView(models.Controller, db.session))

# Main Page
@app.route('/', methods=['GET', 'POST'])
def select_reactor():
    # TODO: Admin authetification?
    # TODO: Quick Edit Button?
    reactors = models.Reactor.query.order_by(models.Reactor.idx).all()
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
    ip = '128.208.236.57'
    port = 8001
    reactorno = reactorno
    current, loop_list = cmd.get_current(ip, port, reactorno)
    return json.dumps(current)


@app.route('/reactor/<int:reactorno>', methods=['GET', 'POST'])
def control_reactor(reactorno):
    # TODO: Debug Submission
    #  TODO: Add data visualization
    # TODO: Add Probe and other data display
    # TODO: Do we need current in this function?
    # TODO: GET IP/ Port from database
    ip = '128.208.236.57'
    port = 8001
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
    return render_template('reactor.html',
                           loop_form_dict=loop_form_dict,
                           graphscript=script,
                           graphdiv=div,
                           current=current,
                           reactor=(reactorno, ip, port),
                           all_actions=utils.ACTIONS,
                           all_loops=loop_list,
                           update=10000)


@app.route('/reactor/<int:reactorno>/CalConstants', methods=['GET', 'POST'])
def calconstants(reactorno):
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


@app.route('/reactor/<int:reactorno>/Constants', methods=['GET', 'POST'])
def constants(reactorno):
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