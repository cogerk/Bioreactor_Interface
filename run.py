import os
import config
from __init__ import app
import data.main as data
from views import reactors

extra_dirs = [os.getcwd() + x for x in ['/templates/', '/static/']]
extra_files = []
for extra_dir in extra_dirs:
    for dirname, dirs, files in os.walk(extra_dir):
        for filename in files:
            filename = os.path.join(dirname, filename)
            if os.path.isfile(filename):
                extra_files.append(filename)

if __name__ == '__main__':
    print('Beginning data collection')
    for react in reactors:
        data.start_data(react)
    print('Starting Flask Server')
    app.run(host='localhost',
            port=8002,
            debug=config.DEBUG,
            extra_files=extra_files)