import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

COR = "tests/test_resources/correlation.csv"


class TestFunctionsStdev(unittest.TestCase):
    def test_function_stdev1(self):
        path = CsvPath()
        Save._save(path, "test_function_stdev1")
        path.parse(
            f"""${COR}[1-10][
                    push("a", #1)
                    last.nocontrib() -> @sd = stdev(stack("a"))
                    last.nocontrib() -> print("stdev $.variables.sd")
                ]
             """
        )
        lines = path.collect()
        print(f"test_function_stdev1: variables: {path.variables}")
        print(f"lines: {lines}")
        assert "sd" in path.variables
        assert path.variables["sd"] == 15138.25

    def test_function_stdev2(self):
        path = CsvPath()
        Save._save(path, "test_function_stdev2")
        path.parse(
            f"""${COR}[1-10][
                    push("a", #1)
                    last.nocontrib() -> @sd = pstdev(stack("a"))
                    last.nocontrib() -> print("pstdev $.variables.sd")
                ]
             """
        )
        lines = path.collect()
        print(f"test_function_stdev2: variables: {path.variables}")
        print(f"lines: {lines}")
        assert "sd" in path.variables
        assert path.variables["sd"] == 14361.41
