import unittest
from csvpath.csvpath import CsvPath
from csvpath.matching.util.expression_utility import ExpressionUtility
from tests.save import Save

PATH = "tests/test_resources/test.csv"
BOOL = "tests/test_resources/bool.csv"


class TestFunctionsQualifiers(unittest.TestCase):
    def test_qualifier_notnone(self):
        #
        # baseline
        #
        path = CsvPath()
        Save._save(path, "test_qualifier_notnone")
        path.parse(
            f"""${PATH}[*][
                    @t=none() ]"""
        )
        lines = path.collect()
        print(f"test_qualifier_notnone a: lines: {len(lines)}")
        print(f"test_qualifier_notnone a: path vars: {path.variables}\n")
        assert len(lines) == 9
        assert "t" in path.variables
        #
        # not None
        #
        path = CsvPath()
        Save._save(path, "test_qualifier_notnone")
        path.parse(
            f"""${PATH}[*][
                    @t.notnone=none() ]"""
        )
        lines = path.collect()
        print(f"test_qualifier_notnone b: lines: {len(lines)}")
        print(f"test_qualifier_notnone b: path vars: {path.variables}\n")
        assert len(lines) == 9
        assert "t" not in path.variables
        #
        # not none and not none
        #
        path = CsvPath()
        Save._save(path, "test_qualifier_notnone")
        path.parse(
            f"""${PATH}[*][
                    @t.notnone=yes() ]"""
        )
        lines = path.collect()
        print(f"test_qualifier_notnone c: lines: {len(lines)}")
        print(f"test_qualifier_notnone c: path vars: {path.variables}\n")
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
        assert path.variables["fish"][True] == 4

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
        assert path.variables["who"][True] == 3

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
