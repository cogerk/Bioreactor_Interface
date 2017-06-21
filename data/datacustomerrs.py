"""
Define Custom Errors
"""

# TODO: Which of these are required?

class InvalidDir(BaseException):
    """Error for specifying a directory ID that doesn't exist"""


class NotMatching(BaseException):
    """Error for specifying a file name that doesn't exist"""


class NoFolders(BaseException):
    """Error for specifying a directory to find folders in that has no folders
    in it"""


class NoSuchReactor(Warning):
    """Error for specifying a reactor number to find the directory for"""


class BadFileNames(BaseException):
    """No correctly formatted files here"""


class CrioConnect(BaseException):
    """Problem connecting to cRIO"""


class CrioFormat(BaseException):
    """Problem formatting data from cRIO to saveable form"""