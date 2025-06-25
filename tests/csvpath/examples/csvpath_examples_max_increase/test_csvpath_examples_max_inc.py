import unittest
import pytest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}examples{os.sep}csvpath_examples_max_increase{os.sep}Automobiles_Annual_Imports_and_Exports_Port_Authority_of_NY.csv"


class TestFunctionsMaxInc(unittest.TestCase):
    def test_max_inc_1(self):
        path = CsvPath()
        #
        # problem perceived in this example was actually just forgetting that
        # everything is a string until it is converted. adding int() is correct
        # and in no way a problem. it's how it's suppose to work, but easy to
        # forget.
        #
        path.parse(
            f"""${PATH}[1*]
            [
                @m1 = max(#"Automobile Volume")
                @m2.increase = int(#"Automobile Volume")
            ]"""
        ).fast_forward()
        assert path.variables["m1"] == 690636
        assert path.variables["m2"] == 690636
