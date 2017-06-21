# Define Custom Errors


class InvalidAction(BaseException):
    """
    Error if an action not in ACTIONS constant is passed.
    """
    pass


class InvalidLoop(BaseException):
    """
    Error if a control loop that the reactor does not have is passed.
    """
    pass


class InvalidValue(BaseException):
    """
    Error if control parameters passed are not in the expected format/data type
    """
    pass


class MissingKey(BaseException):
    """
    No 'secretkey.txt' file in the directory
    """
    pass


class CannotReachController(BaseException):
    """
    Was unable to reach controller
    """
    pass


class UnfoundStatus(BaseException):
    """
    Could not find status of a particular loop
    """
    pass


class IncorrectClusterOrder(BaseException):
    """
    Was unable to reach controller
    """
    pass


class CannotReachControllerWarn(Warning):
    """
    Was unable to reach controller
    """
    pass


class CannotReachReactor(BaseException):
    """
    Was unable to reach reactor
    """
    pass


class CannotReachReactorWarn(Warning):
    """
    Was unable to reach reactor
    """
    pass


class DataNotCollected(Warning):
    """
    Was unable to reach controller
    """
    pass


class NonBoolean(Warning):
    """
    A non boolean value was written to a boolean actuator
    """


class NotProperlyFormatted(Warning):
    """
    This is not properly formatted on cRIO Side
    """