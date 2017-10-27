
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import customerrs as cust

if 'app' not in globals():  # For launching Bokeh: If app is already running
    app = Flask(__name__)

    try:
        with open('secretkey.txt') as myfile:
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
import data.main as data
import data.googledriveutils as gdu

react = views.reactors[0]
gdu.write_to_reactordrive(no=react.idx,
                    ip=react.controller.ip,
                    port=react.controller.port,
                    loops=react.loops,
                    collect_int=react.collect_int_secs/60,
                    file_length=react.file_length_days,
                    buffer_size=10)
#print('Beginning data collection')
#for react in views.reactors:
#    data.start_data(react)
