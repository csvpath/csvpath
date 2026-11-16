import unittest
import os
import datetime
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
NUMBERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers.csv"


class TestCsvPathFunctionsNow(unittest.TestCase):
    def test_function_now1(self):
        path = CsvPath()
        #
        # compare with this year, not a hard-coded one, so the test does not
        # break every January. it can still fail if run across midnight on
        # December 31st.
        #
        year = datetime.datetime.now().strftime("%Y")
        path.parse(f'${PATH}[*][now("%Y") == "{year}"]')
        lines = path.collect()
        assert len(lines) == 9

    #
    # @n is set on the first line, so every later now() is strictly later.
    # note: two consecutive now() calls could in principle return the same
    # microsecond; if this test ever flakes, that is why.
    #
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
