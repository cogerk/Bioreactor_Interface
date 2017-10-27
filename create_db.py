"""
This is run once to initialize the database. It also adds the first reactor & controller.
Use a database editor such as http://sqlitebrowser.org to edit
You can also use the host/admin page to add/change reactor info.
Written by: Kathryn Cogert
Mar 1 2017
"""

#import os.path
#from config import SQLALCHEMY_DATABASE_URI
from __init__ import db
from reactorhandler import get_loops, get_signal_list


def make_db(Reactor, Controller, debug=False):
    reactorno = 1#int(input('Reactor #: '))
    controllerno = 1 #int(input('cRIO #: '))
    ip = '172.28.236.61'#input('cRIO IP: ')
    port = 8080#int(input('Webservice Port (usually 8080): '))
    debug_port = 8001#int(input('Webservice Debug Port (usually 8001): '))
    controller_type = 'cRIO-9067'#input('Description/Model # of Controller: ')
    descrip = 'AOA/Anammox Reactor' #input('Reactor Description: ')
    name = 'Kathryn Cogert'#input('Name of person responsible for reactor: ')
    email = 'cogerk@gmail.com'#input('Email for alarms: ')
    collect_int = 120#float(input('Data collection time interval, secs: '))
    file_length = 14#float(input('Days before making new file, days: '))

    get_port = debug_port if debug else port
    loops = get_loops(ip, get_port, reactorno)
    signals = get_signal_list(ip, get_port, reactorno)
    db.create_all()
    first_controller = Controller(controllerno, ip, port, debug_port,
                                  controller_type)
    first_rctr = Reactor(reactorno, descrip, first_controller, name, email,
                         collect_int, file_length, loops, signals)
    db.session.add(first_controller)
    db.session.add(first_rctr)
    db.session.commit()

