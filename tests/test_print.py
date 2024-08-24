import unittest
from csvpath.matching.functions.printf import Print
from csvpath.matching.functions.yes import Yes
from csvpath.matching.matcher import Equality
from csvpath.matching.matcher import Term
from csvpath.matching.matcher import Matcher
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestPrint(unittest.TestCase):
    def test_print_plus_function(self):
        pathstr = f"""${PATH}[*]
            [
              @h = #0
              yes() -> print( "$.headers.level $.headers.message", advance(6) )
            ] """

        path = CsvPath()
        Save._save(path, "test_print_plus_function")
        path.parse(pathstr)
        lines = path.collect()
        print(f"test_print_plus_function: path.vars: {path.variables}")
        assert path.is_valid
        assert len(lines) == 2

    def test_print_variables(self):
        path = CsvPath()
        matcher = Matcher(csvpath=path, data="[no()]")
        path.set_variable("test", value="fish")
        string = "this is a print string with a $.variables.test variable"
        astr = Term(matcher, value=string, name=None)
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
        astr = Term(matcher, value=string, name=None)
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

    def test_print_variables3(self):
        path = CsvPath()
        matcher = Matcher(csvpath=path, data="[no()]")
        path.set_variable("col", value="1115")
        path.set_variable("cntln", value="3338")
        path.set_variable("cnt", value="0015")
        path.set_variable("t", value="True")
        string = "$.variables.col, $.variables.t, $.variables.cntln, $.variables.cnt"
        astr = Term(matcher, value=string, name=None)
        p = Print(matcher, "print", astr)
        e = Equality(matcher)
        e.left = Yes(matcher, name="yes")
        e.right = p
        t = p.handle_variables(string)
        print(f"at 1 string is: {t}\n")
        t = p.handle_variables(t)
        print(f"at 2 string is: {t}\n")
        t = p.handle_variables(t)
        print(f"at 3 string is: {t}\n")
        t = p.handle_variables(t)
        print(f"at 4 string is: {t}\n")
        i = t.find("1115")
        assert i > -1
        print(f"t: {t}")
        i = t.find("3338")
        assert i > -1
        i = t.find("0015")
        assert i > -1
        i = t.find("True")
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
        astr = Term(matcher, value=string, name=None)
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

    # this test only checks that the NAME_LINE token is handled correctly
    # print(  @h=="WARN", "$.headers.level, $.headers.message" )

    def test_print_plus_header(self):
        pathstr = f"""${PATH}[1-100]
            [
              @h = #level
              @h == "WARN" -> print( "$.headers.level $.headers.message" )
            ] """

        path = CsvPath()
        Save._save(path, "test_print_plus_header")
        path.parse(pathstr)
        path.collect()

    def test_function_jinja(self):
        path = CsvPath()
        Save._save(path, "test_function_jinja")
        out = "tests/test_resources/out.txt"
        inf = "tests/test_resources/in.txt"
        path.parse(
            f""" ${PATH}[*][ yes()
                             last.nocontrib() -> jinja("{inf}", "{out}")
            ]
            """
        )
        print("")
        path.fast_forward()
        print(f"test_function_jinja: path vars: {path.variables}")
        with open(out, "r") as file:
            txt = file.read()
            i = txt.find("scan count: 9")
            assert i >= 0
