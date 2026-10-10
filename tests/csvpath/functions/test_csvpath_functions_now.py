import unittest
import os
import pytest
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
NUMBERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers.csv"


class TestCsvPathFunctionsNow(unittest.TestCase):
    def test_function_now1(self):
        path = CsvPath()
        # TODO: obviously this will break and need updating 1x a year. :(
        path.parse(f'${PATH}[*][now("%Y") == "2026"]')
        lines = path.collect()
        assert len(lines) == 9

    #
    # @n and now() are datetimes, and datetime comparisons currently ignore
    # the time of day (issue #312), so they compare as equal. this passed
    # only while lt() behaved as lte() (issue #301). once #312 is fixed,
    # now() is later than @n and lt() is true again, so this will pass and
    # the strict marker must be removed. note: two consecutive now() calls
    # could in principle return the same microsecond; if this test flakes
    # after #312, that is why.
    #
    @pytest.mark.xfail(
        strict=True, reason="#312: datetime comparisons ignore time of day"
    )
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
