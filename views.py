import json
from flask import render_template, request, redirect, flash, url_for #Flask
from flask_admin import Admin #Flask-Admin
from bokeh.embed import autoload_server
import reactorhandler as rct
import calconstanthandler as calconst
import constanthandler as const
import controlcmdhandler as cmd
import utils
from __init__ import app, db, models
from forms import build_calconstant_form, build_control_forms, build_constant_form, create_reactor_form #Flask-WTF

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
    SelectForm = create_reactor_form(rct_list)
    form = SelectForm()
    if form.validate_on_submit():
        flash('Redirecting to ' + form.reactor_no.data + ' control panel')
        return redirect(url_for('control_reactor', reactorno=form.reactor_no.data))
    return render_template('index.html', form=form, details=reactors)


@app.route('/reactor/<int:reactorno>/current', strict_slashes=False)
def send_current(reactorno):
    ip, port = utils.get_controller_info(reactorno, True)
    reactorno = reactorno
    print('Updating')
    current, loop_list = cmd.get_current(ip, port, reactorno)
    return json.dumps(current)


@app.route('/reactor/<int:reactorno>', methods=['GET', 'POST'], strict_slashes=False)
def control_reactor(reactorno):
    ip, port = utils.get_controller_info(1, True)
    status = None
    loop_form_dict, current, loop_list = build_control_forms(ip,
                                                             port,
                                                             reactorno)
    script_dict = {}
    script_dict['Probes'] = autoload_server(model=None,
                                            app_path='/R' +
                                                     str(reactorno) +
                                                     '_probes')
    for loop in loop_list:
        appname = '/R' + str(reactorno) + '_'+loop
        #TODO: Control Loop Graphs
        script_dict[loop] = None #autoload_server(model=None, app_path=appname)
    json_current = json.dumps(current)
    script = ''
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
    formclass, slopes, ints, sigs = build_calconstant_form(
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


@app.route('/test', strict_slashes=False)
def test():
    return render_template('test.html')

@app.route('/reactor/<int:reactorno>/Constants', methods=['GET', 'POST'], strict_slashes=False)
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
