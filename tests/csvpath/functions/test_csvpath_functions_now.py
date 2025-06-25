import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
NUMBERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers.csv"


class TestCsvPathFunctionsNow(unittest.TestCase):
    def test_function_now(self):
        path = CsvPath()
        # TODO: obviously this will break and need updating 1x a year. :(
        path.parse(f'${PATH}[*][now("%Y") == "2025"]')
        lines = path.collect()
        assert len(lines) == 9

    def test_function_now2(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                   firstline.nocontrib() -> @n = now()
                   lt( @n , now() )
        ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_function_now3(self):
        path = CsvPath()
        path.parse(
            f"""
                ${PATH}[*][
                        now("%d") == today()
                        now("%m") == thismonth()
                        now("%Y") == thisyear()
                ] """
        )
        lines = path.collect()
        assert len(lines) == 9
