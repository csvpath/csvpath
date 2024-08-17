class MatchException(Exception):
    """most general exception when matching"""

    pass


class ChildrenException(Exception):
    """raised when the structure of a match part is incorrect"""

    pass


class DataException(Exception):
    """raised when a datium is unexpected or incorrect"""

    pass

    def __str__(self):
        return f"""{self.__class__}"""
