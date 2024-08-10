import unittest
from csvpath.csvpath import CsvPath
from csvpath.scanning.scanner import Scanner

PATH = "tests/test_resources/test.csv"


class TestCsvPath(unittest.TestCase):
    def test_includes(self):
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

    def test_line_numbers(self):
        csvpath = CsvPath()
        assert [1, 2, 3] == csvpath._collect_line_numbers(these=[1, 2, 3])
        assert [1, 2, 3] == csvpath._collect_line_numbers(from_line=1, to_line=3)
        assert ["3..."] == csvpath._collect_line_numbers(from_line=3, all_lines=True)
        assert [3] == csvpath._collect_line_numbers(from_line=3)
        assert ["0..3"] == csvpath._collect_line_numbers(to_line=3)

    def test_variables(self):
        path = CsvPath()
        scanner = path.parse(f"${PATH}[2-4][@me = count()]")
        print(f"{scanner}")
        for i, ln in enumerate(path.next()):
            assert path.get_variable("me") == i + 1
            print(f'...{i} = {path.get_variable("me")}')

    def test_header_counting(self):
        path = CsvPath()
        path.parse(f"${PATH}[2-4][@me = count()]")
        assert path.header_index("lastname") == 1

    def test_collect_line_numbers(self):
        path = CsvPath()
        path.parse(f"${PATH}[2-4][@me = count()]")
        lns = path.collect_line_numbers()
        print(f"test_collect_line_numbers: lns: {lns}")
        assert lns == [2, 3, 4]

        path = CsvPath()
        path.parse(f"${PATH}[2*][@me = count()]")
        lns = path.collect_line_numbers()
        print(f"test_collect_line_numbers: lns: {lns}")
        assert lns == ["2..."]

        path = CsvPath()
        path.parse(f"${PATH}[3-0][@me = count()]")
        lns = path.collect_line_numbers()
        print(f"test_collect_line_numbers: lns: {lns}")
        assert lns == [0, 1, 2, 3]

        path = CsvPath()
        path.parse(f"${PATH}[3+0+5+1][@me = count()]")
        lns = path.collect_line_numbers()
        print(f"test_collect_line_numbers: lns: {lns}")
        assert lns == [3, 0, 5, 1]

    def test_ff(self):
        path = CsvPath()
        path.parse(f"${PATH}[*][@me = count()]")
        print("")

        assert path._advance == 0
        path.advance(1)
        assert path._advance == 1
        for _ in path.next():
            print(f"test_ff: _: {_}")
            assert _[0] == "David"
            break

        i = 0
        for _ in path.next():
            if i == 0:
                print(f"test_ff: _: {_}")
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
            assert path._advance == 8

        path = CsvPath()
        path.parse(f"${PATH}[*][@me = count()]")
        i = 0
        for _ in path.next():
            path.advance(-1)
            assert path._advance == 8
            i += 1
        assert i == 1
