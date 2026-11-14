import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsHasMatches(unittest.TestCase):
    #
    # has_matches() is True only when an earlier line matched (#573). It used
    # to compute current_match_count + 1 > 0, which is True on every line.
    #
    # test.csv: header, then 8 data lines. Only the first data line
    # (David,Kermit) has a lastname other than Bat.
    #

    def test_has_matches_false_when_nothing_matches(self):
        path = CsvPath()
        path.parse(f"""${PATH}[1*][ no() push("hm", has_matches()) ]""")
        lines = path.collect()
        assert len(lines) == 0
        assert path.variables["hm"] == [False] * 8

    def test_has_matches_turns_true_on_the_line_after_the_first_match(self):
        #
        # line 1 (Kermit) does not match. line 2 is the first match, so
        # has_matches() is still False on line 2 and True from line 3 on.
        #
        path = CsvPath()
        path.parse(
            f"""${PATH}[1*][
                #lastname == "Bat"
                push.nocontrib("hm", has_matches())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 7
        assert path.variables["hm"] == [False, False] + [True] * 6

    def test_has_matches_ignores_an_early_raise_on_the_same_line(self):
        #
        # an onmatch component raises the match count partway through the
        # line it is on (Qualified.line_matches). push.onmatch checks the
        # line, which raises the count, and only then evaluates its
        # has_matches() argument. on line 1 the live count is already 1,
        # but no earlier line matched, so has_matches() must be False.
        #
        path = CsvPath()
        path.parse(
            f"""${PATH}[1*][
                yes()
                push.onmatch("hm", has_matches())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 8
        assert path.variables["hm"] == [False] + [True] * 7

    def test_has_matches_as_a_match_component(self):
        #
        # the docs example: has_matches() -> fail(). nothing else matches,
        # so the file must stay valid.
        #
        path = CsvPath()
        path.parse(
            f"""${PATH}[1*][
                #lastname == "Nope"
                has_matches.nocontrib() -> fail()
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0
        assert path.is_valid is True

    def test_has_matches_in_or_mode(self):
        #
        # with OR, a line matches when any component matches. only line 1
        # (Kermit) matches, so has_matches() is False on line 1 and True
        # from line 2 on.
        #
        path = CsvPath()
        path.OR = True
        path.parse(
            f"""${PATH}[1*][
                #lastname == "Kermit"
                push.nocontrib("hm", has_matches())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["hm"] == [False] + [True] * 7
