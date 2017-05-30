from __init__ import db
from flask_admin.contrib.sqla import ModelView #Flask-SQLAlchemy


# Reactor Database
class Reactor(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    descrip = db.Column(db.String(120), unique=True)
    controller_idx = db.Column(db.Integer, db.ForeignKey('controller.idx'))
    controller = db.relationship('Controller',
        backref=db.backref('reactors', lazy='dynamic'))
    principle = db.Column(db.String(80))
    email = db.Column(db.String(120))

    def __init__(self, idx=None, descrip=None, controller=None, principle=None, email=None):
        self.idx = idx
        self.descrip = descrip
        self.controller = controller
        self.principle = principle
        self.email = email

    def __repr__(self):
        return '%r (Description: %r)' % (self.idx, self.descrip)


# cRIO Database
class Controller(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(80), unique=True)
    debug_port = db.Column(db.Integer)
    port = db.Column(db.Integer)
    controller_type = db.Column(db.String(80))

    def __init__(self, idx=None, ip=None, port=None, debug_port=None, controller_type=None):
        self.idx = idx
        self.ip = ip
        self.port = port
        self.debug_port = debug_port
        self.controller_type = controller_type

    def __repr__(self):
        return str(self.idx)


class ReactorModelView(ModelView):
    """
    Custom view to show reactor database on admin page
    """
    column_list = ['idx', 'descrip', 'principle', 'email', 'controller_idx']
    column_labels = dict(descrip='Description',
                         controller='Controller #',
                         controller_idx='Controller #',
                         email='Email For Alarms',
                         idx='Reactor #')


class ControllerModelView(ModelView):
    """
    Custom view to show reactor database on admin page
    """
    column_list = ['idx', 'ip', 'port', 'debug_port', 'controller_type']
    column_labels = dict(idx='Controller #',
                         ip='IP',
                         debug_port='Debug Port',
                         controller_type='Description/Model')