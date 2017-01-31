from flask import Flask, render_template, request, redirect, flash, url_for
from forms import Settings, CalConstantForm, build_forms
import customerrs as cust
import utils


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
    # TODO: Add constant control<-
    # TODO: generalize for all reactors
    # TODO: Add data visualization
    ip = '128.208.236.57'
    port = 8001
    loop_form_dict = build_forms()
    if request.method == 'POST':
        status = utils.submit_command_to_reactor(ip, port, 1, request.form)
        flash(status)
    return render_template('R1.html',
                           loop_form_dict=loop_form_dict,
                           all_actions=cust.ACTIONS,
                           all_loops=cust.LOOPS)


@app.route('/R1/CalConstants', methods=['GET', 'POST'])
def calconstants():
    ip = '128.208.236.57'
    port = 8001
    form = CalConstantForm
    if request.method == 'POST':
        print(request.form)
    return render_template('CalConstants.html',
                           forms=form)
