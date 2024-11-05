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

    pass

    def __str__(self):
        return f"""{self.__class__}"""


class PrintParserException(Exception):
    pass
