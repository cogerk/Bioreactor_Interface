"""
imports Flask, SQLALchemy, and Flask-Admin sets them to variables,
then imports models.py and views.py, which define the content of the website

Modified By: Kathryn Cogert
Stolen From: Tim Dobbs (https://github.com/tsdobbs/encyclopedia_brunch)
Stolen On: Feb 28 2017
"""
# TODO: If cRIO 404, special error
# TODO: CRIO Side general debug
# TODO: CRIO Side, assign celings to VFD and MFC
# TODO: ISE Manager
# TODO: Calibration protocol
# TODO: Offline measurement entry + Biomass activity



from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import customerrs as cust

app = Flask(__name__)
try:
    with open ('secretkey.txt', ) as myfile:
        app_secret_key = myfile.readlines()
except cust.MissingKey:
    pass

app_secret_key = app_secret_key[0]
app.secret_key = app_secret_key
app.config.from_object('config')
db = SQLAlchemy(app)
# TODO: Login Page
#login_manager = LoginManager()
#login_manager.init_app(app)

import models, views
