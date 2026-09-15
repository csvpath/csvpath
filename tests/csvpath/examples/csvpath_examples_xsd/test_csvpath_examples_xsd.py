import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

GOOD = f"tests{os.sep}csvpath{os.sep}examples{os.sep}csvpath_examples_xsd{os.sep}automobiles.xml"
BAD = f"tests{os.sep}csvpath{os.sep}examples{os.sep}csvpath_examples_xsd{os.sep}automobiles_bad.xml"


class TestCsvPathExamplesXsd(unittest.TestCase):
    def test_xsd_1(self):
        path = CsvPath()
        path.parse(
            f"""~
                  validation-mode:fail,print,no-raise
                ~${GOOD}[0][
                    xsd("tests{os.sep}csvpath{os.sep}examples{os.sep}csvpath_examples_xsd{os.sep}automobiles.xsd")
                ]
            """
        ).fast_forward()
        assert path.is_valid is True

    def test_xsd_2(self):
        path = CsvPath()
        path.parse(
            f"""~
                  validation-mode:fail,print,no-raise
                ~${BAD}[0][
                    xsd("tests{os.sep}csvpath{os.sep}examples{os.sep}csvpath_examples_xsd{os.sep}automobiles.xsd")
                ]
            """
        ).fast_forward()
        assert path.is_valid is False

    def test_xsd_3(self):
        path = CsvPath()
        path.parse(
            f"""~
                  validation-mode:fail,print,raise
                ~${BAD}[0][
                    xsd("tests{os.sep}csvpath{os.sep}examples{os.sep}csvpath_examples_xsd{os.sep}automobiles.xsd")
                ]
            """
        )
        with pytest.raises(MatchException):
            path.fast_forward()
