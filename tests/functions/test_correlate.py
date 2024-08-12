import unittest
from csvpath.csvpath import CsvPath

COR = "tests/test_resources/correlation.csv"


class TestFunctionsCorrelate(unittest.TestCase):
    def test_function_correlation1(self):
        path = CsvPath()
        path.parse(
            f"""${COR}[1-10][
                    push("a", #0)
                    push("b", #1)
                    last.nocontrib() -> @c = correlate.corr(stack("a"), stack("b"))
                    last.nocontrib() -> print("correlation $.variables.c")
                ]
             """
        )
        lines = path.collect()
        print(f"test_function_correlation: variables: {path.variables}")
        print(f"lines: {lines}")
        assert "c" in path.variables
        assert path.variables["c"] == 1.0

    def test_function_correlation2(self):
        path = CsvPath()
        path.parse(
            f"""${COR}[11-20][
                    push("a", #0)
                    push("b", #1)
                    last.nocontrib() -> @c = correlate.corr(stack("a"), stack("b"))
                    last.nocontrib() -> print("correlation $.variables.c")
                ]
             """
        )
        lines = path.collect()
        print(f"test_function_correlation: variables: {path.variables}")
        print(f"lines: {lines}")
        assert "c" in path.variables
        assert path.variables["c"] == 0.65

    def test_function_correlation3(self):
        path = CsvPath()
        path.parse(
            f"""${COR}[21-30][
                    push("a", #0)
                    push("b", #1)
                    last.nocontrib() -> @c = correlate.corr(stack("a"), stack("b"))
                    last.nocontrib() -> print("correlation $.variables.c")
                ]
             """
        )
        lines = path.collect()
        print(f"test_function_correlation: variables: {path.variables}")
        print(f"lines: {lines}")
        assert "c" in path.variables
        assert path.variables["c"] == 1.0
