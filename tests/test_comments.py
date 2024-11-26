import unittest
import pytest
from csvpath import CsvPath
from csvpath import CsvPaths
from csvpath.util.printer import LogPrinter
from csvpath.matching.util.exceptions import MatchException

PATH = "tests/test_resources/test.csv"


class TestComments(unittest.TestCase):
    def test_update_settings_from_metadata(self):
        path = CsvPath()
        print("")
        assert path.OR is False
        assert path.collect_when_not_matched is False
        assert path.has_default_printer is True
        assert path.print_validation_errors is True
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
        print(f"path meta: {path.metadata}")
        assert "logic-mode" in path.metadata
        assert "return-mode" in path.metadata
        print(f"returnmode: {path.metadata['return-mode']}")
        assert "print-mode" in path.metadata
        assert "validation-mode" in path.metadata
        assert path.OR is True
        assert path.collect_when_not_matched is True
        assert path.has_default_printer is False
        assert path.print_validation_errors is False

    def test_update_settings_from_metadata2(self):
        path = CsvPath()
        path.add_printer(LogPrinter(path.logger))
        assert path.print_validation_errors is True
        path.parse(
            f"""
            ~
            validation-mode: print no-raise
            ~
            ${PATH}[1*][
                ~ this path is simple and so are its comments ~
                concat("a", "b", stack("s"))
            ]
            """
        )
        print(f"path meta: {path.metadata}")
        assert "validation-mode" in path.metadata
        assert path.log_validation_errors is True
        assert path.print_validation_errors is True
        assert path.raise_validation_errors is False
        path.fast_forward()
        for p in path.printers:
            print(f"last linnnner: {p.last_line}")
            assert (
                p.last_line and p.last_line.find("Wrong value in match component") > -1
            )

    def test_update_settings_from_metadata3(self):
        path = CsvPath()
        assert path.raise_validation_errors is None
        path.parse(
            f"""
            ~
            validation-mode: raise print
            ~
            ${PATH}[1*][
                ~ this path is simple and so are its comments ~
                concat("a", "b", stack("s"))
            ]
            """
        )
        print(f"path meta: {path.metadata}")
        assert "validation-mode" in path.metadata
        assert path.log_validation_errors is True
        assert path.print_validation_errors is True
        assert path.raise_validation_errors is True
        with pytest.raises(MatchException):
            path.fast_forward()
        for p in path.printers:
            assert (
                p.last_line and p.last_line.find("Wrong value in match component") > -1
            )
        assert path.has_errors() is True

    def test_update_settings_from_metadata_match_error(self):
        path = CsvPath()
        assert path.raise_validation_errors is None
        path.parse(
            f"""
            ~ validation-mode: print, match, no-raise, no-stop ~
            ${PATH}[1*][
                mod.nocontrib(line_number(), 2) == 1 -> @a = 5
                mod.nocontrib(line_number(), 2) == 0 -> @a = "five"
                ~ every other line we blow up, but because we're matching
                  validation errors we collect all the lines ~
                add( @a, 1 )
            ]
            """
        )
        lines = path.collect()
        assert path.has_errors() is True
        assert len(lines) == 8

        path = CsvPath()
        assert path.raise_validation_errors is None
        path.parse(
            f"""
            ~ validation-mode: print, no-raise, no-stop ~
            ${PATH}[1*][
                mod.nocontrib(line_number(), 2) == 1 -> @a = 5
                mod.nocontrib(line_number(), 2) == 0 -> @a = "five"
                add( @a, 1 )
            ]
            """
        )
        lines = path.collect()
        assert len(lines) == 4

    def test_comment_settings_affecting_multiple_paths(self):
        paths = CsvPaths()
        """~ 3 paths:
                - AND no matches all returned
                - OR all match all returned
                - AND no matches none returned
                - OR all match none returned
        ~"""
        paths.file_manager.add_named_file(
            name="test", path="tests/test_resources/test.csv"
        )
        settings = {}
        settings["settings"] = [
            """~ logic-mode:AND return-mode:no-matches print-mode:default ~ $[1][ yes() no() print("Hi $.csvpath.line_number")]""",
            """~ logic-mode:OR return-mode:matches print-mode:default  ~ $[2][ yes() no() print("Hi $.csvpath.line_number")]""",
            """~ logic-mode:AND return-mode:matches print-mode:no-default  ~ $[3][ yes() no() print("Hi $.csvpath.line_number")]""",
            """~ logic-mode:OR return-mode:no-matches print-mode:no-default ~ $[4][ yes() no() print("Hi $.csvpath.line_number")]""",
        ]
        paths.paths_manager.set_named_paths(settings)
        paths.collect_paths(filename="test", pathsname="settings")
        results = paths.results_manager.get_named_results("settings")
        assert len(results) == 4
        assert len(results[0]) == 1
        # results has 1 line that was printed by print()
        # results[0].csvpath handed that 1 line off to two printers: StdOut and the Result
        assert results[0].lines_printed < len(results[0].csvpath.printers)
        assert len(results[1]) == 1
        assert results[1].lines_printed < len(results[1].csvpath.printers)
        assert len(results[2]) == 0
        # the print mode removes StdOut from results[2].csvpath leaving 1 printer, Result
        assert results[2].lines_printed == len(results[2].csvpath.printers)
        assert len(results[3]) == 0
        assert results[3].lines_printed == len(results[3].csvpath.printers)

    def test_comments_below(self):
        path = CsvPath()
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
        print(f"path meta: {path.metadata}")
        assert "collect" in path.metadata
        assert path.metadata["collect"] == "no-matches"
        assert "logic" in path.metadata
        assert path.metadata["logic"] == "AND"
        assert "original_comment" in path.metadata
        assert path.metadata["original_comment"].find("fizzbats") > -1

    def test_comments1(self):
        path = CsvPath()
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
        path.parse(
            """$tests/test_resources/test.csv[1*]
            [
                ~
                    [$#@"()!%^&*`@-/_=+{}#|  \\;:',.<>?()/"$[
                ~
                push("d", line_number())
            ]"""
        )
        path.fast_forward()
        assert len(path.variables["d"]) == 8

    def test_comments_back_to_back_and_empty(self):
        path = CsvPath()
        path.parse(
            """$tests/test_resources/test.csv[1*]
            [
                ~I have a lot to say ~ ~
                    [$#@"()!%^&*`@-/_=+{}#|\\;:',.<>?()/"$[
                ~~~
                push.onmatch("cnt", count_lines())
                count.nocontrib() == 3 -> advance(2)
            ]"""
        )
        path.fast_forward()
        assert path.variables["cnt"] == [2, 3, 4, 7, 8, 9]
