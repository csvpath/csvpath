import os
import unittest
from csvpath import CsvPath
import pytest

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}usage.csv"


class TestCsvPathEncoding(unittest.TestCase):
    def test_csvpath_encoding(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise")
        path.parse(f"${PATH}[*][yes()]")
        #
        # if PATH runs despite non-utf-8 encoding we're good
        #
        path.collect()
