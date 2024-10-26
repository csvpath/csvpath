import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsInt(unittest.TestCase):
    def test_function_int0(self):
        path = CsvPath()
        Save._save(path, "test_function_int0")
        path.parse(
            f"""
            ~ validation-mode: print ~
            ${PATH}[*] [
                @st = int(" 3 ")
                @no = int(float(3))
                @bo = int(no())
                @b2 = int( "3.2" )
                @b3 = int( -3.3 )
            ]
            """
        )
        path.collect()
        print(f"\ntest_function_int0: path.vars: {path.variables}")
        assert path.variables["st"] == 3
        assert path.variables["no"] == 3
        assert path.variables["bo"] == 0
        assert path.variables["b2"] == 3
        assert path.variables["b3"] == -3

    def test_function_int1(self):
        path = CsvPath()
        Save._save(path, "test_function_int1")
        path.parse(
            f""" ${PATH}[*] [
                @st = int(" ")
                @no = int(none())
                @bo = int(no())
            ]
            """
        )
        path.collect()
        assert path.variables["st"] == 0
        assert path.variables["no"] is None
        assert path.variables["bo"] == 0

    def test_function_int2(self):
        path = CsvPath()
        Save._save(path, "test_function_int2")
        path.parse(
            f""" ${PATH}[*] [
                @st = int(" 3 ")
                @no = int(yes())
                @bo = int(8.58)
                @so = int("$8,58")
            ]
            """
        )
        path.collect()
        assert path.variables["st"] == 3
        assert path.variables["no"] == 1
        assert path.variables["bo"] == 8
        assert path.variables["so"] == 8

    def test_function_num1(self):
        path = CsvPath()
        Save._save(path, "test_function_num1")
        path.parse(
            f""" ${PATH}[*] [
                @st = num(" 3 ")
                @no = num(" 3.5 ")
                @bo = num(8.58)
                @ca = num(yes())
                @so = num(8)
            ]
            """
        )
        path.collect()
        assert isinstance(path.variables["st"], float)
        assert isinstance(path.variables["no"], float)
        assert isinstance(path.variables["bo"], float)
        assert isinstance(path.variables["ca"], int)
        assert isinstance(path.variables["so"], int)
        assert path.variables["st"] == 3
        assert path.variables["no"] == 3.5
        assert path.variables["bo"] == 8.58
        assert path.variables["ca"] == 1
        assert path.variables["so"] == 8

    def test_function_num2(self):
        path = CsvPath()
        Save._save(path, "test_function_num2")
        path.parse(
            f""" ${PATH}[1] [
                num(3.52, 1, 1, 2)
                num(3.5, 1, 0, 1)
                num(18.58, 2, -1, 2)
                num(18.58, 20, 2, -1)
                num(18.58, -1, -1, 2)
                num(18.58, -1, 0, -1)
            ]
            """
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_function_num3(self):
        path = CsvPath()
        Save._save(path, "test_function_num3")
        path.parse(
            f""" ${PATH}[1] [
                and(
                   not( num(3.52, 1, 1, 1)),
                   not( num(3.5, 2, 2, 1)),
                   not( num(18.58, 5, 3, 2)),
                   not( num(18.58, 2, 1, 0, 0)),
                   not( num(1.5, 0, -1, 2, 0)),
                   not( num(18.58, 3, 1, 0))
                )
            ]
            """
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_function_float1(self):
        path = CsvPath()
        Save._save(path, "test_function_float1")
        path.parse(
            f""" ${PATH}[*] [
                @st = float(" 3 ")
                @no = float(" 3.5 ")
                @bo = float("$5.39")
                @ca = float("$5000,39")
                @so = float(yes())
            ]
            """
        )
        path.collect()
        assert isinstance(path.variables["st"], float)
        assert isinstance(path.variables["no"], float)
        assert isinstance(path.variables["bo"], float)
        assert isinstance(path.variables["ca"], float)
        assert isinstance(path.variables["so"], float)
        assert path.variables["st"] == 3.0
        assert path.variables["no"] == 3.5
        assert path.variables["bo"] == 5.39
        assert path.variables["ca"] == 5000.39
        assert path.variables["so"] == 1

    def test_function_float2(self):
        path = CsvPath()
        Save._save(path, "test_function_float2")
        path.parse(
            f""" ${PATH}[*] [
                @st = float(" 3 ")
                @no = float(" 3.5 ")
                @bo = float("$5.39")
                @ca = float("$5000,39")
                @so = float(yes())
            ]
            """
        )
        path.collect()
        assert isinstance(path.variables["st"], float)
        assert isinstance(path.variables["no"], float)
        assert isinstance(path.variables["bo"], float)
        assert isinstance(path.variables["ca"], float)
        assert isinstance(path.variables["so"], float)
        assert path.variables["st"] == 3.0
        assert path.variables["no"] == 3.5
        assert path.variables["bo"] == 5.39
        assert path.variables["ca"] == 5000.39
        assert path.variables["so"] == 1

    def test_function_float_mul1(self):
        path = CsvPath()
        Save._save(path, "test_function_float_mul1")
        path.parse(
            f""" ${PATH}[*] [
                @s2 = float(multiply(-1,3.8))
            ]
            """
        )
        path.collect()
        print(f"test_function_float_mul1: path.vars: {path.variables}")
        assert isinstance(path.variables["s2"], float)
        assert path.variables["s2"] == -3.8

    def test_function_float_notnone1(self):
        path = CsvPath()
        Save._save(path, "test_function_float_notnone1")
        path.parse(
            f""" ${PATH}[*] [
                push("nofloat", float(none()))
                            ]
            """
        )
        path.fast_forward()
        assert path.variables["nofloat"] == [
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ]

    def test_function_float_notnone2(self):
        path = CsvPath()
        Save._save(path, "test_function_float_notnone2")
        path.parse(
            f"""
             ~ validation-mode: no-match no-raise ~
            ${PATH}[*] [
                float.notnone(none())
            ]
            """
        )
        lines = path.collect()
        assert len(lines) == 0
