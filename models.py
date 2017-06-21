from flask_admin.contrib.sqla import ModelView
from flask_admin import expose
import config
import reactorhandler as rct
# TODO: Test addition of dummy reactor control loops

def create_classes():
    """
    This function defines all the models for the flash function.
    By defining them in a function, a circular import is avoided in views.py
    :return:
    """
    from __init__ import db

    # Reactor Database
    class Reactor(db.Model):
        idx = db.Column(db.Integer, nullable=False, primary_key=True,
                        unique=True, autoincrement=True)
        descrip = db.Column(db.String(120), unique=True)
        controller_idx = db.Column(db.Integer,
                                   db.ForeignKey('controller.idx'))
        controller = db.relationship('Controller',
                                     backref=db.backref('reactors',
                                                        lazy='dynamic'))
        principle = db.Column(db.String(80))
        email = db.Column(db.String(120))
        collect_int_secs = db.Column(db.Float,
                                     nullable=False,
                                     default=120)
        file_length_days = db.Column(db.Float,
                                     nullable=False,
                                     default=14)
        loops = db.relationship('StringTable', backref='idx', cascade="all, delete-orphan")

        def __init__(self, idx=None, descrip=None, controller=None,
                     principle=None, email=None, collect_int_secs=120,
                     file_length_days=14, loops=[None]):
            self.idx = idx
            self.descrip = descrip
            self.controller = controller
            self.principle = principle
            self.email = email
            self.collect_int_secs = collect_int_secs
            self.file_length_days = file_length_days
            self.loops = list(map(StringTable, loops))

        def __repr__(self):
            return '%r (Description: %r)' % (self.idx, self.descrip)

    # cRIO Database
    class Controller(db.Model):
        idx = db.Column(db.Integer, primary_key=True)
        ip = db.Column(db.String(80), unique=True)
        debug_port = db.Column(db.Integer)
        port = db.Column(db.Integer)
        controller_type = db.Column(db.String(80))

        def __init__(self, idx=None, ip=None, port=None, debug_port=None,
                     controller_type=None):
            self.idx = idx
            self.ip = ip
            self.port = port
            self.debug_port = debug_port
            self.controller_type = controller_type

        def __repr__(self):
            return str(self.idx)

    # Loops database
    class StringTable(db.Model):
        string = db.Column(db.String(20), primary_key=True, nullable=True)
        r_idx = db.Column(db.Integer, db.ForeignKey('reactor.idx'))

        def __init__(self, string=None):
            self.string = string

        def __repr__(self):
            return (self.string)

    # Model views
    class ReactorModelView(ModelView):
        """
        Custom view to show reactor database on admin page
        """
        column_list = ['idx', 'descrip', 'principle', 'email',
                       'controller_idx', 'collect_int_secs',
                       'file_length_days']
        form_excluded_columns = ('loops')
        column_labels = dict(descrip='Description',
                             controller='Controller #',
                             controller_idx='Controller #',
                             email='Email For Alarms',
                             idx='Reactor #',
                             collect_int_secs='Data Collection Interval, secs',
                             file_length_days='File Length, days')

        def on_model_change(self, form, model, is_created):
            if model.idx is not None:
                get_port = model.controller.debug_port \
                    if config.DEBUG else model.controller.port
                r_loops = rct.get_loops(model.controller.ip, get_port, model.idx)
            else:
                r_loops = ['None']
            model.loops = list(map(StringTable, r_loops))

    class ControllerModelView(ModelView):
        """
        Custom view to show reactor database on admin page
        """
        column_list = ['idx', 'ip', 'port', 'debug_port', 'controller_type']
        column_labels = dict(idx='Controller #',
                             ip='IP',
                             debug_port='Debug Port',
                             controller_type='Description/Model')

    return ControllerModelView, ReactorModelView, Reactor, Controller, \
           StringTable

