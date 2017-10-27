# start.sh

python bokehservermanager.py &
python run.py && fg

# Util commands:
#   $ jobs:
#       - returns the process ID (PID) pushed to background
#   $ kill %<job_number>:
#       - kill the process with job_number