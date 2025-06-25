import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.util.printer import LogPrinter
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathComments(unittest.TestCase):
    def test_update_settings_from_metadata(self):
        path = CsvPath()
        assert path.OR is False
        assert path.collect_when_not_matched is False
        assert path.has_default_printer is True
        assert path.print_validation_errors is True
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ~ logic-mode: OR
              return-mode: no-matches
              print-mode: no-default
              validation-mode: raise no-print
            ~
            ${PATH}[1*]
            [
                ~ this path is simple and so are its comments ~
                yes()
            ]
            """
        )
        assert "logic-mode" in path.metadata
        assert "return-mode" in path.metadata
        assert "print-mode" in path.metadata
        assert "validation-mode" in path.metadata
        assert path.OR is True
        assert path.collect_when_not_matched is True
        assert path.has_default_printer is False
        assert path.print_validation_errors is False

    def test_update_settings_from_metadata2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.add_printer(LogPrinter(path.logger))
        assert path.print_validation_errors is True
        path.parse(
            f"""
            ~ validation-mode: print no-raise ~
            ${PATH}[1*][
                ~ this path is simple and so are its comments ~
                @c = concat("a", "b", "c")
                print("$.variables.c")
            ]
            """
        )
        assert "validation-mode" in path.metadata
        assert path.log_validation_errors is True
        assert path.print_validation_errors is True
        assert path.raise_validation_errors is False
        path.fast_forward()
        for p in path.printers:
            assert p.last_line and p.last_line.find("abc") > -1

    def test_update_settings_from_metadata3(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise, collect")
        assert path.raise_validation_errors is None
        path.parse(
            f"""
            ~ validation-mode: raise, print ~
            ${PATH}[1*][
                ~ this path is simple and so are its comments ~
                @a = add("five", none())
                print("$.variables.a")
            ] """
        )
        assert "validation-mode" in path.metadata
        assert path.log_validation_errors is True
        assert path.print_validation_errors is True
        assert path.raise_validation_errors is True
        with pytest.raises(MatchException):
            path.fast_forward()
        for p in path.printers:
            assert p.last_line and p.last_line.find("add requires") > -1
        assert path.has_errors() is True

    def test_update_settings_from_metadata_match_error_1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        assert path.raise_validation_errors is None
        path.parse(
            f"""
            ~
            id:match :
            because we have match we will ignore the four errors and collect 8 lines.
            validation-mode: print, match, no-raise, no-stop, collect
            ~
            ${PATH}[1*][
                mod.nocontrib(line_number(), 2) == 1 -> @a = 5
                mod.nocontrib(line_number(), 2) == 0 -> @a = "five"
                ~ every other line we blow up, but because we're matching
                  validation errors we collect all the lines ~
                @b = add( @a, 1 )
            ]
            """
        )
        lines = path.collect()
        assert len(lines) == 8
        assert path.has_errors() is True

    def test_update_settings_from_metadata_match_error_2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""~
            because we don't have validation-mode match we will only match on non-error lines == 4
            validation-mode: print, no-raise, no-stop ~
            ${PATH}[1*][
                mod.nocontrib(line_number(), 2) == 1 -> @a = 5
                mod.nocontrib(line_number(), 2) == 0 -> @a = "five"
                @b = add( @a, 1 )
            ]
            """
        )
        lines = path.collect()
        assert len(lines) == 4

    def test_comments_below(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ~ checking collection of metadata,
              not the actual modes. logic: AND collect: no-matches : ~
            ${PATH}[1*]
            [
                ~ this path is simple and so are its comments ~
                push.onmatch("cnt", count_lines())
                count.nocontrib() == 3 -> advance(2)
            ]
            ~ what about me? fizzbats! ~
            """
        )
        assert "collect" in path.metadata
        assert path.metadata["collect"] == "no-matches"
        assert "logic" in path.metadata
        assert path.metadata["logic"] == "AND"
        assert "original_comment" in path.metadata
        assert path.metadata["original_comment"].find("fizzbats") > -1

    def test_comments1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""${PATH}[1*]
            [
                ~ this path is simple and so are its comments ~
                push.onmatch("cnt", count_lines())
                count.nocontrib() == 3 -> advance(2)
            ]"""
        )
        path.fast_forward()
        assert path.variables["cnt"] == [2, 3, 4, 7, 8, 9]

    def test_comments2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""${PATH}[1*]
            [
                ~ this path
                  has line breaks
                  in its comments ~
                push.onmatch("cnt", count_lines())
                count.nocontrib() == 3 -> advance(2)
            ]"""
        )
        path.fast_forward()
        assert path.variables["cnt"] == [2, 3, 4, 7, 8, 9]

    def test_comments_everything_except_tilde_and_right_bracket(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""${PATH}[1*]
            [
                ~
                    [$#@"()!%^&*`@-/_=+{{}}#|  \\;:',.<>?()/"$[
                ~
                push("d", line_number())
            ]"""
        )
        path.fast_forward()
        assert len(path.variables["d"]) == 8

    def test_comments_back_to_back_and_empty(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""${PATH}[1*]
            [
                ~I have a lot to say ~ ~
                    [$#@"()!%^&*`@-/_=+{{}}#|\\;:',.<>?()/"$[
                ~~~
                push.onmatch("cnt", count_lines())
                count.nocontrib() == 3 -> advance(2)
            ]"""
        )
        path.fast_forward()
        assert path.variables["cnt"] == [2, 3, 4, 7, 8, 9]
