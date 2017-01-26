from flask_wtf import Form
from flask import Flask, render_template, request, redirect, flash, url_for
from forms import Settings, pHSwitch, pHManual, pHAuto
import customerrs as cust

app = Flask(__name__)
app.secret_key = 'w1nkl3r!'

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
    #TODO: Finish building this guy out
    pH_switch_form = pHSwitch(prefix='Switch')
    pH_manual_form = pHManual(prefix='Manual')
    pH_auto_form = pHAuto(prefix='SetParams')
    if pH_switch_form.validate_on_submit() and pH_switch_form.submit.data:
        action='Switch'
    #TODO: pass to URL Builder
    if pH_manual_form.validate_on_submit and pH_manual_form.submit.data:
        action='Manual'
    if pH_auto_form.validate_on_submit and pH_auto_form.submit.data:
        action='SetParams'
    #TODO: Remove submit button and post on click
        #pH_switch_form.control_on
    return render_template('R1.html',
                           pH_switch=pH_switch_form,
                           pH_manual=pH_manual_form,
                           pH_auto=pH_auto_form)


@app.route('/R1/<status>')
def status():
    return render_template(status.html, status=status)