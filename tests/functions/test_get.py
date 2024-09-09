import unittest
import pytest
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsGet(unittest.TestCase):
    def test_function_get1(self):
        path = CsvPath()
        Save._save(path, "test_function_get1")
        print("")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                tally(#firstname)
                @frog = get(@firstname, "Frog")
                @frog == 2 -> print("frog: $.variables.frog ")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_get1: lines: {lines}")
        print(f"test_function_get1: vars: {path.variables}")
        assert len(lines) == 1
        assert "frog" in path.variables
        assert path.variables["frog"] == 2

    def test_function_get2(self):
        path = CsvPath()
        Save._save(path, "test_function_get1")
        print("")
        with pytest.raises(ChildrenException):
            path.parse(
                f"""
                ${PATH}[1*]
                [
                    ~ if 1st arg is Var there must be a 2nd arg ~
                    tally(#firstname)
                    @frog = get(@firstname)
                    @frog == 2 -> print("frog: $.variables.frog ")
                ]"""
            )
            path.collect()

    def test_function_get3(self):
        path = CsvPath()
        Save._save(path, "test_function_get3")
        print("")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                push("names", #firstname)
                @fourth = get(@names, 4)
                ~ this existance test should fail until we have 4 items in the stack ~
                @fourth -> print("fourth: $.variables.fourth ")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_get3: lines: {lines}")
        print(f"test_function_get3: vars: {path.variables}")
        assert len(lines) == 4
        assert "fourth" in path.variables
        assert path.variables["fourth"] == "Bird"

    def test_function_get4(self):
        path = CsvPath()
        Save._save(path, "test_function_get1")
        print("")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                ~ tally is a value producer -- no impact on match ~
                tally(#firstname)
                ~ this is an assignment -- no impact on match ~
                @frog = get("firstname", #firstname)
                ~ left side of when/do has impact on match unless .nocontrib ~
                @frog == 2 -> print("frog: $.variables.frog ")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_get1: lines: {lines}")
        print(f"test_function_get1: vars: {path.variables}")
        assert len(lines) == 1
        assert "frog" in path.variables
        assert path.variables["frog"] == 2