import os

basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'reactors.db')
DEBUG = True

#http://alembic.zzzcomputing.com/en/latest/tutorial.html