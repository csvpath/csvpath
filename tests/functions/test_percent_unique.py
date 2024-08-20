import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsPercentUnique(unittest.TestCase):
    def test_function_percent_unique(self):
        path = CsvPath()
        Save._save(path, "test_function_percent_unique")
        path.parse(
            f"""${PATH}[1-4][
                            not(#2 == "ribbit...")
                            @p = percent_unique.last.onmatch( #lastname) ]"""
        )
        lines = path.collect()
        print(f"test_function_percent_unique: path vars: {path.variables}")
        assert len(lines) == 3
        assert path.variables["p"] == 33
