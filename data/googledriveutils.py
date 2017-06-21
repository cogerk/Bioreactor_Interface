"""
Written By: Kathryn Cogert
For: Winkler Lab/CSE599 Winter Quarter 2016
Purpose: Write and read from a google doc.


Note: Due to this issue:https://github.com/ctberthiaume/gdcp/issues/11, I had
to run python2.7 in a virtual environment for this to work.  UGH!


"""
# TODO: cRIO side, DO and NH4 status calls
#TODO: ALARM LOG
#TODO: Visualization Tools
import datetime
import os
import time
import warnings

import numpy as np
import pandas as pd
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

import customerrs as cust
from controlcmdhandler import submit_to_reactor
import data.datacustomerrs as datacust

# TODO: rework errors so it only warns about missing status pages once
# TODO: Use admin to find location of files https://flask-admin.readthedocs.io/en/latest/advanced/#managing-files-folders
# TODO: Improved commenting and documention for this package

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


def get_newdata(no, ip, port, loop):
    """
    Uses HTTP method to query cRIO server for reactor status of given loop
    :param reactorno: int, this is the reactor in question
    :param ip: str, this is the ip of the reactor in question
    :param port: int, this is the port to access the webservice on
    :return: dataframe, this is a dataframe of requested values
    """
    # TODO: Send me an email if you can't connect to the cRIO
    # TODO: Generalize for all loops
    # TODO: Can we use this data when getting reactor status for control panel?
    # TODO: Reactor SBR Phase Control Page
    try:
        status = submit_to_reactor(ip, port, no, loop, 'Status')
    except cust.UnfoundStatus:
        currenttime = str(datetime.datetime.now())
        e_str = 'At ' + currenttime + ' data from Reactor #' + \
                str(no) + ' for loop ' + str(loop) + ' could not be collected.'
        warnings.warn(e_str, cust.DataNotCollected)
        raise cust.DataNotCollected(e_str)
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
    new_df = pd.DataFrame(new_dict)
    new_df.set_index('Timestamp', inplace=True)
    return new_df


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


def find_file(file_name, directory):
    """
    Returns a file of a given name in a given directory
    :param file_name: str, this is the name of file of interest
    :param directory: str, this is the folder ID of the directory of interest
    :return: googledriveobject, this is the file you are looking for.
    :exception NotMatching: if no folder of specified name is found, raise
    exception
    :exception NoFolders: if there are no folders in the specified directory,
    raise exception
    """
    # get list of files from our directory of interest
    file_list = get_file_list(directory)
    # We'll use this to decide whether we need to raise an error later
    no_files_here = True
    for afile in file_list:
        no_files_here = False  # We won't need to raise the error
        if afile['title'] == file_name:
            # Look for folder that matches name, and save the folder ID
            fid = afile['id']
            return afile
    # If nothing matched, the name was wrong
    if 'fid' in locals() or 'fid' in globals():
        raise datacust.NotMatching('No file of that name in specified dir')
    # if none of files in the list were folders, then say so.
    if no_files_here:
        raise datacust.NoFolders('There are no files in specified directory')


def create_folder(name, parent_id):
        folder_metadata = {
            'title': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [{"kind": "drive#fileLink",
                         "id": parent_id} ]}
        folder = drive.CreateFile(folder_metadata)
        folder.Upload()
        return folder['id']


def find_reactorfolder(reactorno, loop):
    """
    Finds the directory of a specified reactor. (reactors are numbered 1
    thru 6)
    :param reactorno: int, this is the reactor in question
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
        #TODO: Email alarm when creating new folder
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
        # TODO Error if this doesn't work
    elif isinstance(date, pd.tslib.Timestamp):
        ts_date = date
    elif date is None:
        ts_date = OLD

    # TODO Else return an error
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
                #except Exception as e:
                #    # If can't parse file, let user know the organization sucks
                #    print('Warning: ' + str(e))
                #    continue  # skip this iteration
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
    :param collect_int: float, this is the number of secs between data pts.
    :param make: boolean, if true (default) than make a new file if needed
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
                                          "parents":
                                              [{"kind": "drive#fileLink",
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
    except:
        try:
            date = pd.datetime.strptime(datestring, '%Y-%m-%d %H:%M')
        except:
            try:
                date = pd.datetime.strptime(datestring, '%m/%d/%y %H:%M')
            except:
                date = OLD
    return date

def get_rfile(r_file):
    r_file.GetContentFile('temp.csv')
    # if dataframe, then return dataframe
    df = pd.read_csv('temp.csv',
                     header=[0, 1],
                     index_col=idx,
                     parse_dates=True,
                     date_parser=dateparser)
    remove_file('temp.csv')
    return df

"""
def read_from_reactordrive(reactorno,
                           date,
                           csv=False,
                           filename='temp.csv',
                           date2=None):

    Reads the google drive files for reactor data and saves as a csv or df
    :param reactorno: int, the number of reactor in question
    :param date: date to return values for
    :param csv: boolean, downloads csv if true, df if false. default is df
    :param filename: str, if csv, name of the file to save as, default is temp
    :param date2: (optional) if seeking a range a values, 2nd date
    :return:

    # TODO, date 2 is already handled in r1datautils get_values_from.  Resolve.
    # If we asked for latest, fine the latest file only.
    if date is True:
        our_file = list_rfiles_by_date(reactorno)
        return_df = get_rfile(our_file[0])
    else:
        # If date was passed as a string, parse that.
        if isinstance(date, str):
        # TODO: Error if this is not good.
            date = pd.to_datetime(date)
        # If we gave only one date, find file that includes that date
        file_list = list_rfiles_by_date(reactorno, date)
        if date2 is None:
            return_df = get_rfile(file_list[0])
        # Otherwise, return all files between the two given dates
        else:
            # If date was passed as a string, parse that.
            if isinstance(date2, str):
                # TODO: Error if this is not good.
                date2 = pd.to_datetime(date)
            file_list2 = list_rfiles_by_date(reactorno, date2)
            idx1 = file_list.index(
                min(afile for afile in file_list if file[1] > 0))
            idx2 = file_list2.index(
                min(afile for afile in file_list2 if file[1] > 0))
            if idx1 is idx2:
                our_file = min(afile for afile in file_list if file[1]>0)
                return_df = get_rfile(our_file[0])
            else:
                if idx1 < idx2:
                    our_file = file_list[idx1:idx2+1]
                else:
                    our_file = file_list[idx2:idx1+1]
                for each in our_file:
                    df = get_rfile(each[0])
                    try:
                        return_df = return_df.append(df)
                    except NameError:
                        return_df = df
    if csv:
        return_df.to_csv(filename)
    return return_df
"""

def write_to_reactordrive(no, ip, port, loops, collect_int, file_length):
    """
    Writes some latest dataframe to a specified file for a specified reactor
    :param no: int, this is the reactor # in question
    :param ip: ip, this is the ip of the controller of the reactor in q
    :param port: port, this is the port to access the
    :param collect_int: float, this is the number of secs between data pts.
    :param file_length: float, this is the number of days in a data file
    """
    # Get latest data point from the reactor as a dataframe
    for loop in loops:
        try:
            to_write = get_newdata(no, ip, port, str(loop))
        except cust.DataNotCollected:
            continue
        file_to_write = find_make_reactorfile(no,
                                              str(loop),
                                              to_write,
                                              collect_int,
                                              file_length)
            #ts_str = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
            #print('Due to error with g drive file retrieval, ' + \
            #      'skipped collection at ' + \
            #      str(ts_str) + '\n')
            #print(str(e))
           # return
        # Take all data in drive and convert to dataframe
        #TODO: More efficient way to write to drive?
        #TODO: Error if this block of code does not work
        file_to_write.GetContentFile('temp.csv')
        old_data = pd.read_csv('temp.csv',
                               header=[0, 1],
                               index_col=[0])
        # TODO: User needs to include timestamp on all status pulls written exactly like this
        # Append latest data point in local csv file
        new_data = old_data.append(to_write)
        new_data.to_csv('temp.csv')
        # Write to google drive file
        file_to_write.SetContentFile('temp.csv')
        # Upload
        file_to_write.Upload()
        # Delete that local file
        remove_file('temp.csv')
        # If latest data point had a new column, add to all past files
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
        # TODO: error if there was no file with that name


# Old functions that might be handy later

# To add new columns to old files, no longer in use
# TODO: If there are new columns, add them to old files w/ this function
def add_new_columns(reactorno, loop):
    # Return latest file & a list of all files
    latest_file = list_rfiles_by_date(reactorno)
    file_list = list_rfiles_by_date(reactorno, False)
    # Convert latest file to dataframe and get column names
    df = get_rfile(latest_file[0])
    allcols = df.columns
    # Go through the file_list in reverse order (to keep them chronological)
    for each in reversed(file_list):
        # Find missing columns and add them
        df = get_rfile(each[0])
        cols = df.columns
        missing_cols = set(allcols) - set(cols)
        if missing_cols:
            for each2 in missing_cols:
                print(df)
                df[each2] = np.nan
                tgt_folder_id = find_reactorfolder(reactorno, loop)
                print('Adding new column(s) to ' + each[2])
            df.to_csv('temp.csv')
            each[0].SetContentFile('temp.csv')
            remove_file('temp.csv')  # Remove temp file w/ first data pt
            each[0].Upload()  # Upload it

    return
