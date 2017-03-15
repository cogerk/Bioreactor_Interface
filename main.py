"""
Runs this flask app.  To start this application from terminal use:
$ python run.py

Stolen By: Kathryn Cogert
Stolen From: Tim Dobbs (https://github.com/tsdobbs/encyclopedia_brunch)
Stolen On: Feb 28 2017
"""
import os
from __init__ import app
extra_dirs = [os.getcwd() + x for x in ['/templates/', '/static/']]
extra_files = []
for extra_dir in extra_dirs:
    for dirname, dirs, files in os.walk(extra_dir):
        for filename in files:
            filename = os.path.join(dirname, filename)
            if os.path.isfile(filename):
                extra_files.append(filename)
if __name__ == '__main__':
    app.run(debug=True, extra_files=extra_files)