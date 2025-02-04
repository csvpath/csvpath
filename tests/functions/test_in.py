import unittest
import pytest
import os
from csvpath import CsvPaths, CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"
FOOD = f"tests{os.sep}test_resources{os.sep}food.csv"


class TestFunctionsIn(unittest.TestCase):
    def test_function_header_in1(self):
        path = CsvPath()
        path.parse(f'${PATH}[*][in(#firstname,"Bug|Bird|Ants")]')
        lines = path.collect()
        assert len(lines) == 3

    def test_function_count_in2(self):
        """~this test is also in with count but there using onmatch"""
        path = CsvPath()
        path.parse(
            f"""
                        ${PATH}
                        [*]
                        [count.one( in(#firstname,"Bug|Bird|Ants") ) == 2]
                   """
        )
        lines = path.collect()
        assert len(lines) == 2
        assert "one" in path.variables
        assert path.variables["one"][True] == 3
        assert path.variables["one"][False] == 6

    def test_function_count_in3(self):
        path = CsvPath()
        path.parse(
            f"""
                ${PATH}
                [*]
                [
                    @x.onmatch = count()
                    in(#firstname,"Bug|Bird|Ants")
                ]
                   """
        )
        lines = path.collect()
        assert "x" in path.variables
        assert path.variables["x"] == 3
        assert len(lines) == 3

    def test_function_in4(self):
        path = CsvPath()
        path.parse(
            f"""${FOOD}[*]
                        [ ~ Find the first time fruit were the most popular ~
                            @fruit = in( #food, "Apple|Pear|Blueberry")
                            ~@food.onmatch = #food~
                            @fruit.asbool -> print("$.headers.food $.headers.year")
                            first.year.onmatch( #year )
                            exists( @fruit.asbool )
                            last.nocontrib() -> print("First years most popular: $.variables.year")
                        ]
                    """
        )
        path.collect()
        assert "year" in path.variables
        assert path.variables["year"]["1643"] == 4

    def test_function_in5(self):
        path = CsvPath()
        path.parse(f'${PATH}[*][in( #0 , "Bug|Bird|Ants" )]')
        lines = path.collect()
        assert len(lines) == 3

    def test_function_in6(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [
                @oc.onchange.onmatch = in(#firstname, "Frog|Bug|Fish")
                 print.onmatch("printing: oc: $.variables.oc, count: $.csvpath.match_count")

            ]
            """
        )
        lines = path.collect()
        assert path.variables["oc"] is True
        assert len(lines) == 4

    def test_function_new_in1(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[1*] [
                yes()
                @oc = in(#firstname, #firstname)
            ]
            """
        )
        lines = path.collect()
        assert path.variables["oc"] is True
        assert len(lines) == 8

    def test_function_new_in2(self):
        path = CsvPath()

        path.parse(
            f""" ${PATH}[1*] [
                ~ changes from None to True on line 1; after that no changes
                  we determine matches in assignment when onchange; therefore,
                  just 1 match.
                ~
                @oc.onchange = in(#firstname, #firstname)
                ~ we only print on match so one print ~
                @cnt = count()
                print.onmatch(
                    "printing: oc: $.variables.oc, $.variables.cnt,
                    count: $.csvpath.count_matches @ $.csvpath.line_number")
            ]
            """
        )
        lines = path.collect()
        assert path.variables["oc"] is True
        assert len(lines) == 1

    def test_function_new_in3(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[1*] [
                @oc.onchange = in(#firstname, #say, #firstname, #lastname)
                @cnt = count()
                print.onmatch(
                    "printing: oc: $.variables.oc, $.variables.cnt,
                    count: $.csvpath.count_matches @ $.csvpath.line_number")
            ]
            """
        )
        lines = path.collect()
        assert path.variables["oc"] is True
        assert len(lines) == 1

    def test_function_new_in4(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[1*] [
                @oc = in(#firstname, "Brazil", #say, "Bird")
                in(#firstname, "Bird")
                @cnt = count()
                @lc.onmatch = count_lines()
                @ln.onmatch = line_number()
                print.onmatch(
                    "printing: oc: $.variables.oc, $.headers.firstname, $.variables.cnt,
                    count: $.csvpath.count_matches @ $.csvpath.line_number")
            ]
            """
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["oc"] is False
        assert path.variables["ln"] == 5
        assert path.variables["lc"] == 6
        assert path.variables["cnt"] == 1

    def test_function_new_in5(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.file_manager.add_named_file(name="food", path=FOOD)
        paths.paths_manager.add_named_paths_from_dir(
            directory=f"tests{os.sep}test_resources{os.sep}named_paths"
        )

        paths.fast_forward_paths(pathsname="food_lookup", filename="food")

        path = paths.csvpath()

        path.parse(
            f""" ${FOOD}[1*] [
                @food_found = in(#food, $food_lookup.variables.food_names)
            ]
            """
        )
        lines = path.collect()
        assert len(lines) == 10
        assert path.variables["food_found"] is True

    def test_function_new_in6(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]
        with pytest.raises(MatchException):
            path.parse(
                f""" ${FOOD}[1*] [
                    ~ we have no CsvPaths so we should blow up ~
                    @food_found = in(#food, $food_lookup.variables.food)
                ]
                """
            )
            path.fast_forward()

    def test_function_new_in7(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.file_manager.add_named_file(name="food", path=FOOD)
        paths.paths_manager.add_named_paths_from_dir(
            directory=f"tests{os.sep}test_resources{os.sep}named_paths"
        )
        paths.collect_paths(pathsname="food_lookup", filename="food")

        path = paths.csvpath()
        path.parse(
            f""" ${FOOD}[1*] [
                @food_found = in(#food, $food_lookup.headers.food)
            ]
            """
        )
        lines = path.collect()
        assert len(lines) == 10

    def test_function_in_bad1(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]
        path._raise_validation_errors = True
        path.parse(
            f""" ${FOOD}[1*] [
                @food_found = in(#food)
            ]
            """
        )
        with pytest.raises(MatchException):
            path.fast_forward()
