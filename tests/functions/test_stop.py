import unittest
from csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


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

    def test_function_skip_all1(self):
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

    def test_function_stop_all1(self):
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
