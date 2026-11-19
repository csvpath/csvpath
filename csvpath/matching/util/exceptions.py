class MatchException(Exception):
    """most general exception when matching"""


class MatchComponentException(MatchException):
    """most general exception for the matching part of a csvpath"""


class ChildrenException(MatchComponentException):
    """raised when the structure of a match part is incorrect"""


class ChildrenValidationException(MatchComponentException):
    """raised exclusively when the runtime actuals required
    by build-in validation are not met. this exception is
    only for the Args class's use -- and more specifically
    for the runtime arg matching, not so much the pre-run
    match componant validation."""


class DataException(MatchException):
    """raised when a datium is unexpected or incorrect"""

    def __str__(self):
        #
        # the message is what the user reads in the error. it used to be
        # the class, so every DataException printed as
        # <class '...DataException'> instead of what was wrong.
        #
        msg = super().__str__()
        return msg if msg else self.__class__.__name__


class PrintParserException(Exception):
    pass
