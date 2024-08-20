import unittest
from csvpath.matching.matcher import Matcher
from csvpath.matching.productions.expression import Expression
from csvpath.matching.productions.equality import Equality
from csvpath.matching.productions.header import Header
from csvpath.matching.productions.term import Term
from csvpath.csvpath import CsvPath
from tests.save import Save


HEADERS = ["abc", "aheader", "crows", "d"]
LINE = ["fish", 10, "alert", "fum"]
PATH = "tests/test_resources/test.csv"
PATH3 = "tests/test_resources/test-3.csv"


class TestMatcher(unittest.TestCase):

    # ============= JUST MATCHER SYNTAX MOSTLY ================

    def test_match_equality1(self):
        matcher = Matcher(
            csvpath=None,
            data="""[
                                end() == 0 -> print("$.headers")
                                not( end() ==  0 ) -> no()
                          ] """,
            line=LINE,
            headers=HEADERS,
        )
        print(f"{matcher}")
        assert matcher.matches(syntax_only=True)

    def test_match_one_header(self):
        matcher = Matcher(
            csvpath=None, data='[#2=="alert"]', line=LINE, headers=HEADERS
        )
        print(f"{matcher}")
        assert len(matcher.expressions) == 1
        print(f"test_match_one_header: 0th: {matcher.expressions[0]}")
        assert isinstance(matcher.expressions[0][0], Expression)
        assert len(matcher.expressions[0][0].children) == 1
        assert isinstance(matcher.expressions[0][0].children[0], Equality)
        assert len(matcher.expressions[0][0].children[0].children) == 2
        assert isinstance(matcher.expressions[0][0].children[0].children[0], Header)
        assert isinstance(matcher.expressions[0][0].children[0].children[1], Term)
        assert matcher.expressions[0][0].children[0].matches()
        assert matcher.expressions[0][0].matches()
        assert matcher.matches(syntax_only=True)

    def test_match_equality_to_list(self):
        matcher = Matcher(
            csvpath=None,
            data='[first("alert", "test", "abc", "xyz")]',
            line=LINE,
            headers=HEADERS,
        )
        print(f"{matcher}")
        assert len(matcher.expressions) == 1
        assert isinstance(matcher.expressions[0][0], Expression)
        assert len(matcher.expressions[0][0].children) == 1
        print(f"children m.e[0].c         : {matcher.expressions[0][0].children}")
        print(
            f"children m.e[0].c[0].c    : {matcher.expressions[0][0].children[0].children}"
        )
        print(
            f"children m.e[0].c[0].c[0] : {matcher.expressions[0][0].children[0].children[0]}"
        )
        eq = matcher.expressions[0][0].children[0].children[0]
        ls = eq.commas_to_list()
        print(f"ls: {len(ls)}: {ls}")
        assert len(ls) == 4

        matcher = Matcher(
            csvpath=None,
            data='[first("alert", "test", "abc")]',
            line=LINE,
            headers=HEADERS,
        )
        print(f"{matcher}")
        eq = matcher.expressions[0][0].children[0].children[0]
        ls = eq.commas_to_list()
        print(f"ls: {len(ls)}: {ls}")
        assert len(ls) == 3

    def test_match_regex_function(self):
        matcher = Matcher(
            csvpath=None, data="[regex(#2 == /a.+ert/)]", line=LINE, headers=HEADERS
        )
        print(f"{matcher}")
        assert matcher.matches()

    def test_match_count_function(self):
        matcher = Matcher(csvpath=None, data="[count()==1]", line=LINE, headers=HEADERS)
        print(f"{matcher}")
        assert matcher.matches(syntax_only=True)

    def test_match_function_arg(self):
        matcher = Matcher(
            csvpath=CsvPath(), data="[count(#aheader==10)]", line=LINE, headers=HEADERS
        )
        print(f"{matcher}")
        assert matcher.matches(syntax_only=True)

    def test_match_nested_function_arg(self):
        matcher = Matcher(
            csvpath=None, data="[count(not(#aheader==10))]", line=LINE, headers=HEADERS
        )
        print(f"{matcher}")
        assert matcher.matches(syntax_only=True)

    def test_match_twice(self):
        matcher = Matcher(
            csvpath=None, data='[count()==1 #abc=="fish"]', line=LINE, headers=HEADERS
        )
        print(f"{matcher}")
        assert matcher.matches(syntax_only=True)

    def test_match_thrice(self):
        matcher = Matcher(
            csvpath=None,
            data='[count()==1 #abc=="fish" not(#crows=="tired")]',
            line=LINE,
            headers=HEADERS,
        )
        print(f"{matcher}")
        assert matcher.matches(syntax_only=True)

    # ============= SCAN AND MATCH ================

    def test_match_header_includes(self):
        path = CsvPath()
        path.parse(f'${PATH}[2-4][#0=="Frog"]')
        # test properties
        headers = path.headers
        print(f"test_match_header_includes: headers: {headers}")
        assert headers
        assert len(headers) == 3
        assert "lastname" in headers
        assert headers.index("lastname") == 1

    def test_match_a_header_match(self):
        path = CsvPath()
        scanner = path.parse(f'${PATH}[2-4][#0=="Frog"]')
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
        i = 0
        for i, ln in enumerate(path.next()):
            if i == 0:
                assert ln[0][0:4] == "Frog"
        assert i == 0

    def test_match_miss_because_header(self):
        path = CsvPath()
        Save._save(path, "test_match_miss_because_header")
        scanner = path.parse(f'${PATH}[2-4][#0=="Frog" #1=="Kermit"]')
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
            print(f"test_match_miss_because_header: {i}:{ln}")
            raise Exception("we should not have matched!")

    def test_match_two_headers_count(self):
        path = CsvPath()
        Save._save(path, "test_match_two_headers_count")
        scanner = path.parse(f'${PATH}[2-4][#0=="Frog" #lastname=="Bats" count()==2]')
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
        i = 0
        for i, ln in enumerate(path.next()):
            if i == 0:
                assert ln[2] == "growl"
        assert i == 0

    def test_match_two_headers_wrong_count(self):
        path = CsvPath()
        Save._save(path, "test_match_two_headers_wrong_count")
        scanner = path.parse(f'${PATH}[2-4][#0=="Frog" #lastname=="Bats" count()==3]')
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
        i = 0
        for i, ln in enumerate(path.next()):
            raise Exception("We should not get here!")

    def test_match_string_with_space(self):
        path = CsvPath()
        Save._save(path, "test_match_string_with_space")
        scanner = path.parse(f'${PATH}[*][#2=="sniffle sniffle..."]')
        # test properties
        print(f"{scanner}")
        # test lines returned
        lines = path.collect()
        assert len(lines) == 1

    def test_quoted_headers(self):
        path = CsvPath()
        Save._save(path, "test_quoted_headers")
        scanner = path.parse(
            f"""
            ${PATH3}[2-4][#0=="Frog" #"My lastname"=="Bats" count()==3]
        """
        )
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
        i = 0
        for i, ln in enumerate(path.next()):
            raise Exception("We should not get here!")