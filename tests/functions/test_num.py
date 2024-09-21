import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsNum(unittest.TestCase):
    def test_function_num(self):
        path = CsvPath()
        Save._save(path, "test_function_num")
        path.parse(
            f"""${PATH}[1][
                @t = num("100,123")
                @d = num("$1,000.01")

            ]"""
        )
        path.collect()
        print(f"test_function_num: path vars: {path.variables}")
        assert "t" in path.variables
        assert "d" in path.variables
        assert path.variables["t"] == 100123
        assert path.variables["d"] == 1000.01
