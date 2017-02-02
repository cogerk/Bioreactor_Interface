from flask import Flask, render_template, request, redirect, flash, url_for
from forms import Settings, build_calconstant_form, build_control_forms, build_constant_form
import utils
import customerrs as cust
import constanthandler as const
import calconstanthandler as calconst
import controlcmdhandler as cmd

app = Flask(__name__)
app.secret_key = 'w1nkl3r!'
# TODO: How to put secret key in a configs file

@app.route('/', methods=['GET', 'POST'])
def select_reactor():
    form = Settings()
    if form.validate_on_submit():
        #TODO: Flash raises error
        #TODO: How to keep email, IP, and port to reactor control page
        #flash('Redirecting to ' + form.reactor_no.data + ' control panel')
        return redirect(url_for(form.reactor_no.data))
    return render_template('index.html', form=form)


@app.route('/R1', methods=['GET', 'POST'])
def R1():
    # TODO: generalize for all reactors
    # TODO: Add data visualization
    ip = '128.208.236.57'
    port = 8001
    reactorno=1
    loop_form_dict = build_control_forms(reactorno)
    if request.method == 'POST':
        status = cmd.submit_to_reactor(ip, port, reactorno, request.form)
        flash(status)
    return render_template('R1.html',
                           loop_form_dict=loop_form_dict,
                           all_actions=cust.ACTIONS,
                           all_loops=cust.LOOPS)


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