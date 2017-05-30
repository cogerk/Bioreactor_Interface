"""
Written By: Kathryn Cogert
For: Winkler Lab/CSE599 Winter Quarter 2016
Purpose: Write and read from a google doc.


Note: Due to this issue:https://github.com/ctberthiaume/gdcp/issues/11, I had
to run python2.7 in a virtual environment for this to work.  UGH!


"""
#TODO: ALARM LOG
#TODO: Visualization Tools
import os
import urllib.request, urllib.error, urllib.parse
import datetime
from xml.etree import ElementTree
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import pandas as pd
import numpy as np
import time
import utils
import customerrs as cust


"""
Define Custom Errors
"""


class BaseError(Exception):
    """Base error for google drive manipulation and navigation errors."""


class InvalidDir(BaseError):
    """Error for specifying a directory ID that doesn't exist"""


class NotMatching(BaseError):
    """Error for specifying a file name that doesn't exist"""


class NoFolders(BaseError):
    """Error for specifying a directory to find folders in that has no folders
    in it"""


class NoSuchReactor(BaseError):
    """Error for specifying a reactor number to find the directory for"""


class BadFileNames(BaseError):
    """No correctly formatted files here"""


class CrioConnect(BaseError):
    """Problem connecting to cRIO"""


class CrioFormat(BaseError):
    """Problem formatting data from cRIO to saveable form"""


"""
Define Constants
"""
# TODO: Get these from database
IP = '128.208.236.226'
PORT = 8080
DEBUG_PORT = 8001
WLAB = 'Winkler Lab'
RDATA = 'ReactorData'
OLD = datetime.datetime(year=1900, month=1, day=1, hour=0,
                                    minute=0, second=0, microsecond=0)

"""
Authenticate the connection to google drive
Requires correct client_secrets, credentials, and settings files.
"""
gauth = GoogleAuth(os.getcwd()+"/settings.yaml")
gauth.LoadCredentialsFile("mycreds.txt")
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


def get_newdata(reactorno, debug=False):
    """
    Uses HTTP method to query cRIO server for reactor status
    :param reactorno: int, this is the reactor in question
    :return: dataframe, this is a dataframe of requested values
    """
    # TODO: Use call_reactor from rutils instead for all this code from here...
    # Builds the cRIO web server URL where we will make the GET request
    url = 'http://%s:%d/R%d/R%dSBRControl_Status'\
          %(IP, PORT, reactorno, reactorno)
    debug_url = 'http://%s:%d/R%d/R%dSBRControl_Status' \
                %(IP, DEBUG_PORT, reactorno, reactorno)
    # Makes the GET request
    if debug:
        result = urllib.request.urlopen(debug_url).read()
    else:
        result = urllib.request.urlopen(url).read()

    #TODO: Send me an email if you can't connect to the cRIO
    # Result is a labview "cluster" type variable, (like a struct in java)
    # But it is saved here as an XML string and converted to a parseable form
    root = ElementTree.fromstring(result)
    # TODO: Generalize for all loops
    status = {}
    loop = 'SBR'
    for terminal in root:
        if terminal.find('Name').text == loop + 'Data':
            names = terminal.find('Value').findall('Name')
            vals = terminal.find('Value').findall('Value')
            break
    data = list(zip(names, vals))
    for each in data:
        if each[1].text:
            value = utils.convert_to_datatype(each)
            status[each[0].text.strip()] = value
        else:
            status[each[0].text.strip()] = {}
            names2 = each[1].findall('Name')
            vals2 = each[1].findall('Value')
            data2 = list(zip(names2, vals2))
            for each2 in data2:
                # Special rules for SBR control parameters
                if each2[0].text == 'Phase Timing Pair':
                    phase_pair = [x.text for x in each2[1].findall('Value') if x.text is not None]
                    # TODO: Reactor SBR Phase Control Page
                    try:
                        phase_pair[1] = float(phase_pair[1])
                    except ValueError:
                        raise cust.IncorrectClusterOrder(
                            'User needs to make sure that '
                            'phase name is first (0) in cluster')
                    phase_pair = tuple(phase_pair)
                    if status[each[0].text.strip()] == {}:
                        status[each[0].text.strip()] = [phase_pair]
                    else:
                        temp = status[each[0].text.strip()]
                        temp.append(phase_pair)
                        status[each[0].text.strip()] = temp
                else:
                    value = utils.convert_to_datatype(each2)
                    if status[each[0].text.strip()] == {}:
                        status[each[0].text.strip()] = \
                            [(each2[0].text, value)]
                    else:
                        temp = status[each[0].text.strip()]
                        temp.append((each2[0].text.strip(), value))
                        status[each[0].text.strip()] = temp
    #TODO: ...to here
    new_df = {}
    for key in status:
        if type(status[key]) is list:
            for each in status[key]:
                new_df[(key, each[0])] = [each[1]]
        else:
            new_df[(key)] = [status[key]]
    print(new_df)
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
        raise InvalidDir('Specified directory ' + directory + ' is invalid')


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
    for afile in file_list:
        # if file is a folder...
        if afile['mimeType'] == 'application/vnd.google-apps.folder':
            no_folders_here = False  # We won't need to raise the error
            if afile['title'] == folder_name:
                # Look for folder that matches name, and save the folder ID
                fid = afile['id']
                return fid
    # If nothing matched, the name was wrong
    if 'fid' in locals() or 'fid' in globals():
        raise NotMatching('No folder of that name in specified dir')
    # if none of files in the list were folders, then say so.
    if no_folders_here:
        raise NoFolders('There are no folders in specified directory')


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
        raise NotMatching('No file of that name in specified dir')
    # if none of files in the list were folders, then say so.
    if no_files_here:
        raise NoFolders('There are no files in specified directory')


def find_reactorfolder(reactorno):
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
    # Navigate through the directories
    wlab_fid = find_folderid(WLAB, 'root')
    rdata_fid = find_folderid(RDATA, wlab_fid)
    r_fid = find_folderid(r_folder_name, rdata_fid)
    # If we can't find a folder, say so.
    if r_fid is None:
        raise NoSuchReactor('There is no folder for reactor #' + reactorno)
    elif wlab_fid is None:
        raise InvalidDir('Cannot find ' + WLAB + ' Directory')
    elif rdata_fid is None:
        raise InvalidDir('Cannot find ' + RDATA + ' Directory')
    # Return the reactor number's folder ID
    return r_fid


def list_rfiles_by_date(reactorno, date=True):
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
    tgt_folder_id = find_reactorfolder(reactorno)
    all_file_list = get_file_list(tgt_folder_id)
    # If there are files, only look at files named w/ correct format.
    if all_file_list:
        file_list = []
        filename_format = 'R' + str(reactorno) + 'data %Y-%m-%d'
        for afile in all_file_list:
            # If it's not a folder, try to parse filename and get time stamp
            if afile['mimeType'] != 'application/vnd.google-apps.folder':
                file_title = afile['title']
                try:
                    file_ts = datetime.datetime.strptime(file_title,
                                                         filename_format)
                except Exception as e:
                    # If can't parse file, let user know the organization sucks
                    print('Warning: ' + str(e))
                    continue  # skip this iteration
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


def find_make_reactorfile(reactorno, collect_int, file_length, debug=False):
    """
    Find latest or make new file in specified reactor's directory for writing
    :param reactorno: int, the number of reactor in question
    :param collect_int: float, this is the number of secs between data pts.
    :param make: boolean, if true (default) than make a new file if needed
    :param file_length: float, this is the number of days in a file.
    :return: our_file, this is the file
    """
    # Get latest file
    file_deets = list_rfiles_by_date(reactorno)
    if file_deets is None:  # If there were no files in folder, make one!
        days_since_creation = file_length+1
    else:  # Else, find days since latest files creation
        days_since_creation = file_deets[1]
    if days_since_creation < file_length:
        # If file is newer than our specified file length, return it.
        our_file = file_deets[0]
    else:  # Otherwise, make a new one!
        # Get the current date
        what_time_is_it = datetime.datetime.now()
        # File name format is "R#Data YYYY-MM-DD"
        filename_format = 'R' + str(reactorno) + 'data %Y-%m-%d'
        filename = what_time_is_it.strftime(filename_format)
        # Create a new file with that name
        tgt_folder_id = find_reactorfolder(reactorno)
        our_file = drive.CreateFile({'title': filename,
                                          'mimeType': 'text/csv',
                                          "parents":
                                              [{"kind": "drive#fileLink",
                                                "id": tgt_folder_id}]})
        to_write = get_newdata(reactorno, debug)  # Get first data pt
        to_write.to_csv('temp.csv')  # Convert to CSV
        our_file.SetContentFile('temp.csv')  # Write this to google drive
        remove_file('temp.csv')  # Remove temp file w/ first data pt
        our_file.Upload()  # Upload it
        # Tell user what happened
        print('Successfully created new file ' + filename)
        time.sleep(collect_int)  # Wait before collecting another pt
    return our_file


def get_rfile(r_file):
    r_file.GetContentFile('temp.csv')

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

    # if dataframe, then return dataframe
    df = pd.read_csv('temp.csv',
                     index_col='Date',
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

def write_to_reactordrive(reactorno, collect_int, file_length, debug=False):
    """
    Writes some latest dataframe to a specified file for a specified reactor
    :param reactorno: int, this is the reactor in question
    :param collect_int: float, this is the number of secs between data pts.
    :param file_length: float, this is the number of days in a data file
    """
    # Get latest data point from the reactor.
    to_write = get_newdata(reactorno, debug)
    # Find our file we asked for


    try:
        file_to_write = find_make_reactorfile(reactorno, collect_int,
                                              file_length)
    except Exception as e:
        ts_str = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
        print('Due to error with g drive file retrieval, ' + \
              'skipped collection at ' + \
              str(ts_str) + '\n')
        print(str(e))
        return
        # Take all data in drive and convert to dataframe
    #TODO: Error if this block of code does not work
    file_to_write.GetContentFile('temp.csv')
    old_data = pd.read_csv('temp.csv')
    old_data = old_data.set_index('Date')
    # Append latest data point in local csv file
    new_data = old_data.append(to_write)
    new_data.to_csv('temp.csv')
    # Write to google drive file
    file_to_write.SetContentFile('temp.csv')
    # Delete that local file
    remove_file('temp.csv')
    # If latest data point had a new column, add to all past files
    if set(old_data.columns) - set(to_write.columns):
        add_new_columns(reactorno)
        try:
            file_to_write.Upload()  # Upload it
            print('Reactor #' + str(reactorno) + \
                  ' Data point saved successfully')
        except Exception as e:
            ts_str = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
            print('Due to error with g drive file upload,' + \
                'skipped collection at ' + str(ts_str) + ':')
            print(str(e))

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
def add_new_columns(reactorno):
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
                tgt_folder_id = find_reactorfolder(reactorno)
                print('Adding new column(s) to ' + each[2])
            df.to_csv('temp.csv')
            each[0].SetContentFile('temp.csv')
            remove_file('temp.csv')  # Remove temp file w/ first data pt
            each[0].Upload()  # Upload it

    return
