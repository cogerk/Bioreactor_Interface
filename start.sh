# start.sh

python bokehservermanager.py &
python main.py && fg

# Util commands:
#   $ jobs:
#       - returns the process ID (PID) pushed to background
#   $ kill %<job_number>:
#       - kill the process with job_number