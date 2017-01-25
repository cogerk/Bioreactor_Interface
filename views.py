from flask import Flask, render_template, request, redirect, flash, url_for
from forms import Settings, ControlStatus, pHControlManual, pHControlAuto
from wtforms import Form, FloatField, BooleanField, TextAreaField, FileField, DateTimeField, validators
from wtforms.validators import DataRequired

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def select_reactor():
    form = Settings(request.form)
    if request.method == 'POST' and form.validate():
        #TODO: Flash raises error
        #TODO: How to keep email, IP, and port to reactor control page
        flash('Redirecting to ' + form.reactor_no.data + ' control panel')
        return redirect(url_for(form.reactor_no.data))
    return render_template('index.html', form=form)


@app.route('/R1', methods=['GET', 'POST'])
def R1():
    #TODO: Finish building this guy out
    pH_stat_form = ControlStatus(request.form, prefix='pH_stat')
    pH_manual_form = pHControlManual(request.form)
    pH_auto_form = pHControlAuto(request.form)
    control_status = check_control_stat(pH_stat_form)
    if request.method == 'POST' and pH_stat_form.validate():
        control_status = check_control_stat(pH_stat_form)
    return render_template('R1.html',
                           pH_stat=pH_stat_form,
                           pH_manual=pH_manual_form,
                           pH_auto=pH_auto_form,
                           status=control_status)

