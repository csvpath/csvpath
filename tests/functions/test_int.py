import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestFunctionsInt(unittest.TestCase):
    def test_function_int0(self):
        path = CsvPath()
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
        print(f"path.var: {path.variables}")
        assert path.variables["st"] == 3
        assert path.variables["no"] == 3
        assert path.variables["bo"] == 0
        assert path.variables["b2"] == 3
        assert path.variables["b3"] == -3

    def test_function_int1(self):
        path = CsvPath()

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

    def test_function_float1(self):
        path = CsvPath()

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

        path.parse(
            f""" ${PATH}[*] [
                @s2 = float(multiply(-1,3.8))
            ]
            """
        )
        path.collect()
        assert isinstance(path.variables["s2"], float)
        assert path.variables["s2"] == -3.8

    def test_function_float_notnone1(self):
        path = CsvPath()

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

    def test_validity_int1(self):
        path = CsvPath().parse(f"""${PATH}[*][ int.notnone(none()) ]""")
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_validity_int2(self):
        path = CsvPath().parse(
            f""" ~id:int2~ ${PATH}[*][any(length(concat("a", int(random(0)))))]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_validity_int3(self):
        path = CsvPath().parse(f"""~id:int3~ ${PATH}[3][ int.notnone("a") ]""")
        path.config.add_to_config("errors", "csvpath", "raise, print")
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_validity_int4(self):
        path = CsvPath()
        path.parse(
            f"""~
                id:validity_int4
                validation-mode: print no-raise
            ~
            ${PATH}[*][
                int.notnone("a")
                int.notnone("b")
                and( int("c"), int("d") )
            ]"""
        )
        path.fast_forward()
