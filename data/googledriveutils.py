"""
Written By: Kathryn Cogert
For: Winkler Lab/CSE599 Winter Quarter 2016
Purpose: Write and read from a google doc.


Note: Due to this issue:https://github.com/ctberthiaume/gdcp/issues/11, I had
to run python2.7 in a virtual environment for this to work.  UGH!


"""
# TODO: cRIO side, NH4 status calls
# TODO: ALARM LOG

import datetime
import os
import time
import warnings
import pandas as pd
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import customerrs as cust
from controlcmdhandler import submit_to_reactor
import data.datacustomerrs as datacust

"""
Define Constants
"""
# TODO: put this & google authetication in admin
WLAB = 'Winkler Lab'
RDATA = 'ReactorData'
OLD = datetime.datetime(year=1900, month=1, day=1, hour=0, minute=0, second=0,
                        microsecond=0)

"""
Authenticate the connection to google drive
Requires correct client_secrets, credentials, and settings files.
"""
os.chdir('data')
gauth = GoogleAuth(os.getcwd()+"/settings.yaml")
gauth.LoadCredentialsFile(os.getcwd()+"/mycreds.txt")
if gauth.credentials is None:
    # Authenticate if they're not there
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    # Refresh them if expired
    gauth.Refresh()
else:
    # Initialize the saved creds
    gauth.Authorize()
# Save the current credentials to a file
gauth.SaveCredentialsFile("mycreds.txt")
drive = GoogleDrive(gauth)
os.chdir('..')


def remove_file(filename):
    """
    Determines if a file exists before trying to delete it
    :param filename: str, name of file to delete
    :return: boolean if the filename doesn't exist
    """
    if os.path.exists(filename):
        os.remove(filename)
    else:
        return False
    return


def get_newdata(no, ip, port, loops):
    """
    Uses HTTP method to query cRIO server for reactor status of given loop
    :param no: int, this is the reactor in question
    :param ip: str, this is the ip of the reactor in question
    :param port: int, this is the port to access the webservice on
    :param loops: LoopTable, list of all control loops for reactor.
    :return: dataframe, this is a dataframe of requested values
    """
    # TODO: Send me an email if you can't connect to the cRIO
    # TODO: Generalize for all loops
    # TODO: Can we use this data when getting reactor status for control panel?
    # TODO: Reactor SBR Phase Control Page
    new_dfs = {}
    for loop in loops:
        try:
            status = submit_to_reactor(ip, port, no, str(loop), 'Status')
        except cust.UnfoundStatus:
            currenttime = str(datetime.datetime.now())
            e_str = 'At ' + currenttime + ' data from Reactor #' + \
                    str(no) + ' for loop ' + str(loop) + \
                    ' could not be collected.'
            warnings.warn(e_str, cust.DataNotCollected)
            continue
        new_dict = {}
        for key in status:
            if type(status[key]) is list:
                for each in status[key]:
                    if each[0] == 'Timestamp':
                        new_dict[(each[0], each[0])] = [each[1]]
                    else:
                        new_dict[(key, each[0])] = [each[1]]
            else:
                new_dict[(key, key)] = [status[key]]
        new_dfs[loop.string] = pd.DataFrame(new_dict)
        new_dfs[loop.string].set_index('Timestamp', inplace=True)
    return new_dfs


def get_file_list(directory):
    """
    Returns a file list given the file ID of a directory folder.
    :param directory: str, this is the file ID of the directory of interest
    :return: file_list, list, this is a list of all the files in the directory
    :exceptions: if the specified ID is invalid, raises an exception.
    """
    # List all files
    try:
        file_list = drive.ListFile({'q': "'%s' in parents and trashed=false" %
                                         directory}).GetList()
        return file_list
    except:
        # If directory id is bad, say so.
        raise datacust.InvalidDir('Specified directory ' +
                                  directory + ' is invalid')


def find_folderid(folder_name, directory):
    """
    Returns the id of a folder of a given name in a given directory
    :param folder_name: str, this is the name of folder of interest
    :param directory: str, this is the folder ID of the directory of interest
    :return: str, this is the folder ID from folder_name
    :exception NotMatching: if no folder of specified name is found, raise
    exception
    :exception NoFolders: if there are no folders in the specified directory,
    raise exception
    """
    # get list of files from our directory of interest
    file_list = get_file_list(directory)
    # We'll use this to decide whether we need to raise an error later
    no_folders_here = True
    fid = None
    for afile in file_list:
        # if file is a folder...
        if afile['mimeType'] == 'application/vnd.google-apps.folder':
            no_folders_here = False  # We won't need to raise the error
            if afile['title'] == folder_name:
                # Look for folder that matches name, and save the folder ID
                fid = afile['id']
    # if none of files in the list were folders, then say so.
    if no_folders_here:
        raise datacust.NoFolders('There are no folders in specified directory')
    # If nothing matched, the name was wrong
    if fid is not None:
        return fid
    else:
        raise datacust.NotMatching('No folder of that name in specified dir')


def create_folder(name, parent_id):
        folder_metadata = {
            'title': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [{"kind": "drive#fileLink",
                         "id": parent_id}]}
        folder = drive.CreateFile(folder_metadata)
        folder.Upload()
        return folder['id']


def find_reactorfolder(reactorno, loop):
    """
    Finds the directory of a specified reactor. (reactors are numbered 1
    thru 6)
    :param reactorno: int, this is the reactor in question
    :param loop: str, this is the control loop in question
    :return: str, this is the file ID of the specified reactor's directory
    :exception No Such Reactor: if no directory of the specified reactor
    exists, raise an error.
    """
    # folder will be 'R1', 'R2', etc. So make that string.
    r_folder_name = 'R' + str(reactorno)
    loop_folder_name = r_folder_name + '_' + loop
    # Navigate through the directories
    wlab_fid = find_folderid(WLAB, 'root')
    rdata_fid = find_folderid(RDATA, wlab_fid)
    try:
        r_fid = find_folderid(r_folder_name, rdata_fid)
    except (datacust.NoFolders, datacust.NotMatching):
        # Create Folder
        warnstr = 'There is no folder for reactor #' + str(reactorno) + \
                  '\n Creating new folder: ' + r_folder_name

        warnings.warn(warnstr, datacust.NoSuchReactor)
        # Create folder
        r_fid = create_folder(r_folder_name, rdata_fid)
    # If we can't find a folder, say so.
    # Return the reactor number's folder ID
    try:
        loop_fid = find_folderid(loop_folder_name, r_fid)
    except (datacust.NoFolders, datacust.NotMatching):

        warnstr = 'There is no loop folder for reactor #' + str(reactorno) + \
                  ' loop ' + loop + \
                  '\n Creating new folder: ' + loop_folder_name

        warnings.warn(warnstr, datacust.NoSuchReactor)
        # Create folder.
        loop_fid = create_folder(loop_folder_name,  r_fid)
        # TODO: Email alarm when creating new folder
    # TODO: unittest the error throwing
    if wlab_fid is None:
        raise datacust.InvalidDir('Cannot find ' + WLAB + ' Directory')
    elif rdata_fid is None:
        raise datacust.InvalidDir('Cannot find ' + RDATA + ' Directory')
    elif r_fid is None:
        raise datacust.InvalidDir('Cannot find Directory')

    return loop_fid


def list_rfiles_by_date(reactorno, loop, date=True):
    """
    Finds the list of reactor files and creates a key to sort by date
    :param reactorno: int, the number of reactor in question
    :param loop: str, the control loop in question
    :param date: boolean, if true, give only latest file, else give all files
    :return: a file list or file and a key in format:
        [index in original file_list, days since creation,
            file title, file timestamp]
    """
    # If we asked for the latest file, get the current date
    if date is True:
        ts_date = datetime.datetime.now()
    elif isinstance(date, str):
        ts_date = pd.to_datetime(date)
    elif isinstance(date, pd.tslib.Timestamp):
        ts_date = date
    elif date is None:
        ts_date = OLD
    # Get a list of files in the reactor's folder.
    tgt_folder_id = find_reactorfolder(reactorno, loop)
    all_file_list = get_file_list(tgt_folder_id)
    # If there are files, only look at files named w/ correct format.
    if all_file_list:
        file_list = []
        filename_format = 'R' + str(reactorno) + ' ' + loop + ' data %Y-%m-%d'
        for afile in all_file_list:
            # If it's not a folder, try to parse filename and get time stamp
            if afile['mimeType'] != 'application/vnd.google-apps.folder':
                file_title = afile['title']
                file_ts = datetime.datetime.strptime(file_title,
                                                     filename_format)
                # If we can, add it to file list along with other identifiers
                ts_delta = (datetime.datetime.combine(
                    ts_date, datetime.datetime.min.time())-file_ts).days
                file_list.append((afile, ts_delta, afile['title'], file_ts))
        # If we asked for latest, return only requested file
        if date is not None:
            tgt_file = min([n for n in file_list if n[1] >= 0],
                           key=lambda n: n[1])
            return tgt_file
        else:  # Else, return list of files
            file_list = sorted(file_list, key=lambda x: x[1])
            return file_list
    else:
        return None


def find_make_reactorfile(reactorno,
                          loop,
                          to_write,
                          collect_int,
                          file_length):
    """
    Find latest or make new file in specified reactor's directory for writing
    :param reactorno: int, the number of reactor in question
    :param loop: str, the control loop in question
    :param to_write: dataframe, the data to save to the file
    :param collect_int: float, this is the number of secs between data pts.
    :param file_length: float, this is the number of days in a file.
    :return: our_file, this is the file
    """
    # Find...
    # Get list of all files
    file_deets = list_rfiles_by_date(reactorno, loop)
    if file_deets is None:  # If there were no files in folder, make one!
        days_since_creation = file_length+1
    else:  # Else, find days since latest files creation
        days_since_creation = file_deets[1]
    if days_since_creation < file_length:
        # If file is newer than our specified file length, return it.
        our_file = file_deets[0]

    # Make... (if can't find)
    else:
        # Get the current date
        what_time_is_it = datetime.datetime.now()
        # File name format is "R#Data YYYY-MM-DD"
        filename_format = 'R' + str(reactorno) + ' ' + loop + ' data %Y-%m-%d'
        filename = what_time_is_it.strftime(filename_format)
        # Create a new file with that name
        tgt_folder_id = find_reactorfolder(reactorno, loop)
        our_file = drive.CreateFile({'title': filename,
                                     'mimeType': 'text/csv',
                                     "parents": [{"kind": "drive#fileLink",
                                                  "id": tgt_folder_id}]})
        to_write.to_csv('temp.csv')  # Convert to CSV
        our_file.SetContentFile('temp.csv')  # Write this to google drive
        remove_file('temp.csv')  # Remove temp file w/ first data pt
        our_file.Upload()  # Upload it
        # Tell user what happened
        print('Successfully created new file ' + filename)
        time.sleep(collect_int)  # Wait before collecting another pt
    return our_file


# parse the dates
def dateparser(datestring):
    try:
        date = pd.datetime.strptime(datestring, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            date = pd.datetime.strptime(datestring, '%Y-%m-%d %H:%M')
        except ValueError:
            try:
                date = pd.datetime.strptime(datestring, '%m/%d/%y %H:%M')
            except ValueError:
                date = OLD
    return date


def get_rfile(r_file):
    r_file.GetContentFile('temp.csv')
    # if dataframe, then return dataframe
    df = pd.read_csv('temp.csv',
                     header=[0, 1],
                     index_col=0,
                     parse_dates=True,
                     date_parser=dateparser)
    remove_file('temp.csv')
    return df


def write_to_buffer(no, ip, port, loops, collect_int, buffer_size):
    """
    Writes some latest dataframe to a specified file for a specified reactor
    :param no: int, this is the reactor # in question
    :param ip: ip, this is the ip of the controller of the reactor in q
    :param port: port, this is the port to access the
    :param loops: LoopTable, control loops in reactor
    :param collect_int: float, this is the number of secs between data pts.
    :param buffer_size: int, the size of buffer to save before writing to drive
    """
    # Get latest data point from the reactor as a dataframe
    all_df = get_newdata(no, ip, port, loops)
    time.sleep(collect_int)
    for _ in list(range(buffer_size-1)):
        new_df = get_newdata(no, ip, port, loops)
        for loop in loops:
            if str(loop) in all_df.keys():
                all_df[str(loop)] = pd.concat([all_df[str(loop)],
                                              new_df[str(loop)]])
        time.sleep(collect_int)
    return all_df


def write_to_reactordrive(no, ip, port, loops, collect_int, file_length,
                          buffer_size):
    to_write = write_to_buffer(no, ip, port, loops, collect_int, buffer_size)
    for loop in loops:
        try:
            loop_to_write = to_write[str(loop)]
        except KeyError:
            continue
        file_to_write = find_make_reactorfile(no,
                                              str(loop),
                                              loop_to_write,
                                              collect_int,
                                              file_length)
        file_to_write.GetContentFile('temp.csv')
        old_data = pd.read_csv('temp.csv',
                               header=[0, 1],
                               index_col=[0])
        # TODO: User needs to include timestamp on all status pulls
        # Append buffer to file, upload and delete temp file.
        new_data = pd.concat([old_data, loop_to_write])
        new_data.to_csv('temp.csv')
        file_to_write.SetContentFile('temp.csv')
        file_to_write.Upload()
        print('Reactor #:'+str(no)+' '+str(loop)+' loop saved.')
        remove_file('temp.csv')
    return


def find_r1masterfile():
    # Navigate through the directories
    wlab_fid = find_folderid('Winkler Lab', 'root')
    kp_fid = find_folderid('KathrynsProjects', wlab_fid)
    amxrct_fid = find_folderid('Anammox Reactor', kp_fid)
    trials_fid = find_folderid('Reactor Trials', amxrct_fid)
    # List files in directory
    file_list = get_file_list(trials_fid)
    for afile in file_list:
        if afile['title'] == 'AMX RCT.xlsx':
            # Return the file we asked for
                return afile
