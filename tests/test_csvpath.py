import unittest
from csvpath import CsvPath
from csvpath.scanning.scanner import Scanner
from csvpath.util.config import OnError

PATH = "tests/test_resources/test.csv"


class TestCsvPath(unittest.TestCase):
    def test_matcher_get_header(self):
        path = CsvPath()
        path.parse("$tests/test_resources/test.csv[3][ yes() ]")
        path.fast_forward()
        v1 = path.matcher.get_header_value(2)
        v2 = path.matcher.get_header_value("say")
        print(f"\n test_matcher_get_header: : {v1} == {v2}")
        assert v1 == v2
        assert v1 == "ribbit..."

    def test_csvpath_stop_when_last(self):
        path = CsvPath()
        path.parse(
            """$tests/test_resources/test.csv[0-5][
                push.onmatch("line", line_number())
            ]"""
        )
        path.fast_forward()
        print(f"\n test_csvpath_stop_when_last: path.vars: {path.variables}")
        print(
            f"\n test_csvpath_stop_when_last: last line: {path.line_monitor.physical_line_number}"
        )
        assert path.line_monitor.physical_line_number == 5

    def test_csvpath_total_lines_check(self):
        path = CsvPath()
        path.parse(f"${PATH}[*][yes()]")
        path.fast_forward()
        assert path.line_monitor.data_line_count == 9

    def test_csvpath_has_errors(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = [OnError.COLLECT.value]
        print(f"path's policy: {path.config.csvpath_errors_policy}")
        path.parse(
            """$tests/test_resources/test.csv[1][
                            push.onmatch("i", int("five"))
                   ]"""
        )
        path.fast_forward()
        assert path.has_errors()
        errors = path.errors
        for e in errors:
            print(f">>> error: \n{e}\n")

    def test_csvpath_vars_frozen(self):
        path = CsvPath()
        path.parse(
            """$tests/test_resources/empty2.csv[*][
                            @c = count()
                            push.onmatch("line", line_number())
                            last.nocontrib() -> push("chk", "True")
                   ]"""
        )
        path.fast_forward()
        print(f"test_csvpath_vars_frozen: vars: {path.variables}")
        assert "c" in path.variables
        assert path.variables["c"] == 3
        assert "chk" in path.variables
        assert path.variables["chk"] == ["True"]
        assert "line" in path.variables
        assert path.variables["line"] == [0, 1, 2]

    def test_csvpath_a_lot_of_csvpaths(self):
        #
        # we had an open files bug due to too many loggers. this
        # is just in case something similar.
        #
        for i in range(0, 1000):
            print(f"test_csvpath_a_lot_of_csvpaths: starting {i}")
            path = CsvPath()
            print(f"test_csvpath_a_lot_of_csvpaths: made a {i}th CsvPath! {path}")

    def test_csvpath_includes(self):
        # csvpath = CsvPath()
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

    def test_csvpath_line_numbers(self):
        csvpath = CsvPath()
        assert [1, 2, 3] == csvpath._collect_line_numbers(these=[1, 2, 3])
        assert [1, 2, 3] == csvpath._collect_line_numbers(from_line=1, to_line=3)
        assert ["3..."] == csvpath._collect_line_numbers(from_line=3, all_lines=True)
        assert [3] == csvpath._collect_line_numbers(from_line=3)
        assert ["0..3"] == csvpath._collect_line_numbers(to_line=3)

    def test_csvpath_collect_when_not_matched1(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1*][
            #lastname == "Bat"
        ]"""
        )
        lines = path.collect()
        assert len(lines) == 7

        path = CsvPath()
        path.collect_when_not_matched = True
        path.parse(
            f"""${PATH}[1*][
            #lastname == "Bat"
        ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_csvpath_variables(self):
        path = CsvPath()
        scanner = path.parse(f"${PATH}[2-4][@me = count()]")
        print(f"{scanner}")
        for i, ln in enumerate(path.next()):
            assert path.get_variable("me") == i + 1
            print(f'...{i} = {path.get_variable("me")}')

    def test_csvpath_header_counting(self):
        path = CsvPath()
        path.parse(f"${PATH}[2-4][@me = count()]")
        assert path.header_index("lastname") == 1

    def test_csvpath_collect_line_numbers(self):
        path = CsvPath()
        path.parse(f"${PATH}[2-4][@me = count()]")
        lns = path.collect_line_numbers()
        print(f"test_csvpath_collect_line_numbers: lns: {lns}")
        assert lns == [2, 3, 4]

        path = CsvPath()
        path.parse(f"${PATH}[2*][@me = count()]")
        lns = path.collect_line_numbers()
        print(f"test_csvpath_collect_line_numbers: lns: {lns}")
        assert lns == ["2..."]

        path = CsvPath()
        path.parse(f"${PATH}[3-0][@me = count()]")
        lns = path.collect_line_numbers()
        print(f"test_csvpath_collect_line_numbers: lns: {lns}")
        assert lns == [0, 1, 2, 3]

        path = CsvPath()
        path.parse(f"${PATH}[3+0+5+1][@me = count()]")
        lns = path.collect_line_numbers()
        print(f"test_csvpath_collect_line_numbers: lns: {lns}")
        assert lns == [3, 0, 5, 1]

    def test_csvpath_ff(self):
        path = CsvPath()
        path.parse(f"${PATH}[*][@me = count()]")
        print("")

        assert path.advance_count == 0
        path.advance(1)
        assert path.advance_count == 1
        for _ in path.next():
            print(f"test_csvpath_ff: _: {_}")
            assert _[0] == "David"
            break

        i = 0
        for _ in path.next():
            if i == 0:
                print(f"test_csvpath_ff: _: {_}")
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
        path.parse(f"${PATH}[*][@me = count()]")
        i = 0
        for _ in path.next():
            path.advance(-1)
            assert path.advance_count == 8
            i += 1
        assert i == 1
