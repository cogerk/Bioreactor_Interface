"""
Written By: Kathryn Cogert
For: Winkler Lab cRIO bioreactors
Purpose: Read reactor data to google drive every 30 secs for R2.
"""
#TODO: Implement faster quit like R1 master file updater
import threading
import config
import data.googledriveutils as gdu
#gdu = imp.load_source('googledriveutils', os.getcwd() + '/Project/googledriveutils.py')
# TODO: If timestamp is not current

def main():
    """
    Saves data in google drive.
    :return:
    """
    # Timing parameters for user to inpurt
    collect_int = eval(input('R1 data collection interval in secs: '))
    file_length = eval(input('R1 days to wait before making new file: '))

    def r1_fromreactor():
        # Takes data from cRIO and puts it in google drive
        print('Querying Reactor #1')
        gdu.write_to_reactordrive(1, collect_int, file_length, config.DEBUG)
        threading.Timer(collect_int, r1_fromreactor).start()

    r1_fromreactor()


main()
