import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsValidate(unittest.TestCase):
    def test_function_validate1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1][ validate() ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.is_valid is True

    def test_function_validate2(self):
        path = CsvPath()
        path.parse(f""" ${PATH}[1] [ fail() validate() ]""")

        path.collect()
        assert path.is_valid is True

    def test_function_validate3(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[3] [
                fail()
                @f = valid()
                validate()
                @v = valid()
            ]"""
        )

        path.collect()
        path.variables.get("f") is False
        path.variables.get("v") is True
        assert path.is_valid is True
