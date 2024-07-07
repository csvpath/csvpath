import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


class TestScanner(unittest.TestCase):
    def test_scan_all(self):
        path = CsvPath()
        scanner = path.parse(f"${PATH}[*]")
        print(f"{scanner}")
        # test properties
        assert scanner.from_line is None
        assert scanner.to_line is None
        assert scanner.all_lines
        assert len(scanner.these) == 0
        # test line numbers included
        for i in range(0, 8):
            assert path.includes(i)
        # test lines returned
        for i, ln in enumerate(path.next()):
            pass
        assert i == 8

    def test_scan_normal_from_to(self):
        path = CsvPath()
        scanner = path.parse(f"${PATH}[2-4]")
        # test properties
        print(f"{scanner}")
        assert scanner.from_line == 2
        assert scanner.to_line == 4
        assert not scanner.all_lines
        assert len(scanner.these) == 0
        # test line numbers included
        lns = []
        print(f"check from line: {scanner.from_line}")
        for ln in path.line_numbers():
            lns.append(ln)
        assert len(lns) == 3
        assert 2 in lns and 3 in lns and 4 in lns
        # test lines returned
        for i, ln in enumerate(path.next()):
            if i == 0:
                assert ln[0][0:4] == "Fish"
            elif i == 1:
                assert ln[0][0:4] == "Frog"
            elif i == 2:
                assert ln[0][0:3] == "Bug"
        assert i == 2

    def test_scan_from_line_to_end(self):
        path = CsvPath()
        scanner = path.parse(f"${PATH}[3*]")
        print(f"{scanner}")
        # test properties
        assert scanner.from_line == 3
        assert scanner.to_line is None
        assert scanner.all_lines
        assert len(scanner.these) == 0
        # test line numbers included
        lns = []
        print(f"check from line: {scanner.from_line}")
        for ln in path.line_numbers():
            lns.append(ln)
        assert len(lns) == 1
        assert lns[0] == "3..."
        # test lines returned
        for i, ln in enumerate(path.next()):
            print(f"   {i}...{ln}")
            if i == 0:
                assert ln[0][0:4] == "Frog"
            elif i == 1:
                assert ln[0][0:3] == "Bug"
            elif i == 2:
                assert ln[0][0:4] == "Bird"
            elif i == 3:
                assert ln[0][0:4] == "Ants"
            elif i == 4:
                assert ln[0][0:4] == "Slug"
        assert i == 5

    def test_scan_one_line(self):
        path = CsvPath()
        scanner = path.parse(f"${PATH}[3]")
        print(f"{scanner}")
        # test properties
        assert scanner.from_line is None
        assert scanner.to_line is None
        assert not scanner.all_lines
        assert len(scanner.these) == 1
        # test line numbers included
        lns = []
        print(f"check from line: {scanner.from_line}")
        for ln in path.line_numbers():
            lns.append(ln)
        assert len(lns) == 1
        # test lines returned
        for ln in path.next():
            assert ln[0][0:4] == "Frog"

    #
    # pytest -s -v -k test_line_plus_line
    #
    def test_scan_line_plus_line(self):
        path = CsvPath()
        scanner = path.parse(f"${PATH}[1+3]")
        print(f"{scanner}")
        assert scanner.from_line is None
        assert scanner.to_line is None
        assert not scanner.all_lines
        assert len(scanner.these) == 2
        # test line numbers included
        lns = []
        print(f"check from line: {scanner.from_line}")
        for ln in path.line_numbers():
            lns.append(ln)
        assert len(lns) == 2
        assert 1 in lns and 3 in lns
        # test lines returned
        for i, ln in enumerate(path.next()):
            if i == 0:
                assert ln[0][0:5] == "David"
            elif i == 1:
                assert ln[0][0:4] == "Frog"
        assert i == 1

    #
    # pytest -s -v -k test_multi_line_plus_line
    #
    def test_scan_multi_line_plus_line(self):
        path = CsvPath()
        scanner = path.parse(f"${PATH}[1+3+5]")
        print(f"{scanner}")
        assert scanner.from_line is None
        assert scanner.to_line is None
        assert not scanner.all_lines
        assert len(scanner.these) == 3
        # test line numbers included
        lns = []
        print(f"check from line: {scanner.from_line}")
        for ln in path.line_numbers():
            lns.append(ln)
        assert len(lns) == 3
        assert 1 in lns and 3 in lns and 5 in lns
        # test lines returned
        for i, ln in enumerate(path.next()):
            if i == 0:
                assert ln[0][0:5] == "David"
            elif i == 1:
                assert ln[0][0:4] == "Frog"
            elif i == 2:
                assert ln[0][0:4] == "Bird"
        assert i == 2

    def test_scan_to_from(self):
        path = CsvPath()
        scanner = path.parse(f"${PATH}[4-2]")
        # test properties
        print(f"{scanner}")
        assert scanner.from_line == 4
        assert scanner.to_line == 2
        assert not scanner.all_lines
        assert len(scanner.these) == 0
        # test line numbers included
        lns = []
        print(f"check from line: {scanner.from_line}")
        for ln in path.line_numbers():
            lns.append(ln)
        print(f" lines are {lns}")
        assert len(lns) == 3
        assert 2 in lns and 3 in lns and 4 in lns
        # test lines returned
        for i, ln in enumerate(path.next()):
            print(f"{i} = {ln}")
            if i == 0:
                assert ln[0][0:4] == "Fish"
            elif i == 1:
                assert ln[0][0:4] == "Frog"
            elif i == 2:
                assert ln[0][0:3] == "Bug"
        assert i == 2

    def test_scan_from_to_plus_from_to(self):
        path = CsvPath()
        scanner = path.parse(f"${PATH}[1-3+6-7]")
        # test properties
        print(f"{scanner}")
        assert scanner.from_line is None
        assert scanner.to_line is None
        assert not scanner.all_lines
        assert len(scanner.these) == 5
        # test line numbers included
        lns = []
        print(f"check from line: {scanner.from_line}")
        for ln in path.line_numbers():
            lns.append(ln)
        print(f" lines are: {lns}")
        assert len(lns) == 5
        assert 1 in lns and 2 in lns and 3 in lns and 6 in lns and 7 in lns
        # test lines returned
        for i, ln in enumerate(path.next()):
            print(f"{i} = {ln}")
            if i == 0:
                assert ln[0][0:4] == "Davi"
            elif i == 1:
                assert ln[0][0:4] == "Fish"
            elif i == 2:
                assert ln[0][0:4] == "Frog"
            elif i == 3:
                assert ln[0][0:4] == "Ants"
            elif i == 4:
                assert ln[0][0:4] == "Slug"
        assert i == 4
