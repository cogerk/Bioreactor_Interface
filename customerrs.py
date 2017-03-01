## Define Custom Errors
class InvalidAction(Exception):
    """
    Error if an action not in ACTIONS constant is passed.
    """
    pass


class InvalidLoop(Exception):
    """
    Error if a control loop that the reactor does not have is passed.
    """
    pass


class InvalidValue(Exception):
    """
    Error if control parameters passed are not in the expected format/data type
    """
    pass

class MissingKey(Exception):
    """
    No 'secretkey.txt' file in the directory
    """
    pass


