import difflib
import urllib.request
from xml.etree import ElementTree
from flask import Flask, render_template, request, redirect, flash, url_for
from forms import Settings, build_forms
import customerrs as cust
import utils


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
    # TODO: Add constant control<-
    # TODO: generalize for all reactors
    # TODO: Add data visualization
    ip = '128.208.236.57'
    port = 8001
    form_dict = build_forms()
    if request.method == 'POST':
        [loop, action, params] = utils.get_submitted_vals(request.form)
        get_url = utils.build_url(ip, port, 1, loop, action, params)
        print(get_url)
        result = urllib.request.urlopen(get_url).read()
        root = ElementTree.fromstring(result)
        for terminal in root:
            if terminal.find('Name').text == 'ControlStatus':
                flash(terminal.find('Value').text)

    return render_template('R1.html',
                           form_dict=form_dict,
                           all_actions=cust.ACTIONS,
                           all_loops=cust.LOOPS)