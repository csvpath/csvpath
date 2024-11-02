import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.util.config import Config
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.exceptions import ChildrenException
from tests.save import Save

PATH = "tests/test_resources/test.csv"
NUMBERS = "tests/test_resources/numbers3.csv"


class TestValidBasicTypesDecimal(unittest.TestCase):
    def test_function_decimal1(self):
        path = CsvPath()
        Save._save(path, "test_function_decimal1")
        path.parse(
            f""" ${NUMBERS}[*] [
                @st = decimal("abc")
            ]
            """
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_function_decimal2(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_function_decimal2")
        path.parse(
            f""" ${NUMBERS}[1] [
                ~ too high 3.52 ~
                push("a", decimal("numbers31", 1, 1) )
                ~ too high 3.52 ~
                push("a", decimal(0, 1, 0) )
                ~ fits 3.52 ~
                push("a", decimal("numbers31", 20) )
                ~ fits 3.52 ~
                push("a", decimal(0, 20, 2) )
                ~ too low 3.52 ~
                push("a", decimal("numbers31", none(), 18.60) )
                ~ too high 3.52 ~
                push("a", decimal(0, -1, -50) )
                ~ too high 3.52 ~
                push("a", decimal("numbers31", -20) )
                ~ fits: 3.52 ~
                push("a", decimal(0, none(), -10) )
            ]
            """
        )
        path.collect()
        print(f"test_func_dec2: {path.variables}")
        expected = [False, False, True, True, False, False, False, True]
        print(f"expected:              {expected}")
        assert "a" in path.variables
        a = path.variables["a"]
        assert a == expected

    def test_function_decimal3(self):
        path = CsvPath()
        Save._save(path, "test_function_decimal3")
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: no-raise, no-stop
                  explain-mode:no-explain
                ~
                ${NUMBERS}[1*] [
                    or(
                        decimal.strict(1),
                        decimal.strict.notnone(2)
                    )
                ]"""
        )
        lines = path.collect()
        assert len(lines) == 2

    def test_function_decimal4(self):
        print("")
        testini = "tests/test_resources/deleteme/config.ini"
        os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = testini
        path = CsvPath()
        Save._save(path, "test_function_decimal4")
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: no-raise, no-stop ~
                ${NUMBERS}[1*] [
                        decimal.weak(1)
                        decimal.weak.notnone(2)
                ]"""
        )
        lines = path.collect()
        assert len(lines) == 7
