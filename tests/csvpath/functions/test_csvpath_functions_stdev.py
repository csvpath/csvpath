import unittest
import pytest
import os
import statistics
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

COR = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}correlation.csv"


class TestCsvPathFunctionsStdev(unittest.TestCase):
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
        #
        # pstdev() takes the stack it is named, not some other stack. this
        # used to push to "a" and read "b", and only checked that the
        # variable existed. now two stacks hold different data and the
        # result must be the population stdev of the named one.
        #
        path = CsvPath()

        path.parse(
            f"""${COR}[1-10][
                    ~ stack name in pstdev ~
                    push("a", #0)
                    push("b", #1)
                    last.nocontrib() -> @sd = pstdev("b")
                ]
             """
        )
        path.collect()
        # rows 1-10 of the Salary column are 30000 to 75000 in steps of
        # 5000. pstdev() rounds to 2 places.
        salaries = [30000 + 5000 * i for i in range(10)]
        expected = round(statistics.pstdev(salaries), 2)
        assert expected == 14361.41
        assert path.variables["b"] == [str(s) for s in salaries]
        assert path.variables["sd"] == expected
        # the Years stack, 1 to 10, would give a very different value
        assert path.variables["sd"] != round(statistics.pstdev(range(1, 11)), 2)

    def test_function_stdev6(self):
        #
        # a stack name that was never pushed to has no values, so there is
        # no stdev. the docs do not say what is returned; this pins None.
        #
        path = CsvPath()
        path.parse(
            f"""${COR}[1-10][
                    push("a", #1)
                    last.nocontrib() -> @sd = pstdev("never_pushed")
                ]
             """
        )
        path.collect()
        assert "sd" in path.variables
        assert path.variables["sd"] is None
