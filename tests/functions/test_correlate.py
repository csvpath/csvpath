import unittest
from csvpath.csvpath import CsvPath

COR = "tests/test_resources/correlation.csv"


class TestFunctionsCorrelate(unittest.TestCase):
    def test_function_correlation(self):
        path = CsvPath()
        path.parse(
            f"""${COR}[1*][
                    @c = correlate.cor(#0, #1)
                    exists( @c.nocontrib )  -> print("$.variables.cor_variance")
                ]
             """
        )
        lines = path.collect()
        print(f"test_function_correlation: variables: {path.variables}")
        print(f"lines: {lines}")
        cor = path.variables["cor"]
        print(f"cor is {cor}")
        assert cor is not None
        assert cor == (10, 82.5, 2062500000.0, 412500.0, 1.0)
