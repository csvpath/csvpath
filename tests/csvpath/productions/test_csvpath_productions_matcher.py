import os
import unittest
from csvpath.matching.matcher import Matcher
from csvpath.matching.productions.expression import Expression
from csvpath.matching.productions.equality import Equality
from csvpath.matching.productions.header import Header
from csvpath.matching.productions.term import Term
from csvpath import CsvPath


HEADERS = ["abc", "aheader", "crows", "d"]
LINE = ["fish", 10, "alert", "fum"]
PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
PATH3 = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test-3.csv"


class TestCsvPathProductionsMatcher(unittest.TestCase):
    """
    #
    # this test is no longer workable. updating it doesn't seem worthwhile atm.
    #
    def test_match_one_header(self):
        matcher = Matcher(
            csvpath=None, data='[#2=="alert"]', line=LINE, headers=HEADERS
        )
        assert len(matcher.expressions) == 1
        assert isinstance(matcher.expressions[0][0], Expression)
        assert len(matcher.expressions[0][0].children) == 1
        assert isinstance(matcher.expressions[0][0].children[0], Equality)
        assert len(matcher.expressions[0][0].children[0].children) == 2
        assert isinstance(matcher.expressions[0][0].children[0].children[0], Header)
        assert isinstance(matcher.expressions[0][0].children[0].children[1], Term)
        assert matcher.expressions[0][0].children[0].matches()
        assert matcher.expressions[0][0].matches()
    """

    # ============= SCAN AND MATCH ================

    def test_matcher_siblings(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(f"${PATH}[2-4][add(1,2,3,4,5)]")
        path.fast_forward()
        assert path.matcher
        sibs = path.matcher.expressions[0][0].children[0].siblings()
        assert sibs
        assert len(sibs) == 5

    def test_match_header_includes(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(f'${PATH}[2-4][#0=="Frog"]')
        # test properties
        headers = path.headers
        assert headers
        assert len(headers) == 3
        assert "lastname" in headers
        assert headers.index("lastname") == 1

    def test_match_a_header_match(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        scanner = path.parse(f'${PATH}[2-4][#0=="Frog"]')
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
        i = 0
        for i, ln in enumerate(path.next()):
            if i == 0:
                assert ln[0][0:4] == "Frog"
        assert i == 0

    def test_match_miss_because_header(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        scanner = path.parse(f'${PATH}[2-4][#0=="Frog" #1=="Kermit"]')
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
            raise Exception("we should not have matched!")

    def test_match_two_headers_count(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        scanner = path.parse(f'${PATH}[2-4][#0=="Frog" #lastname=="Bats" count()==2]')
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
        i = 0
        for i, ln in enumerate(path.next()):
            if i == 0:
                assert ln[2] == "growl"
        assert i == 0

    def test_match_two_headers_wrong_count(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        scanner = path.parse(f'${PATH}[2-4][#0=="Frog" #lastname=="Bats" count()==3]')
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
        i = 0
        for i, ln in enumerate(path.next()):
            raise Exception("We should not get here!")

    def test_match_string_with_space(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(f'${PATH}[*][#2=="sniffle sniffle..."]')
        lines = path.collect()
        assert len(lines) == 1

    def test_quoted_headers(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        scanner = path.parse(
            f"""
            ${PATH3}[2-4][#0=="Frog" #"My lastname"=="Bats" count()==3]
        """
        )
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
        i = 0
        for i, ln in enumerate(path.next()):
            raise Exception("We should not get here!")
