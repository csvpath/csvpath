import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

GOOD = f"tests{os.sep}csvpath{os.sep}examples{os.sep}csvpath_examples_jsonschema{os.sep}automobiles.json"
BAD = f"tests{os.sep}csvpath{os.sep}examples{os.sep}csvpath_examples_jsonschema{os.sep}automobiles_bad.json"


class TestCsvPathExamplesJsonSchema(unittest.TestCase):
    def test_jsonschema_1(self):
        path = CsvPath()
        path.parse(
            f"""~
                  validation-mode:fail,print,no-raise
                ~${GOOD}[0][
                    jsonschema("tests{os.sep}csvpath{os.sep}examples{os.sep}csvpath_examples_jsonschema{os.sep}automobiles.jsonschema")
                ]
            """
        ).fast_forward()
        assert path.is_valid is True

    def test_jsonschema_2(self):
        path = CsvPath()
        path.parse(
            f"""~
                  validation-mode:fail,print,no-raise
                ~${BAD}[*][
                    jsonschema(
                    "tests{os.sep}csvpath{os.sep}examples{os.sep}csvpath_examples_jsonschema{os.sep}automobiles.jsonschema")
                ]
            """
        )
        path.fast_forward()
        assert path.is_valid is False

    def test_jsonschema_3(self):
        path = CsvPath()
        path.parse(
            f"""~
                  validation-mode:fail,raise, no-print
                ~${BAD}[0][
                    jsonschema("tests{os.sep}csvpath{os.sep}examples{os.sep}csvpath_examples_jsonschema{os.sep}automobiles.jsonschema")
                ]
            """
        )
        with pytest.raises(MatchException):
            path.fast_forward()
