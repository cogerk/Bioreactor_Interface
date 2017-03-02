"""
This is run once to initialize the database. It also adds the first reactor & controller.
Use a database editor such as http://sqlitebrowser.org to edit
You can also use the host/admin page to add/change reactor info.
Written by: Kathryn Cogert
Mar 1 2017
"""

#import os.path
#from config import SQLALCHEMY_DATABASE_URI
from __init__ import db, models

reactorno = int(input('Reactor #: '))
controllerno = int(input('cRIO #: '))
ip = input('cRIO IP: ')
port = int(input('Webservice Port (usually 8080): '))
debug_port = int(input('Webservice Debug Port (usually 8001): '))
controller_type = input('Description/Model # of Controller: ')
descrip = input('Reactor Description: ')
name = input('Name of person responsible for reactor: ')
email = input('Email for alarms: ')

db.create_all()
first_controller = models.Controller(controllerno, ip, port, debug_port, controller_type)
first_rctr = models.Reactor(reactorno, descrip, first_controller, name, email)
db.session.add(first_controller)
db.session.add(first_rctr)
db.session.commit()

