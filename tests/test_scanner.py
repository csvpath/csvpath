import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"
PATH2 = f"tests{os.sep}test_resources{os.sep}test-2-with_-and&.csv"


class TestScanner(unittest.TestCase):
    def test_scanner_scan_special_char_filename(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(f"${PATH2}[*][]")
        scanner = path.scanner
        # test properties
        assert scanner.from_line is None
        assert scanner.to_line is None
        assert scanner.all_lines
        assert len(scanner.these) == 0
        # test line numbers included
        for i in range(0, 8):
            assert scanner.includes(i)
        # test lines returned
        for i, ln in enumerate(path.next()):
            pass
        assert i == 8

    def test_scanner_scan_all(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(f"${PATH}[*][]")
        scanner = path.scanner
        # test properties
        assert scanner.from_line is None
        assert scanner.to_line is None
        assert scanner.all_lines
        assert len(scanner.these) == 0
        # test line numbers included
        for i in range(0, 8):
            assert scanner.includes(i)
        # test lines returned
        for i, ln in enumerate(path.next()):
            pass
        assert i == 8

    def test_scanner_scan_normal_from_to(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(f"${PATH}[2-4][]")
        scanner = path.scanner
        # test properties
        assert scanner.from_line == 2
        assert scanner.to_line == 4
        assert not scanner.all_lines
        assert len(scanner.these) == 0
        # test line numbers included
        lns = []
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

    def test_scanner_scan_from_line_to_end(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(f"${PATH}[3*][]")
        scanner = path.scanner
        # test properties
        assert scanner.from_line == 3
        assert scanner.to_line is None
        assert scanner.all_lines
        assert len(scanner.these) == 0
        # test line numbers included
        lns = []
        for ln in path.line_numbers():
            lns.append(ln)
        assert len(lns) == 1
        assert lns[0] == "3..."
        # test lines returned
        for i, ln in enumerate(path.next()):
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

    def test_scanner_scan_one_line(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(f"${PATH}[3][]")
        scanner = path.scanner
        # test properties
        assert scanner.from_line is None
        assert scanner.to_line is None
        assert not scanner.all_lines
        assert len(scanner.these) == 1
        # test line numbers included
        lns = []
        for ln in path.line_numbers():
            lns.append(ln)
        assert len(lns) == 1
        # test lines returned
        for ln in path.next():
            assert ln[0][0:4] == "Frog"

    #
    # pytest -s -v -k test_line_plus_line
    #
    def test_scanner_scan_line_plus_line(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(f"${PATH}[1+3][]")
        scanner = path.scanner
        assert scanner.from_line is None
        assert scanner.to_line is None
        assert not scanner.all_lines
        assert len(scanner.these) == 2
        # test line numbers included
        lns = []
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
    def test_scanner_scan_multi_line_plus_line(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(f"${PATH}[1+3+5][]")
        scanner = path.scanner
        assert scanner.from_line is None
        assert scanner.to_line is None
        assert not scanner.all_lines
        assert len(scanner.these) == 3
        # test line numbers included
        lns = []
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

    def test_scanner_scan_to_from(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(f"${PATH}[4-2][]")
        scanner = path.scanner
        # test properties
        assert scanner.from_line == 4
        assert scanner.to_line == 2
        assert not scanner.all_lines
        assert len(scanner.these) == 0
        # test line numbers included
        lns = []
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

    def test_scanner_scan_from_to_plus_from_to(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(f"${PATH}[1-3+6-7][]")
        scanner = path.scanner
        # test properties
        assert scanner.from_line is None
        assert scanner.to_line is None
        assert not scanner.all_lines
        assert len(scanner.these) == 5
        # test line numbers included
        lns = []
        for ln in path.line_numbers():
            lns.append(ln)
        assert len(lns) == 5
        assert 1 in lns and 2 in lns and 3 in lns and 6 in lns and 7 in lns
        # test lines returned
        for i, ln in enumerate(path.next()):
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

    def test_scanner_is_last(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(f"${PATH}[1-3+6-7][]")
        scanner = path.scanner
        path.line_monitor._physical_end_line_number = 14
        assert scanner.is_last(8, from_line=2, to_line=8, all_lines=False, these=[])
        assert not scanner.is_last(
            10, from_line=2, to_line=8, all_lines=False, these=[]
        )
        assert not scanner.is_last(1, from_line=2, to_line=8, all_lines=False, these=[])
        assert not scanner.is_last(5, from_line=2, to_line=8, all_lines=False, these=[])

        assert not scanner.is_last(
            5, from_line=None, to_line=None, all_lines=True, these=[]
        )
        assert scanner.is_last(
            14, from_line=None, to_line=None, all_lines=True, these=[]
        )
        assert scanner.is_last(
            14, from_line=None, to_line=None, all_lines=False, these=[14]
        )
        assert not scanner.is_last(
            13, from_line=None, to_line=None, all_lines=False, these=[14]
        )
        assert not scanner.is_last(
            15, from_line=None, to_line=None, all_lines=False, these=[14]
        )
        assert not scanner.is_last(
            15, from_line=None, to_line=None, all_lines=False, these=[14, 12]
        )
        assert scanner.is_last(100, from_line=4, to_line=100, all_lines=False, these=[])
        assert scanner.is_last(100, from_line=100, to_line=4, all_lines=False, these=[])
