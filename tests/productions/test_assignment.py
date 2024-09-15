import unittest
from csvpath.csvpath import CsvPath
from csvpath.matching.productions.equality import Equality
from csvpath.matching.matcher import Matcher
from tests.save import Save

PATH = "tests/test_resources/test.csv"
BOOL = "tests/test_resources/bool.csv"
NUMBERS = "tests/test_resources/numbers.csv"


class TestAssignment(unittest.TestCase):
    def test_qualifier_increment1(self):
        path = CsvPath()
        Save._save(path, "test_qualifier_increment1")
        path.parse(
            f"""${NUMBERS}[1-3][
                    ~ should work ~
                    @up.increase = #1
                ]"""
        )
        lines = path.collect()
        print(f"\n test_qualifier_increment1: lines: {lines}")
        print(f"test_qualifier_increment1: vars: {path.variables}")
        assert lines
        assert len(lines) == 3

    def test_qualifier_increment2(self):
        path = CsvPath()
        Save._save(path, "test_qualifier_increment2")
        path.parse(
            f"""${NUMBERS}[1-3][
                    ~ should not decrease @up ~
                    @up.increase = #2
                ]"""
        )
        lines = path.collect()
        print(f"test_qualifier_increment2: vars: {path.variables}")
        print(f"\n test_qualifier_increment2: lines: {lines}")
        assert lines
        assert len(lines) == 1

    def test_qualifier_decrement1(self):
        path = CsvPath()
        Save._save(path, "test_qualifier_decrement1")
        path.parse(
            f"""${NUMBERS}[1-3][
                    ~ should work ~
                    @down.decrease = #2
                ]"""
        )
        lines = path.collect()
        print(f"\n test_qualifier_decrement1: lines: {lines}")
        print(f"test_qualifier_decrement1: vars: {path.variables}")
        assert lines
        assert len(lines) == 3

    def test_qualifier_decrement2(self):
        path = CsvPath()
        Save._save(path, "test_qualifier_decrement2")
        path.parse(
            f"""${NUMBERS}[1-3][
                    ~ should not increase @up ~
                    @down.decrease = #1
                ]"""
        )
        lines = path.collect()
        print(f"test_qualifier_decrement2: vars: {path.variables}")
        print(f"\n test_qualifier_decrement2: lines: {lines}")
        assert lines
        assert len(lines) == 1

    def test_qualifier_assignment(self):
        path = CsvPath()
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
        print(f"test_assignment: mk8: path vars: {path.variables}")
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
