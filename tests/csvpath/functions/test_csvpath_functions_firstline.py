import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
EMPTY = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}empty.csv"


class TestCsvPathFunctionsFirstLine(unittest.TestCase):
    def test_function_firstline1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[0-7]
            [
                regex(/sniffle/, #say)
                firstline.nocontrib() -> @line = count_lines()
                firstmatch.nocontrib() -> @match = count_lines()
                firstscan.nocontrib() -> @scan = count_lines()

            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["line"] == 1
        assert path.variables["scan"] == 1
        assert path.variables["match"] == 5

    def test_function_firstline2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3-7]
            [
                regex(/sniffle/, #say)
                firstline.nocontrib() -> @line = count_lines()
                firstmatch.nocontrib() -> @match = count_lines()
                firstscan.nocontrib() -> @scan = count_lines()

            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert "line" not in path.variables
        assert path.variables["scan"] == 4
        assert path.variables["match"] == 5

    def test_function_firstline3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                firstscan.nocontrib() -> print("we scan the whole file from the 0th line")
                last.nocontrib() -> print("the file has $.csvpath.count_lines rows")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_function_firstline4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                firstline.nocontrib(fail()) ->
                    print("we scan the whole file from the 0th line but are failing.")
            ]"""
        )
        lines = path.collect()
        assert path.is_valid is False
        assert len(lines) == 9

    def test_function_firstline5(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.collect(
                f""" ${PATH}[*][
                    firstline.nocontrib(@t == fail()) ->
                        print("we scan the whole file from the 0th line but are failing.")
                ]"""
            )


class TestCsvPathFunctionsFirstLineAliases:
    #
    # first_scan and first_match are registered aliases of firstscan and
    # firstmatch, but check_valid() did not list them, so both were rejected
    # with "Unknown function name". each alias must behave exactly like its
    # canonical name. scanning from line 2, so line, scan and match differ.
    #
    ALIASES = [
        ("firstline", "first_line"),
        ("firstscan", "first_scan"),
        ("firstmatch", "first_match"),
    ]

    def _run(self, name: str, mode: str, scan: str = "[2*]"):
        path = CsvPath()
        path.parse(
            f"~ validation-mode: {mode}, no-print ~ ${PATH}{scan}[ #lastname == \"Bat\" {name}() ]"
        )
        lines = path.collect()
        return [line[0] for line in lines], len(path.errors)

    @pytest.mark.parametrize("scan", ["[1*]", "[2*]"])
    @pytest.mark.parametrize("mode", ["raise", "no-raise"])
    @pytest.mark.parametrize("canonical,alias", ALIASES)
    def test_alias_matches_canonical(self, canonical, alias, mode, scan):
        assert self._run(alias, mode, scan) == self._run(canonical, mode, scan)

    def test_what_each_name_selects(self):
        #
        # test.csv: line 1 is Kermit (not a Bat), line 2 is Fish (the first
        # Bat). in [1*] the first scanned line is Kermit, which does not
        # match, so only first_match collects Fish. in [2*] the first
        # scanned line is Fish; first_line still never fires, because
        # data line 0 (Kermit) is not scanned.
        #
        assert self._run("first_line", "raise", "[1*]") == ([], 0)
        assert self._run("first_scan", "raise", "[1*]") == ([], 0)
        assert self._run("first_match", "raise", "[1*]") == (["Fish"], 0)
        assert self._run("first_line", "raise", "[2*]") == ([], 0)
        assert self._run("first_scan", "raise", "[2*]") == (["Fish"], 0)
        assert self._run("first_match", "raise", "[2*]") == (["Fish"], 0)
