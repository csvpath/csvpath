import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import ChildrenException
from tests.save import Save

PATH = "tests/test_resources/numbers2.csv"


class TestFunctionsSubtotal(unittest.TestCase):
    def test_function_subtotal1(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_function_subtotal1")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                subtotal.areas(#area, #count1)
                last() -> print("$.variables.areas")
            ]"""
        )
        path.fast_forward()
        assert "earth" in path.variables["areas"]
        assert path.variables["areas"]["earth"] == 6
        assert "space" in path.variables["areas"]
        assert path.variables["areas"]["space"] == 16
        assert "ocean" in path.variables["areas"]
        assert path.variables["areas"]["ocean"] == 10

    def test_function_subtotal2(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_function_subtotal2")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                subtotal.areas(#count1, #area)
                last() -> print("$.variables.areas")
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.fast_forward()

    def test_function_subtotal3(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_function_subtotal3")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                subtotal.areas(#area)
                last() -> print("$.variables.areas")
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.fast_forward()

    def test_function_subtotal4(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_function_subtotal4")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                subtotal.areas(#area, #count1, #count2)
                last() -> print("$.variables.areas")
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.fast_forward()
