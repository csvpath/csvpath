import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

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
        print(f"test_function_stdev1: variables: {path.variables}")
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
        print(f"test_function_stdev2: variables: {path.variables}")
        print(f"lines: {lines}")
        assert "sd" in path.variables
        assert path.variables["sd"] == 14361.41

    def test_function_stdev3(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]

        path.parse(
            f"""${COR}[1-10][
                    ~ not stack, not string ~
                    last.nocontrib() -> @sd = pstdev(1)
                ]
             """
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_function_stdev4(self):
        path = CsvPath()

        path.parse(
            f"""${COR}[1-10][
                    ~ stack name in pstdev ~
                    push("a", #1)
                    last.nocontrib() -> @sd = pstdev("a")
                    last.nocontrib() -> print("pstdev $.variables.sd")
                ]
             """
        )
        lines = path.collect()
        print(f"test_function_stdev2: variables: {path.variables}")
        print(f"lines: {lines}")
        assert "sd" in path.variables
        assert path.variables["sd"] == 14361.41

    def test_function_stdev5(self):
        path = CsvPath()

        path.parse(
            f"""${COR}[1-10][
                    ~ stack name in pstdev ~
                    push("a", #1)
                    last.nocontrib() -> @sd = pstdev("b")
                    last.nocontrib() -> print("pstdev $.variables.sd")
                ]
             """
        )
        lines = path.collect()
        print(f"test_function_stdev2: variables: {path.variables}")
        print(f"lines: {lines}")
        assert "sd" in path.variables
        # assert path.variables["sd"] == 14361.41
