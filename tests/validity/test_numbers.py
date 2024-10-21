import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import ChildrenException
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsValidNumbers(unittest.TestCase):
    def test_validity_int1(self):
        path = CsvPath()
        Save._save(path, "test_validity_int1")
        path.parse(
            f"""${PATH}[*][
                int.notnone(none())
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.fast_forward()

    def test_validity_int2(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_validity_int2")
        path.parse(
            f""" ~id:test_validity_none2~
                ${"tests/test_resources/test.csv"}[*][
                    any( length( concat("a", int(random(0)))))
                ]"""
        )
        with pytest.raises(ChildrenException):
            path.fast_forward()

    def test_validity_int3(self):
        path = CsvPath()
        Save._save(path, "test_validity_int3")
        path.parse(
            f"""~id:validity_int3~ ${PATH}[*][
                int.notnone("a")
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.fast_forward()
