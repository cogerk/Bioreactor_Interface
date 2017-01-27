from flask_wtf import Form
from wtforms import StringField, FloatField, BooleanField, \
    SelectField, IntegerField, SubmitField
from flask import Flask, render_template, request, redirect, flash, url_for
from forms import Settings, build_forms
import customerrs as cust
import utils

app = Flask(__name__)
app.secret_key = 'w1nkl3r!'

@app.route('/', methods=['GET', 'POST'])
def select_reactor():
    test=1
    form = Settings()
    if form.validate_on_submit():
        #TODO: Flash raises error
        #TODO: How to keep email, IP, and port to reactor control page
        #flash('Redirecting to ' + form.reactor_no.data + ' control panel')
        return redirect(url_for(form.reactor_no.data))
    return render_template('index.html', form=form)


@app.route('/R1', methods=['GET', 'POST'])
def R1():
    #TODO: generalize for all reactors
    ip = '128.208.236.57'
    port = 8001
    form_dict = build_forms()
    if request.method == 'POST':
        utils.get_submitted_vals(request.form)
        #get_url = utils.build_url(ip,port,1,loop,action)
        #print(get_url)
    #if pH_switch_form.validate_on_submit() and pH_switch_form.submit.data:
        reactorno = 1
        action = 'Switch'
        ip = ip
        port = port
        loop = 'pH'
        #test = utils.build_url('128.208.236.57', 8001, 1, 'pH', 'Status',
        #                 pH_switch_form.control_on.data)
    #TODO: pass to URL Builder
    return render_template('R1.html',
                           form_dict=form_dict,
                           all_actions=cust.ACTIONS)

@app.route('/R1/<status>')
def status():
    return render_template(status.html, status=status)