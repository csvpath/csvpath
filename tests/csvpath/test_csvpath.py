import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.scanning.scanner import Scanner
from csvpath.util.config import OnError

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
PEOPLE = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}people2.csv"
EMPTY = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}empty2.csv"


class TestCsvPath(unittest.TestCase):
    def test_acsvpath_matcher_get_header(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(f"${PATH}[3][ yes() ]")
        path.fast_forward()
        v1 = path.matcher.get_header_value(None, 2)
        v2 = path.matcher.get_header_value(None, "say")
        assert v1 == v2
        assert v1 == "ribbit..."

    def test_acsvpath_matcher_get_header2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
                    ~ this test checks that a quoted field behaves correctly.
                      it is essentially a test of the csv lib, but worth keeping.
                      atm, CsvPath will not adjust a header that is incorrectly
                      quoted where the quote char is not directly following the
                      delimiter. this is a fixable problem, but unless it is seen
                      in the wild we can hold off. note that whitespace after a
                      quotechar and before a delimiter does not have the same
                      effect -- the field just as the whitespace as part of the
                      value. ~
                    ${PEOPLE}[3][
                        #date_of_birth == "May 12, 1962"
                        @dob = #date_of_birth
                        @hc = count_headers()
                        @hcl = count_headers_in_line()
                        @m = mismatch()
                    ]
                   """
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["dob"] == "May 12, 1962"

    def test_acsvpath_stop_when_last(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""${PATH}[0-5][
                push.onmatch("line", line_number())
            ]"""
        )
        path.fast_forward()
        assert path.line_monitor.physical_line_number == 5

    def test_acsvpath_total_lines_check(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(f"${PATH}[*][yes()]")
        path.fast_forward()
        assert path.line_monitor.data_line_count == 9

    def test_acsvpath_has_errors(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.config.csvpath_errors_policy = [OnError.COLLECT.value]
        path.parse(
            f"""${PATH}[1][
                            push.onmatch("i", int("five"))
                   ]"""
        )
        path.fast_forward()
        assert path.has_errors()

    def test_acsvpath_vars_frozen(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""${EMPTY}[*][
                            @c = count()
                            push.onmatch("line", line_number())
                            last.nocontrib() -> push("chk", "True")
                   ]"""
        )
        path.fast_forward()
        assert "c" in path.variables
        assert path.variables["c"] == 3
        assert "chk" in path.variables
        assert path.variables["chk"] == ["True"]
        assert "line" in path.variables
        assert path.variables["line"] == [0, 1, 2]

    def test_acsvpath_a_lot_of_csvpaths(self):
        #
        # we had an open files bug due to too many loggers. this
        # is just in case something similar.
        #
        for i in range(0, 1000):
            path = CsvPath()
            path.logger

    def test_acsvpath_includes(self):
        # pass line number = None probably in error
        scanner = Scanner()
        assert not scanner.includes(None)
        # is 3 in all lines?
        assert scanner.includes(3, from_line=None, to_line=None, all_lines=True)
        # is 3 >= 2?
        assert scanner.includes(3, from_line=2, to_line=None, all_lines=True)
        # is 1 >= 2?
        assert not scanner.includes(1, from_line=2, to_line=None, all_lines=True)
        # 3 = 3
        assert scanner.includes(3, from_line=3)
        # 3 is within 2 - 4
        assert scanner.includes(3, from_line=2, to_line=4)
        # 1 is not within 2 - 4
        assert not scanner.includes(1, from_line=2, to_line=4)
        # 3 is in (3,5,8)
        assert scanner.includes(3, these=[3, 5, 8])
        # 4 is not in (3,5,8)
        assert not scanner.includes(4, these=[3, 5, 8])
        # 3 is in 0 - 4
        assert scanner.includes(3, to_line=4)
        # 5 is not in 0 - 4
        assert not scanner.includes(5, to_line=4)

    def test_acsvpath_line_numbers(self):
        csvpath = CsvPath()
        assert [1, 2, 3] == csvpath._collect_line_numbers(these=[1, 2, 3])
        assert [1, 2, 3] == csvpath._collect_line_numbers(from_line=1, to_line=3)
        assert ["3..."] == csvpath._collect_line_numbers(from_line=3, all_lines=True)
        assert [3] == csvpath._collect_line_numbers(from_line=3)
        assert ["0..3"] == csvpath._collect_line_numbers(to_line=3)

    def test_acsvpath_collect_when_not_matched1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""${PATH}[1*][
            #lastname == "Bat"
        ]"""
        )
        lines = path.collect()
        assert len(lines) == 7

        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.collect_when_not_matched = True
        path.parse(
            f"""${PATH}[1*][
            #lastname == "Bat"
        ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_acsvpath_variables(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(f"${PATH}[2-4][@me = count()]")
        for i, ln in enumerate(path.next()):
            assert path.get_variable("me") == i + 1

    def test_acsvpath_header_counting(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(f"${PATH}[2-4][@me = count()]")
        assert path.header_index("lastname") == 1

    def test_acsvpath_header_index1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(f"${PATH}[1][yes()]")
        path.fast_forward()
        assert path.matcher.header_index("lastname") == 1
        assert path.matcher.header_index("1") == 1
        assert path.matcher.header_index(1) == 1
        assert path.matcher.header_index("foo") is None

    def test_acsvpath_collect_line_numbers(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(f"${PATH}[2-4][@me = count()]")
        lns = path.collect_line_numbers()
        assert lns == [2, 3, 4]

        path = CsvPath()
        path.parse(f"${PATH}[2*][@me = count()]")
        lns = path.collect_line_numbers()
        assert lns == ["2..."]

        path = CsvPath()
        path.parse(f"${PATH}[3-0][@me = count()]")
        lns = path.collect_line_numbers()
        assert lns == [0, 1, 2, 3]

        path = CsvPath()
        path.parse(f"${PATH}[3+0+5+1][@me = count()]")
        lns = path.collect_line_numbers()
        assert lns == [3, 0, 5, 1]

    def test_acsvpath_ff(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(f"${PATH}[*][@me = count()]")

        assert path.advance_count == 0
        path.advance(1)
        assert path.advance_count == 1
        for _ in path.next():
            assert _[0] == "David"
            break

        i = 0
        for _ in path.next():
            if i == 0:
                assert _[0] == "firstname"
                i += 1
                path.advance(4)
            elif i == 1:
                assert _[0] == "Bird"
                i += 1
            else:
                pass

        for _ in path.next():
            path.advance(14)
            assert path.advance_count == 8

        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(f"${PATH}[*][@me = count()]")
        i = 0
        for _ in path.next():
            path.advance(-1)
            assert path.advance_count == 8
            i += 1
        assert i == 1
