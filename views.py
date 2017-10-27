import json
import warnings
from flask import render_template, request, redirect, flash, url_for
from flask_admin import Admin
from bokeh.embed import server_document
import config
import customerrs
import reactorhandler as rct
import calconstanthandler as calconst
import constanthandler as const
import controlcmdhandler as cmd
import isehandler as isehd
import dbhandler
import utils
from __init__ import app, db, models
import forms as fo
import sqlalchemy.exc
import create_db
# User needs status clusters titled as 'DOData'
# TODO: Labview add totalizers to all actuators
# TODO: SBR Control Page
# TODO: Improved Commenting
# Setup reactor database for easy query

# Build models
ControllerModelView, \
    ReactorModelView, \
    Reactor, \
    Controller, \
    LoopTable, \
    SignalTable = models.create_classes()

bokeh_server = 'http://localhost:5006/'

# Find database if present, if not, make new
try:
    reactors = Reactor.query.order_by(Reactor.idx).all()
    update = True
except sqlalchemy.exc.OperationalError:
    print('Database is incorrectly formatted or empty. '
          'Please populate w/ first reactor')
    create_db.make_db(Reactor, Controller, debug=config.DEBUG)
    reactors = Reactor.query.order_by(Reactor.idx).all()
    update = False

# Update loops for each reactor
if update:
    for r in reactors:
        get_port = r.controller.debug_port \
            if config.DEBUG else r.controller.port
        try:
            r_loops = rct.get_loops(r.controller.ip, get_port, r.idx)
            r_signals = rct.get_signal_list(r.controller.ip, get_port, r.idx)
        except customerrs.CannotReachReactor as e:
            warnings.warn(str(e), customerrs.CannotReachReactorWarn)
            continue
        r.loops = list(map(LoopTable, r_loops))
        r.signals = list(map(SignalTable, r_signals))
        db.session.commit()



# Admin Stuff
admin = Admin(app,
              name='Winkler Lab Reactor Manager',
              template_mode='bootstrap3')
admin.add_view(ReactorModelView(Reactor, db.session))
admin.add_view(ControllerModelView(Controller, db.session))


# Main Page
@app.route('/', methods=['GET', 'POST'], alias=False, strict_slashes=False)
def select_reactor():
    # TODO: Admin authetification?
    rct_list = []
    for rctr in reactors:
        rct_list.append((str(rctr.idx), str(rctr.idx)+' - '+rctr.descrip))
    select_form = fo.create_reactor_form(rct_list)
    form = select_form()
    if form.validate_on_submit():
        return redirect(url_for('control_reactor',
                                reactorno=form.reactor_no.data))
    return render_template('index.html',
                           form=form,
                           details=reactors)


@app.route('/reactor/<int:reactorno>/current', strict_slashes=False)
def send_current(reactorno):
    ip, port = dbhandler.get_controller_info(reactorno, debug=config.DEBUG)
    reactorno = reactorno
    print('Updating')
    current, loop_list = cmd.get_current(ip, port, reactorno)
    return json.dumps(current)


@app.route('/could_not_find_r/<int:reactorno>',
           methods=['GET', 'POST'],
           strict_slashes=False)
def could_not_find_r(reactorno):
    return render_template('could_not_find_r.html', reactorno=reactorno)


@app.route('/could_not_find_c/<int:reactorno>',
           methods=['GET', 'POST'],
           strict_slashes=False)
def could_not_find_c(reactorno):
    return render_template('could_not_find_c.html', reactorno=reactorno)


@app.route('/reactor/<int:reactorno>',
           methods=['GET', 'POST'],
           strict_slashes=False)
def control_reactor(reactorno):
    ip, port = dbhandler.get_controller_info(1, debug=config.DEBUG)
    status = None
    try:
        loop_form_dict, current, loop_list = fo.build_control_forms(ip,
                                                                    port,
                                                                    reactorno)
    except customerrs.CannotReachReactor as e:
        print(e)
        return redirect(url_for('could_not_find_r', reactorno=reactorno))
    except customerrs.CannotReachController as e:
        print(e)
        return redirect(url_for('could_not_find_c', reactorno=reactorno))
    script_dict = {'Probes': server_document(url=bokeh_server + 'R' +
                                                      str(reactorno) +
                                                      '_probes')}

    if 'SBR' in loop_list:
        script_dict['Cycle'] = server_document(url=bokeh_server + 'R' +
                                                        str(reactorno) +
                                                        '_cycle')
    revised_loop_list = []
    for loop in loop_list:
        if type(current[loop]) is str:
            flash(current[loop])
            continue
        else:
            revised_loop_list.append(loop)
        for act in utils.ACTIONS:
            if act != 'Status':
                if type(current[loop][loop+'_'+act]) is str:
                    flash(current[loop][loop+'_'+act])
        if loop != 'SBR':
            appname = '/R' + str(reactorno) + '_'+loop
            # TODO: Control Loop Graphs
            script_dict[loop] = None  # autoload_server(model=None, app_path=appname)
    json_current = json.dumps(current)
    if request.method == 'POST':
        latest, loop_list = cmd.get_current(ip, port, reactorno)
        [loop, actions, params] = cmd.get_submitted(request.form, latest)
        status = cmd.submit_to_reactor(ip,
                                       port,
                                       reactorno,
                                       loop,
                                       actions,
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
                           all_loops=revised_loop_list,
                           update=5000)


@app.route('/reactor/<int:reactorno>/CalConstants',
           methods=['GET', 'POST'],
           strict_slashes=False)
def calconstants(reactorno):
    ip, port, crio = dbhandler.get_controller_info(reactorno,
                                                   debug=config.DEBUG,
                                                   crio=True)
    try:
        signal_list, slopes, ints, status = calconst.get_all_current(ip,
                                                                     port,
                                                                     crio,
                                                                     reactorno)
    except customerrs.CannotReachReactor as e:
        print(e)
        return redirect(url_for('could_not_find_r',
                                reactorno=reactorno))
    except customerrs.CannotReachController as e:
        print(e)
        return redirect(url_for('could_not_find_c',
                                ip=ip))
    formclass = fo.build_calconstant_form(signal_list,
                                          slopes,
                                          ints)
    # TODO: Flash status with jquery as well on change
    # TODO: Disable fields if you can't find the variable error looks like:
    # 'Error: Could Not Find Any Variables in ni.var.psp://crio1-winklerlab/R1pHVariablesR1pHCalibrationConstants Ensure All Calibration Variables are Located here.'
    for each in status[signal_list[0]]:
        flash(each)
    form = formclass()
    script_dict = {}
    for sig in signal_list:
        if 'VFD' in sig:
            split_sig = sig.split(' ')
            joined_sig = split_sig[0]+' '+split_sig[1]+' Flowrate'
            if joined_sig not in list(script_dict.keys()):
                appname = '/R' + str(reactorno)+'_' + \
                          joined_sig.replace(' ', '_')
        else:
            appname = 'R' + str(reactorno)+'_' + sig.replace(' ', '_')
        script_dict[sig] = server_document(url=bokeh_server + appname)
    if form.validate_on_submit():
        signal, values = calconst.get_submitted(form)
        statuses = calconst.submit_to_reactor(reactorno,
                                              signal,
                                              values)
        for status in statuses[0]:
            flash(status)
    return render_template('CalConstants.html',
                           reactor=reactorno,
                           scripts=script_dict,
                           form=form,
                           slopes=slopes,
                           ints=ints,
                           status=status)


@app.route('/reactor/<int:reactorno>/ise', strict_slashes=False)
def make_ise_list(reactorno):
    ip, port = dbhandler.get_controller_info(reactorno, config.DEBUG)
    signals = rct.get_signal_list(ip, port, reactorno)
    ise_list = [(x, (x.split(' '))[0]) for x in signals if 'ISE' in x]
    return render_template('iselist.html',
                           reactor=reactorno,
                           ise_list=ise_list)


@app.route('/reactor/<int:reactorno>/ise/<ise>',
           methods=['GET', 'POST'],
           strict_slashes=False)
def make_ise_manager(reactorno, ise):
    ip, port = dbhandler.get_controller_info(reactorno, config.DEBUG)
    form_dict, current = fo.build_ise_control_forms(ip, port, reactorno, ise)
    ise_setparam_forms = list(form_dict.keys())
    first = ise + ' ISE Parameters'
    del ise_setparam_forms[ise_setparam_forms.index(first)]
    ise_setparam_forms.insert(0, first)
    graphs = server_document(url=bokeh_server + 'R' + str(reactorno) + '_' +
                             ise + '_ISE_rel_sigs')
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
    ip, port, crio = dbhandler.get_controller_info(reactorno,
                                                   debug=config.DEBUG,
                                                   crio=True)
    try:
        other_constants = const.get_all_current(ip, port, crio, reactorno)
    except customerrs.CannotReachReactor as e:
        print(e)
        return redirect(url_for('could_not_find_r',
                                reactorno=reactorno))
    except customerrs.CannotReachController as e:
        print(e)
        return redirect(url_for('could_not_find_c',
                                reactorno=reactorno))
    if len(other_constants) == 0:
        return render_template('NoConstants.html',
                               reactorno=reactorno)
    ConstantForm = fo.build_constant_form(constants)
    form = ConstantForm()
    if form.validate_on_submit():
        name, value = const.get_submitted(form)
        status, v = const.submit_to_reactor(ip,
                                            port,
                                            reactorno,
                                            crio,
                                            name,
                                            value)
        flash(status)
    return render_template('OtherConstants.html',
                           chems=utils.CHEMS,
                           reactor=reactorno,
                           form=form,
                           defaults=constants)
