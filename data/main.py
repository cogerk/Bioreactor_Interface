"""
Written By: Kathryn Cogert
For: Winkler Lab cRIO bioreactors
Purpose: Read reactor data to google drive every 30 secs for R2.
"""

# TODO: Implement faster quit like R1 master file updater
import threading
import config
import data.googledriveutils as gdu
# TODO: If timestamp is not current
# TODO: Does this work for multiple reactors?


def start_data(reactor):
    """
    Saves data in google drive.
    :param reactor: database entry of a given reactor
    :return:
    """
    # Timing parameters for user to inpurt
    collect_int = reactor.collect_int_secs
    file_length = reactor.file_length_days
    no = reactor.idx
    ip = reactor.controller.ip
    if config.DEBUG:
        port = reactor.controller.debug_port
    else:
        port = reactor.controller.port

    def data_collect():
        # Takes data from cRIO and puts it in google drive
        print('Querying Reactor #' + str(reactor.idx))
        loops = reactor.loops
        gdu.write_to_reactordrive(no,
                                  ip,
                                  port,
                                  loops,
                                  collect_int,
                                  file_length)
        threading.Timer(collect_int, data_collect).start()

    data_collect()
