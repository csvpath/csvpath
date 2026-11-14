import unittest
import os
import io
from contextlib import redirect_stdout
from csvpath import CsvPath
from csvpath.matching.functions.function_factory import FunctionFactory

NUMBERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers.csv"
PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsPercentDups(unittest.TestCase):
    def test_function_percent_dups1(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [
                @d = percent_dups()
            ]
            """
        )
        path.fast_forward()
        assert path.variables["d"] == 0

    def test_function_percent_dups2(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [
                @d = percent_dups(#lastname)
            ]
            """
        )
        path.fast_forward()
        assert path.variables["d"] > 66

    def test_function_percent_dups_does_not_block_matching(self):
        # issue #574: _decide_match compared instead of assigning, so a bare
        # percent_dups() left match at None and failed every line. As a value
        # producer it should match by default, like count_dups().
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [
                percent_dups()
            ]
            """
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_function_percent_dups_header_arg_does_not_block_matching(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [
                @d = percent_dups(#lastname)
                percent_dups.other(#lastname)
            ]
            """
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_function_percent_dups_does_not_print(self):
        # issue #574: a stray debug print() ran on every line.
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [
                @d = percent_dups(#lastname)
            ]
            """
        )
        out = io.StringIO()
        with redirect_stdout(out):
            path.fast_forward()
        assert out.getvalue() == ""

    def test_function_percent_dups_default_match_in_or_mode(self):
        # percent_dups() takes the default match, not a fixed True: under
        # OR logic the default is False, so it does not match on its own.
        # Same as count_dups().
        path = CsvPath()
        path.parse(
            f"""~ logic-mode: OR ~ ${PATH}[*] [
                percent_dups()
            ]
            """
        )
        lines = path.collect()
        assert len(lines) == 0


class TestCsvPathFunctionsPercentDupsDescription(unittest.TestCase):
    def test_says_it_has_internal_variables_before_any_line(self):
        #
        # the CLI function lister builds each function this way and the
        # describer reads has_internal_variables before any run. like the
        # other dups functions, percent_dups() keeps its fingerprints in a
        # variable, so it must say so up front. (_register_internal_var_name
        # only sets the flag once a line runs.)
        #
        for name in ["percent_dups", "count_dups", "has_dups", "dup_lines"]:
            f = FunctionFactory.get_function(
                None, name=name, child=None, find_external_functions=False
            )
            assert f.has_internal_variables is True, name
