import unittest
import pytest
from csvpath.csvpath import CsvPath
from csvpath.matching.util.exceptions import ChildrenException
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsSubstring(unittest.TestCase):
    def test_function_substring1(self):
        path = CsvPath()
        Save._save(path, "test_function_substring1")
        path.parse(
            f"""
            ${PATH}[*][
                @s = substring("testtest", 4)
            ]"""
        )
        path.fast_forward()
        print(f"test_function_substring1: path vars: {path.variables}")
        assert path.variables["s"] == "test"

    def test_function_substring2(self):
        path = CsvPath()
        Save._save(path, "test_function_substring2")
        path.parse(
            f"""
            ${PATH}[*][
                @s = substring("testtest", "no way!")
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.fast_forward()

    def test_function_substring3(self):
        path = CsvPath()
        Save._save(path, "test_function_substring3")
        path.parse(
            f"""
            ${PATH}[*][
                @s = substring("testtest", 40)
            ]"""
        )
        path.fast_forward()
        print(f"test_function_substring3: path vars: {path.variables}")
        assert path.variables["s"] == "testtest"

    def test_function_substring4(self):
        path = CsvPath()
        Save._save(path, "test_function_substring4")
        path.parse(
            f"""
            ${PATH}[*][
                @s = substring("", 0)
            ]"""
        )
        path.fast_forward()
        print(f"test_function_substring4: path vars: {path.variables}")
        assert path.variables["s"] == ""

    def test_function_substring5(self):
        path = CsvPath()
        Save._save(path, "test_function_substring5")
        path.parse(
            f"""
            ${PATH}[*][
                @s = substring("abcd", -2)
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.fast_forward()

    def test_function_startswith(self):
        path = CsvPath()
        Save._save(path, "test_function_startswith")
        path.parse(
            f"""
            ${PATH}[*]
            [
                @t1 = starts_with("# testtest", "#")
                @t2 = starts_with("! testtest", "#")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_startswith: path vars: {path.variables}")
        assert len(lines) == 9
        assert path.variables["t1"] is True
        assert path.variables["t2"] is False
