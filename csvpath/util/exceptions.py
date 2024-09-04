class ConfigurationException(Exception):
    """for when CsvPaths is incorrectly setup or some other config problem"""


class ParsingException(Exception):
    """for when the parsers fail for reasons beyond malformed csvpaths"""


class InputException(Exception):
    """for when an input cannot be identified as a csvpath"""


class FormatException(Exception):
    """for a malformed csvpath"""


class FileException(Exception):
    """for problems with files"""


class ProcessingException(Exception):
    """for when there is a problem with collect(), fast_forward(), or next()"""


class VariableException(Exception):
    """when there is a problem creating or accessing a variable"""
