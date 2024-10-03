import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsInt(unittest.TestCase):
    def test_function_int0(self):
        path = CsvPath()
        Save._save(path, "test_function_int0")
        path.parse(
            f"""
            ~ arg-validation-mode: print ~
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
        assert path.variables["no"] == 0
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
