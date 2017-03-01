from __init__ import db


# Reactor Database
class Reactor(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    descrip = db.Column(db.String(120), unique=True)
    controller_idx = db.Column(db.Integer, db.ForeignKey('controller.idx'))
    controller = db.relationship('Controller',
        backref=db.backref('reactors', lazy='dynamic'))
    principle = db.Column(db.String(80))
    email = db.Column(db.String(120))

    def __init__(self, idx, descrip, crio, principle, email):
        self.idx = idx
        self.descrip = descrip
        self.crio = crio
        self.principle = principle
        self.email = email

    def __repr__(self):
        return '<Reactor #: %r><Description: %r>' % (self.id, self.descrip)


# cRIO Database
class Controller(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(80))
    port = db.Column(db.Integer)

    def __init__(self, idx, ip, port):
        self.idx = idx
        self.ip = ip
        self.port = port

    def __repr__(self):
        return '<cRIO #: %r><IP: %r><Port: %r>' % (self.idx, self.IP, self.port)
