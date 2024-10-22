class MatchException(Exception):
    """most general exception when matching"""


class MatchComponentException(MatchException):
    """most general exception for the matching part of a csvpath"""


class ChildrenException(MatchComponentException):
    """raised when the structure of a match part is incorrect"""


class DataException(MatchException):
    """raised when a datium is unexpected or incorrect"""

    pass

    def __str__(self):
        return f"""{self.__class__}"""
