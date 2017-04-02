import json
import re
import warnings
from flask import render_template, request, redirect, flash, url_for #Flask
from flask_admin import Admin #Flask-Admin
from bokeh.embed import autoload_server
import config
import reactorhandler as rct
import calconstanthandler as calconst
import constanthandler as const
import controlcmdhandler as cmd
import isehandler as isehd
import utils
from __init__ import app, db, models
import forms as fo
    # TODO: Replace compound shorts with names when displaying
# Setup reactor database for easy query
reactors = models.Reactor.query.order_by(models.Reactor.idx).all()


# Admin Stuff
admin = Admin(app, name='Winkler Lab Reactor Manager', template_mode='bootstrap3')
admin.add_view(models.ReactorModelView(models.Reactor, db.session))
admin.add_view(models.ControllerModelView(models.Controller, db.session))


# Main Page
@app.route('/', methods=['GET', 'POST'], alias=False, strict_slashes=False)
def select_reactor():
    # TODO: Admin authetification?
    rct_list = []
    for rct in reactors:
        rct_list.append((str(rct.idx), str(rct.idx)+' - '+rct.descrip))
    SelectForm = fo.create_reactor_form(rct_list)
    form = SelectForm()
    if form.validate_on_submit():
        return redirect(url_for('control_reactor',
                                reactorno=form.reactor_no.data))
    return render_template('index.html',
                           form=form,
                           details=reactors)


@app.route('/reactor/<int:reactorno>/current', strict_slashes=False)
def send_current(reactorno):
    ip, port = utils.get_controller_info(reactorno, True)
    reactorno = reactorno
    print('Updating')
    current, loop_list = cmd.get_current(ip, port, reactorno)
    return json.dumps(current)

@app.route('/could_not_find/<int:reactorno>', methods=['GET', 'POST'], strict_slashes=False)
def could_not_find(reactorno):
    return render_template('could_not_find.html', reactorno=reactorno)

@app.route('/reactor/<int:reactorno>', methods=['GET', 'POST'], strict_slashes=False)
def control_reactor(reactorno):
    ip, port = utils.get_controller_info(1, True)
    status = None
    loop_form_dict, current, loop_list = fo.build_control_forms(ip,
                                                                port,
                                                                reactorno)
    if loop_form_dict is None:
        return redirect(url_for('could_not_find',
                                reactorno=reactorno))
    script_dict = {'Probes': autoload_server(model=None,
                                             app_path='/R' +
                                                      str(reactorno) +
                                                      '_probes')}
    for loop in loop_list:
        appname = '/R' + str(reactorno) + '_'+loop
        # TODO: Control Loop Graphs
        script_dict[loop] = None  # autoload_server(model=None, app_path=appname)
    json_current = json.dumps(current)
    if request.method == 'POST':
        latest, loop_list = cmd.get_current(ip, port, reactorno)
        [loop, action, params] = cmd.get_submitted(request.form, latest)
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
                           graphs=script_dict,
                           current=json_current,
                           reactor=(reactorno, ip, port),
                           all_actions=utils.ACTIONS,
                           all_loops=loop_list,
                           update=5000)


@app.route('/reactor/<int:reactorno>/CalConstants',
           methods=['GET', 'POST'],
           strict_slashes=False)
def calconstants(reactorno):
    ip, port = utils.get_controller_info(1, True)
    formclass, slopes, ints, sigs = fo.build_calconstant_form(
        ip, port, reactorno)
    form = formclass()
    script_dict = {}
    for sig in sigs:
        if 'VFD' in sig:
            split_sig = sig.split(' ')
            joined_sig = split_sig[0]+' '+split_sig[1]+' Flowrate'
            if joined_sig not in list(script_dict.keys()):
                appname = '/R' + str(reactorno)+'_' + \
                          joined_sig.replace(' ', '_')
        else:
            appname = '/R' + str(reactorno)+'_' + sig.replace(' ', '_')
        script_dict[sig] = autoload_server(model=None, app_path=appname)
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
                           scripts=script_dict,
                           form=form,
                           slopes=slopes,
                           ints=ints)


@app.route('/reactor/<int:reactorno>/ise', strict_slashes=False)
def make_ise_list(reactorno):
    ip, port = utils.get_controller_info(reactorno, config.DEBUG)
    signals = rct.get_signal_list(ip, port, reactorno)
    ise_list = [(x, (x.split(' '))[0]) for x in signals if 'ISE' in x]
    return render_template('iselist.html',
                           reactor=reactorno,
                           ise_list=ise_list)


@app.route('/reactor/<int:reactorno>/ise/<ise>',
           methods= ['GET', 'POST'],
           strict_slashes=False)


def make_ise_manager(reactorno, ise):
    ip, port = utils.get_controller_info(reactorno, config.DEBUG)
    form_dict, current = fo.build_ise_control_forms(ip, port, reactorno, ise)
    ise_setparam_forms = list(form_dict.keys())
    first = ise + ' ISE Parameters'
    del ise_setparam_forms[ise_setparam_forms.index(first)]
    ise_setparam_forms.insert(0, first)
    # TODO: cRIO Side Add Questionmark to Na ISE Data and units to NH4 data
    graphs = autoload_server(model=None,
                             app_path=
                             '/R' + str(reactorno) + '_' +
                             ise + '_ISE_rel_sigs')
    # TODO: Graph ise data
    if request.method == 'POST':
        command_dict = isehd.get_submitted(request.form, current)
        status = isehd.send_to_reactor(ip, port, reactorno, ise, command_dict,
                                       write=True)
        flash(status)
    return render_template('ise.html',
                           chems=utils.CHEMS,
                           reactor=reactorno,
                           ise=ise,
                           graphscript=graphs,
                           form_dict=form_dict,
                           ise_setparam_forms=ise_setparam_forms,
                           current=current)


@app.route('/reactor/<int:reactorno>/Constants',
           methods=['GET', 'POST'],
           strict_slashes=False)
def constants(reactorno):
    ip, port = utils.get_controller_info(reactorno, config.DEBUG)
    ConstantForm, defaults = fo.build_constant_form(ip, port, reactorno)
    form = ConstantForm()
    if form.validate_on_submit():
        name, value = const.get_submitted(form)
        status = const.submit_to_reactor(ip, port, reactorno, name, value)
        flash(status)
    return render_template('OtherConstants.html',
                           chems=utils.CHEMS,
                           reactor=reactorno,
                           form=form,
                           defaults=defaults)
