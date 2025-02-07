import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestFunctionsCap(unittest.TestCase):
    def test_function_cap_1(self):
        path = CsvPath()
        path.collect(
            f"""${PATH}[*][
            push("cap", caps(#say, yes())) ]"""
        )
        assert "cap" in path.variables
        assert path.variables["cap"][4] == "Sniffle Sniffle..."
        assert path.variables["cap"][8] == "Growl"
