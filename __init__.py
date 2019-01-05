"""
imports Flask, SQLALchemy, and Flask-Admin sets them to variables,
then imports models.py and views.py, which define the content of the website

Modified By: Kathryn Cogert
H/T: Tim Dobbs (https://github.com/tsdobbs/encyclopedia_brunch)
First Modified On: Feb 28 2017
"""
# TODO: Webcam link
# TODO: CRIO Side general debug
# TODO: CRIO Side, assign celings to VFD and MFC
# TODO: Write protocol

# TODO: Offline measurement entry + Biomass activity
# TODO: Add email alarms
# TODO: Build validators

import os
import hashlib
import random
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import customerrs as cust

if 'app' not in globals():  # For launching Bokeh: If app is already running
    app = Flask(__name__)
    if not os.path.exists('secretkey.txt'):
        secretKey = hashlib.sha224(str(random.random()).encode('utf-8')).hexdigest()
        open('secretkey.txt', 'wt').write(secretKey)
    else:
        secretKey = open('secretkey.txt', 'rt').read()

    app_secret_key = secretKey[0]
    app.secret_key = app_secret_key
    app.config.from_object('config')
    db = SQLAlchemy(app)
    # TODO: Login Page
    #login_manager = LoginManager()
    #login_manager.init_app(app)

import models, views
