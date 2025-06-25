import os
import unittest
import pytest
from lark.exceptions import UnexpectedCharacters
from csvpath.csvpath import CsvPath
from csvpath.matching.productions.equality import Equality
from csvpath.matching.matcher import Matcher

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
BOOL = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}bool.csv"
NUMBERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers.csv"


class TestCsvPathProductionsAssignment(unittest.TestCase):
    def test_equal_rhs_1(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""${PATH}[*][
                @a == none() -> @a = 1
                ~ @c = 1 == 0 will throw an exception so we have to use the equals function ~
                @b = eq(1,0)
            ]"""
        ).fast_forward()
        v = path.variables
        print(f"vars: {v}")
        assert v["a"] == 1
        assert v["b"] is False

    def test_equal_rhs_2(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""${PATH}[*][
                @a == none() -> @a = 1
                ~ the current version of the Lark parser grammar does not allow for
                  the == operator to be used as the right-hand-side of an assignment.
                  the constraint isn't ideal, but equals() is an easy work-around, so
                  for now we're accepting it.
                ~
                @c = 1==0
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(UnexpectedCharacters):
            path.fast_forward()

    def test_qualifier_increment0(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.collect(
            f"""
            ${PATH}[*][
                @a.increase = line_number()
                @b = line_number()
                push("as", @a)
                push("bs", @b)
            ]"""
        )
        print(f"vars: {path.variables}")
        print(f"as: {path.variables['as']}")
        print(f"bs: {path.variables['bs']}")
        assert path.variables["as"] == path.variables["bs"]

    def test_qualifier_increment1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""${NUMBERS}[1-3][
                    ~ should work ~
                    @up.increase = int(#1)
                ]"""
        )
        lines = path.collect()
        assert lines
        assert len(lines) == 3

    def test_qualifier_increment2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""${NUMBERS}[1-3][
                    ~ should not decrease @up ~
                    @up.increase = int(#2)
                ]"""
        )
        lines = path.collect()
        assert lines
        assert len(lines) == 1

    def test_qualifier_decrement1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""${NUMBERS}[1-3][
                    ~ should work ~
                    @down.decrease = int(#2)
                ]"""
        )
        lines = path.collect()
        assert lines
        assert len(lines) == 3

    def test_qualifier_decrement2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""${NUMBERS}[1-3][
                    ~ should not increase @up ~
                    @down.decrease = int(#1)
                ]"""
        )
        lines = path.collect()
        assert lines
        assert len(lines) == 1

    def test_qualifier_decrement3(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""${NUMBERS}[0-2][
                    @b.decrease = line_number()
                    @a = line_number()
                    push("as", @a)
                    push("bs", @b)
                ]"""
        )
        path.collect()
        print(f"as: {path.variables['as']}")
        print(f"bs: {path.variables['bs']}")
        assert path.variables["bs"] == [0, 0, 0]

    def test_qualifier_assignment(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        matcher = Matcher(csvpath=path, data="[yes()]")
        eq = Equality(matcher=matcher)
        eq.matcher = matcher
        name = "a"
        tracking = None
        args = {
            "onchange": False,
            "latch": False,
            "onmatch": False,
            "asbool": False,
            "nocontrib": False,
            "notnone": False,
            "increase": False,
            "decrease": False,
            "noqualifiers": True,
            "count": False,
            "current_value": "x",
            "new_value": "y",
            "line_matches": False,
        }
        #### TEST MARKER 1
        ret = eq._do_assignment_new_impl(name=name, tracking=tracking, args=args)
        assert ret is True
        assert matcher.get_variable(name, tracking=tracking) == args["new_value"]

        #### TEST MARKER 2
        args["noqualifiers"] = False
        args["latch"] = True
        args["new_value"] = "z"  # NOT == "y"
        ret = eq._do_assignment_new_impl(name=name, tracking=tracking, args=args)
        assert ret is True
        assert matcher.get_variable(name, tracking=tracking) == "y"

        #### TEST MARKER 3
        del path.variables[name]
        args["current_value"] = None
        ret = eq._do_assignment_new_impl(name=name, tracking=tracking, args=args)
        assert ret is True
        assert matcher.get_variable(name, tracking=tracking) == "z"

        #### TEST MARKER 4
        del path.variables[name]
        args["latch"] = False
        args["onchange"] = True
        args["current_value"] = "x"
        args["new_value"] = "y"
        ret = eq._do_assignment_new_impl(name=name, tracking=tracking, args=args)
        assert ret is True
        assert matcher.get_variable(name, tracking=tracking) == "y"

        #### TEST MARKER 5
        del path.variables[name]
        args["latch"] = False
        args["onchange"] = True
        args["current_value"] = "x"
        args["new_value"] = "x"
        ret = eq._do_assignment_new_impl(name=name, tracking=tracking, args=args)
        assert ret is False
        assert matcher.get_variable(name, tracking=tracking) is None

        #### TEST MARKER 6
        args["latch"] = True
        args["onchange"] = False
        args["current_value"] = "x"
        args["new_value"] = "x"
        ret = eq._do_assignment_new_impl(name=name, tracking=tracking, args=args)
        assert ret is True
        assert matcher.get_variable(name, tracking=tracking) is None

        #### TEST MARKER 7a
        args["onmatch"] = True
        args["latch"] = True
        args["onchange"] = False
        args["current_value"] = "x"
        args["new_value"] = "y"
        ret = eq._do_assignment_new_impl(name=name, tracking=tracking, args=args)
        assert ret is False
        assert matcher.get_variable(name, tracking=tracking) is None

        #### TEST MARKER 7b
        args["onmatch"] = True
        args["latch"] = True
        args["onchange"] = False
        args["current_value"] = "x"
        args["new_value"] = "y"
        args["line_matches"] = True
        ret = eq._do_assignment_new_impl(name=name, tracking=tracking, args=args)
        assert ret is True
        assert matcher.get_variable(name, tracking=tracking) is None

        #### TEST MARKER 8
        args["onmatch"] = True
        args["latch"] = True
        args["onchange"] = False
        args["current_value"] = None
        args["new_value"] = "y"
        args["line_matches"] = True
        ret = eq._do_assignment_new_impl(name=name, tracking=tracking, args=args)
        assert ret is True
        # assert (name, args["new_value"], tracking) in matcher.if_all_match
        # assert matcher.get_variable(name, tracking=tracking) is None
        assert name in path.variables
        assert path.variables[name] == "y"
        path.variables = {}

        #### TEST MARKER 9
        args["onmatch"] = True
        args["latch"] = False
        args["onchange"] = True
        args["current_value"] = None
        args["new_value"] = "y"
        ret = eq._do_assignment_new_impl(name=name, tracking=tracking, args=args)
        assert ret is True
        # assert (name, args["new_value"], tracking) in matcher.if_all_match
        # assert matcher.get_variable(name, tracking=tracking) is None
        assert name in path.variables
        assert path.variables[name] == "y"
        path.variables = {}

        #### TEST MARKER 10
        args["onmatch"] = True
        args["latch"] = True
        args["onchange"] = True
        args["current_value"] = None
        args["new_value"] = "y"
        ret = eq._do_assignment_new_impl(name=name, tracking=tracking, args=args)
        assert ret is True
        # assert (name, args["new_value"], tracking) in matcher.if_all_match
        # assert matcher.get_variable(name, tracking=tracking) is None
        assert name in path.variables
        assert path.variables[name] == "y"
        path.variables = {}

        #### TEST MARKER 11
        matcher.if_all_match = []
        args["onmatch"] = True
        args["latch"] = False
        args["onchange"] = True
        args["current_value"] = "y"
        args["new_value"] = "y"
        args["line_matches"] = True
        ret = eq._do_assignment_new_impl(name=name, tracking=tracking, args=args)
        assert ret is False
        assert matcher.get_variable(name, tracking=tracking) is None

        #### TEST MARKER 12
        matcher.if_all_match = []
        args["onmatch"] = True
        args["latch"] = True
        args["onchange"] = False
        args["current_value"] = "y"
        args["new_value"] = "y"
        args["line_matches"] = True
        ret = eq._do_assignment_new_impl(name=name, tracking=tracking, args=args)
        assert ret is True
        assert matcher.get_variable(name, tracking=tracking) is None

        #### TEST MARKER 13
        args["onmatch"] = True
        args["latch"] = False
        args["onchange"] = False
        args["current_value"] = "y"
        args["new_value"] = "y"
        args["line_matches"] = True
        ret = eq._do_assignment_new_impl(name=name, tracking=tracking, args=args)
        assert ret is True
        # assert (name, args["new_value"], tracking) in matcher.if_all_match
        # assert matcher.get_variable(name, tracking=tracking) is None
        assert name in path.variables
        assert path.variables[name] == "y"
        path.variables = {}

        #### TEST MARKER 14
        matcher.if_all_match = []
        args["onmatch"] = True
        args["latch"] = False
        args["onchange"] = False
        args["current_value"] = "y"
        args["new_value"] = "y"
        args["line_matches"] = False
        ret = eq._do_assignment_new_impl(name=name, tracking=tracking, args=args)
        assert ret is False
        assert matcher.get_variable(name, tracking=tracking) is None
        assert (name, args["new_value"], tracking) not in matcher.if_all_match

        #### TEST MARKER 15
        matcher.if_all_match = []
        args["onmatch"] = False
        args["latch"] = False
        args["onchange"] = False
        args["current_value"] = "y"
        args["new_value"] = "z"
        args["line_matches"] = False
        ret = eq._do_assignment_new_impl(name=name, tracking=tracking, args=args)
        assert ret is True
        assert matcher.get_variable(name, tracking=tracking) == "z"

        #### TEST MARKER 16
        matcher.if_all_match = []
        args["onmatch"] = True
        args["latch"] = True
        args["onchange"] = False
        args["asbool"] = True
        args["current_value"] = "y"
        args["new_value"] = "false"
        args["line_matches"] = True
        ret = eq._do_assignment_new_impl(name=name, tracking=tracking, args=args)
        assert ret is False  # "false" is a bool so False

        #### TEST MARKER 17
        matcher.if_all_match = []
        args["onmatch"] = True
        args["latch"] = True
        args["onchange"] = False
        args["asbool"] = True
        args["current_value"] = "y"
        args["new_value"] = "true"
        args["line_matches"] = True
        ret = eq._do_assignment_new_impl(name=name, tracking=tracking, args=args)
        assert ret is True  # "true" is a bool so True

        #### TEST MARKER 18
        matcher.if_all_match = []
        args["onmatch"] = True
        args["latch"] = True
        args["onchange"] = False
        args["asbool"] = True
        args["nocontrib"] = True
        args["current_value"] = "y"
        args["new_value"] = "false"
        args["line_matches"] = True
        ret = eq._do_assignment_new_impl(name=name, tracking=tracking, args=args)
        assert ret is True  # "false" is a bool so False, but nocontrib
