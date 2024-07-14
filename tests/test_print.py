import unittest
from csvpath.matching.functions.printf import Print
from csvpath.matching.functions.yes import Yes
from csvpath.matching.matcher import Equality
from csvpath.matching.matcher import Term
from csvpath.matching.matcher import Matcher
from csvpath.csvpath import CsvPath


class TestPrint(unittest.TestCase):
    def test_print_variables(self):
        path = CsvPath()
        matcher = Matcher(csvpath=path, data="[no()]")
        path.set_variable("test", value="fish")
        string = "this is a print string with a $.variables.test variable"
        astr = Term(matcher, value=string, name="")
        p = Print(matcher, "print", astr)
        e = Equality(matcher)
        e.left = Yes(matcher, name="yes")
        e.right = p
        t = p.handle_variables(string)
        print(f"t: {t}")
        assert t.index("fish") > -1

    def test_print_variables2(self):
        path = CsvPath()
        matcher = Matcher(csvpath=path, data="[no()]")
        path.set_variable("test", value="fish")
        path.set_variable("blue", value="red")
        string = "this is a $.variables print string with a $.variables.test variable"
        astr = Term(matcher, value=string, name="")
        p = Print(matcher, "print", astr)
        e = Equality(matcher)
        e.left = Yes(matcher, name="yes")
        e.right = p
        t = p.handle_variables(string)
        print(f"at 1 t: {t}\n")
        t = p.handle_variables(t)
        print(f"at 2 t: {t}\n")
        i = t.find("blue")
        assert i > -1
        print(f"t: {t}")
        i = t.find("with a fish")
        assert i > -1

    def test_print_headers(self):
        path = CsvPath()
        headers = ["fish", "bat"]
        path.headers = headers
        line = ["xx", "yy"]
        path.line = line
        matcher = Matcher(csvpath=path, data="[no()]")
        matcher.headers = headers
        matcher.line = line
        string = "this is a $.headers print string with a $.headers.fish variable"
        astr = Term(matcher, value=string, name="")
        p = Print(matcher, "print", astr)
        e = Equality(matcher)
        e.left = Yes(matcher, name="yes")
        e.right = p
        t = p.handle_headers(string)
        print(f"at 1 t: {t}\n")
        t = p.handle_headers(t)
        print(f"at 2 t: {t}\n")
        i = t.find("xx")
        assert i > -1
        print(f"t: {t}")
        i = t.find("with a xx")
        assert i > -1
