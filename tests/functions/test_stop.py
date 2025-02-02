import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestFunctionStop(unittest.TestCase):
    def test_function_stop(self):
        path = CsvPath()

        path.parse(
            f"""
            ${PATH}[*]
            [
                @i = concat( #firstname, #lastname)
                @c = count_lines()
                yes()
                stop(@i == "FishBat")
            ]"""
        )
        lines = path.collect()
        assert path.stopped is True
        assert path.variables["i"] == "FishBat"
        assert path.variables["c"] == 3
        assert len(lines) == 3

    def test_function_skip1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                @name = concat( #firstname, #lastname)
                skip(@name == "FishBat")
                push( "not_skipped", count_lines() )
                print("not skipped!")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 7
        assert path.variables["not_skipped"] == [2, 4, 5, 6, 7, 8, 9]

    def test_function_skip2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                skip.once(#lastname == "Bat")
                push.onmatch("line", count_lines())
            ]"""
        )
        path.fast_forward()
        assert "line" in path.variables
        assert path.variables["line"] == [1, 2, 4, 5, 6, 7, 8, 9]

    def test_function_all_skip_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                ~ no change in function in skip_all ~
                skip_all.once(#lastname == "Bat")
                push.onmatch("line", count_lines())
            ]"""
        )
        path.fast_forward()
        assert "line" in path.variables
        assert path.variables["line"] == [1, 2, 4, 5, 6, 7, 8, 9]

    def test_function_all_stop_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                ~ no change in behavior in stop_all() ~
                @i = concat( #firstname, #lastname)
                @c = count_lines()
                yes()
                stop_all(@i == "FishBat")
            ]"""
        )
        lines = path.collect()
        assert path.stopped is True
        assert path.variables["i"] == "FishBat"
        assert path.variables["c"] == 3
        assert len(lines) == 3

    def test_function_take_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*] [
                push("first_plus_header", #firstname)
                firstscan.nocontrib() -> take()
                push("firstname", #firstname)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
        #
        # if True, we skipped correctly
        #
        assert len(path.variables["firstname"]) == 8
        assert path.variables["firstname"][0] == "David"
        #
        # if True, we grabbed before we skipped
        #
        assert len(path.variables["first_plus_header"]) == 9
        assert path.variables["first_plus_header"][0] == "firstname"
        #
        # if True, we correctly actually did a take() rather than a skip()
        #
        assert lines[0][0] == "firstname"
