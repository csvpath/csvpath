import unittest
from csvpath.csvpath import CsvPath
from csvpath.matching.matcher import Matcher
from csvpath.matching.productions import Variable
from csvpath.matching.functions.lines.stop import Stop
from csvpath.matching.util.expression_utility import ExpressionUtility
from tests.save import Save

PATH = "tests/test_resources/test.csv"
BOOL = "tests/test_resources/bool.csv"


class TestFunctionsQualifiers(unittest.TestCase):
    def test_qualifier_has_known_qualifiers(self):
        # on the name
        var = Variable(None, name="a.b.asbool", value="v")
        assert var.has_known_qualifiers()
        # set property
        var = Variable(None, name="a", value="v")
        var.onmatch = True
        assert var.has_known_qualifiers()
        # as tracking value (or unknown name for other prods)
        var = Variable(None, name="a.me", value="v")
        assert not var.has_known_qualifiers()
        # no quals
        var = Variable(None, name="a", value="v")
        assert not var.has_known_qualifiers()

    def test_qualifier_notnone1(self):
        #
        # baseline
        #
        path = CsvPath()
        Save._save(path, "test_qualifier_notnone1")
        path.parse(
            f"""${PATH}[*][
                    ~ this should set and match ~
                    @t=none() ]"""
        )
        lines = path.collect()
        print(f"test_qualifier_notnone1 a: lines: {len(lines)}")
        print(f"test_qualifier_notnone1 a: path vars: {path.variables}\n")
        assert len(lines) == 9
        assert "t" in path.variables

    def test_qualifier_notnone2(self):
        #
        # not None
        #
        path = CsvPath()
        Save._save(path, "test_qualifier_notnone2")
        path.parse(
            f"""${PATH}[*][
                    ~ this should not set and not match ~
                    @t.notnone=none() ]"""
        )
        lines = path.collect()
        print(f"test_qualifier_notnone2 b: lines: {len(lines)}")
        print(f"test_qualifier_notnone2 b: path vars: {path.variables}\n")
        assert len(lines) == 0
        assert "t" not in path.variables

    def test_qualifier_notnone3(self):
        #
        # not none and not none
        #
        path = CsvPath()
        Save._save(path, "test_qualifier_notnone3")
        path.parse(
            f"""${PATH}[*][
                    ~ this should set ~
                    @t.notnone=yes() ]"""
        )
        lines = path.collect()
        print(f"test_qualifier_notnone3 c: lines: {len(lines)}")
        print(f"test_qualifier_notnone3 c: path vars: {path.variables}\n")
        assert len(lines) == 9
        assert "t" in path.variables
        assert path.variables["t"] is True

    def test_qualifier_notnone4(self):
        #
        # not none and nocontrib
        #
        path = CsvPath()
        Save._save(path, "test_qualifier_notnone4")
        path.parse(
            f"""${PATH}[*][
                    ~ this should match and not set ~
                    @t.notnone.nocontrib=yes() ]"""
        )
        lines = path.collect()
        print(f"test_qualifier_notnone4 c: lines: {len(lines)}")
        print(f"test_qualifier_notnone4 c: path vars: {path.variables}\n")
        assert len(lines) == 9
        assert "t" in path.variables
        assert path.variables["t"] is True

    def test_qualifier(self):
        path = CsvPath()
        Save._save(path, "test_function_qualifier")
        path.parse(
            f"""${PATH}
                        [*]
                        [
                            @t.onmatch=count.firstname_match(#firstname=="Ants")
                            #firstname=="Ants"
                        ]
                   """
        )
        lines = path.collect()
        print(f"test_function_qualifier: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_qualifier: line: {line}")
        print(f"test_function_qualifier: path vars: {path.variables}")
        assert len(lines) == 1
        assert "firstname_match" in path.variables
        assert path.variables["firstname_match"][True] == 1

    def test_exp_util_quals(self):
        name, quals = ExpressionUtility.get_name_and_qualifiers("test.onmatch")
        assert name == "test"
        assert "onmatch" in quals
        name, quals = ExpressionUtility.get_name_and_qualifiers("test.onchange.onmatch")
        assert name == "test"
        assert "onmatch" in quals
        assert "onchange" in quals
        name, quals = ExpressionUtility.get_name_and_qualifiers(
            "test.mytest.onchange.onmatch"
        )
        assert name == "test"
        assert "mytest" in quals
        assert "onmatch" in quals
        assert "onchange" in quals

    def test_latch(self):
        path = CsvPath()
        Save._save(path, "test_latch")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                @my_firstname.latch = #firstname
                @other_firstname = #firstname
            ]"""
        )
        path.fast_forward()
        print(f"test_latch: path vars: {path.variables}")
        assert path.variables["my_firstname"] == "David"
        assert path.variables["other_firstname"] == "Frog"

    def test_function_every_qualifier1(self):
        path = CsvPath()
        Save._save(path, "test_function_every_qualifier1")
        path.parse(
            f"""${PATH}
                        [*]
                        [
                            @t.onmatch=count()
                            every.fish(#lastname=="Bat", 2)
                            #lastname=="Bat"
                        ]
                   """
        )
        #
        # we capture 1 #lastname!="Bat" because there are 2 such lines
        # and we capture 3 #lastname=="Bat" because there are 7 such lines
        #
        lines = path.collect()
        print(f"test_function_every_qualifier: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_every_qualifier1: line: {line}")
        print(f"test_function_every_qualifier1: path vars: {path.variables}")
        assert len(lines) == 3
        assert path.variables["t"] == 3
        assert "fish" in path.variables
        assert path.variables["fish"][True] == 7

    def test_every_qualifier2(self):
        path = CsvPath()
        Save._save(path, "test_every_qualifier2")
        path.parse(
            f"""${PATH}
                        [*]
                        [
                            @t.onmatch=count()
                            every.who(#lastname, 2)
                        ]
                   """
        )
        #
        # we capture 3 #lastnames because there are 3 total in 9
        # and we match on 3 #lastnames because there are 7 "Bat"
        #
        lines = path.collect()
        print(f"test_function_every_qualifier2: lines: {len(lines)}")
        for line in lines:
            print(f"test_every_qualifier2: line: {line}")
        print(f"test_every_qualifier2: path vars: {path.variables}")
        assert len(lines) == 3
        assert path.variables["t"] == 3
        assert "who" in path.variables
        assert path.variables["who"]["Bat"] == 7

    def test_qualifier_first_and_second_non_term(self):
        path = CsvPath()
        Save._save(path, "test_qualifier_header")
        path.parse(
            f"""${BOOL}
                [*]
                [
                    count.fred.sally()
                ]
                """
        )
        path.fast_forward()
        es = path.matcher.expressions
        assert len(es) == 1
        e = es[0][0]
        print(f"\n test_qualifier_first_and_second_non_term: e: {e}")
        count = e.children[0]
        print(f"test_qualifier_first_and_second_non_term: count: {count}")
        assert count.name == "count"
        first = count.first_non_term_qualifier()
        assert first == "fred"
        second = count.second_non_term_qualifier()
        assert second == "sally"

    def test_qualifier_header(self):
        path = CsvPath()
        Save._save(path, "test_qualifier_header")
        path.parse(
            f"""${BOOL}
                [*]
                [
                    or( count_lines() == 2, count_lines.nocontrib() == 5)
                    count_lines.nocontrib() == 2 -> @a = #error.asbool
                    count_lines.nocontrib() == 5 -> @b = #error
                ]
                """
        )
        lines = path.collect()
        print(f"test_qualifier_header: lines: {len(lines)}")
        print(f"test_qualifier_header: path vars: {path.variables}")
        assert len(lines) == 2
        assert "a" in path.variables
        assert "b" in path.variables
        assert path.variables["a"] is True
        assert path.variables["b"] == "true"

    def test_qualified_properties(self):
        path = CsvPath()
        matcher = Matcher(csvpath=path, data="[]")
        stop = Stop(matcher, name="stop")
        assert not stop.asbool
        stop.asbool = True
        assert stop.asbool

        assert not stop.onmatch
        stop.onmatch = True
        assert stop.onmatch

        assert not stop.onchange
        stop.onchange = True
        assert stop.onchange

        assert not stop.latch
        stop.latch = True
        assert stop.latch

        assert not stop.nocontrib
        stop.nocontrib = True
        assert stop.nocontrib

        assert not stop.notnone
        stop.notnone = True
        assert stop.notnone

        assert not stop.once
        stop.once = True
        assert stop.once
