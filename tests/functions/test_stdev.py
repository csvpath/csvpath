import unittest
from csvpath.csvpath import CsvPath

COR = "tests/test_resources/correlation.csv"


class TestFunctionsStdev(unittest.TestCase):
    def test_function_stdev1(self):
        path = CsvPath()
        path.parse(
            f"""${COR}[1-10][
                    push("a", #1)
                    last.nocontrib() -> @sd = stdev(stack("a"))
                    last.nocontrib() -> print("stdev $.variables.sd")
                ]
             """
        )
        lines = path.collect()
        print(f"test_function_correlation: variables: {path.variables}")
        print(f"lines: {lines}")
        assert "sd" in path.variables
        assert path.variables["sd"] == 15138.25

    def test_function_stdev2(self):
        path = CsvPath()
        path.parse(
            f"""${COR}[1-10][
                    push("a", #1)
                    last.nocontrib() -> @sd = pstdev(stack("a"))
                    last.nocontrib() -> print("pstdev $.variables.sd")
                ]
             """
        )
        lines = path.collect()
        print(f"test_function_correlation: variables: {path.variables}")
        print(f"lines: {lines}")
        assert "sd" in path.variables
        assert path.variables["sd"] == 14361.41
