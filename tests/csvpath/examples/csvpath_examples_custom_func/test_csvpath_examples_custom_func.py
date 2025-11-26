import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.scanning.scanner2 import Scanner2 as Scanner
from csvpath.util.config import OnError

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvpathExamplesCustomFunc(unittest.TestCase):
    def test_csvpath_examples_custom_func_extract(self):
        path = CsvPath()
        path.config.add_to_config(
            "functions",
            "imports",
            os.path.join("assets", "config", "extra-functions.imports"),
        )
        path.parse(f'${PATH}[3][ @e = extract(#2, "bb") ]')
        path.fast_forward()
        assert "e" in path.variables
        assert path.variables["e"] is True
