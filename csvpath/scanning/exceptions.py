# pylint: disable=C0114,R0801


class ScanException(Exception):
    """most general exception when scanning"""


class UnexpectedProductionException(Exception):
    """when the result of parsing is an unexpected data structure"""
