class ParsingException(Exception):
    """for when the parsers fail for reasons beyond malformed csvpaths"""

    pass


class InputException(Exception):
    """for when an input cannot be identified as a csvpath"""

    pass


class FormatException(Exception):
    """for a malformed csvpath"""

    pass


class FileException(Exception):
    """for problems with files"""

    pass


class ProcessingException(Exception):
    """for when there is a problem with collect(), fast_forward(), or next()"""

    pass


class VariableException(Exception):
    """when there is a problem creating or accessing a variable"""

    pass
