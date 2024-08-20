import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsColumn(unittest.TestCase):
    def test_function_column(self):
        path = CsvPath()
        Save._save(path, "test_function_column")
        path.parse(
            f"""
            ${PATH}[*]
            [
                @i = column("firstname")
                @j = column("lastname")
                @n = column(2)
                @m = column(minus(1))
            ]"""
        )
        lines = path.collect()
        print(f"test_function_column: path vars: {path.variables}")
        assert len(lines) == 9
        assert path.variables["j"] == 1
        assert path.variables["i"] == 0
        assert path.variables["n"] == "say"
        assert path.variables["m"] == "lastname"
