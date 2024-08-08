import unittest
from csvpath.csvpath import CsvPath
from csvpath.matching.matcher import Matcher

PATH = "tests/test_resources/test.csv"


class TestFunctionsLast(unittest.TestCase):
    def test_function_last1(self):
        path = CsvPath()
        matchpart = """
            [
                count_lines()==0 -> @first = 0
                last() -> @last = count_lines()
            ]"""

        matcher = Matcher(
            csvpath=path,
            data=matchpart,
            line=["Frog", "Bats", "ribbit..."],
            headers=["firstname", "lastname", "say"],
        )
        print("")
        count_lines = matcher.expressions[0][0].children[0].left.left.matches(skip=[])
        assert count_lines is True
        lines = matcher.expressions[0][0].children[0].left.left.to_value(skip=[])
        assert lines == 0
        is0 = matcher.expressions[0][0].children[0].left.matches(skip=[])
        assert is0 is True
        op = matcher.expressions[0][0].children[0].op
        assert op == "->"
        b1 = matcher.expressions[0][0].matches(skip=[])
        b2 = matcher.expressions[1][0].matches(skip=[])
        print("")
        print(f"test_function_last1: path vars: {path.variables}")
        print(f"test_function_last1: b1: {b1}, b2: {b2}")
        assert path.variables["first"] == 0
        assert b1 is True
        assert b2 is False

    def test_function_last2(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [
                count_lines()==0 -> @first = 0
                last() -> @last = count_lines()
            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_last: path vars: {path.variables}")
        print(f"test_function_last: lines: {lines}")
        assert path.variables["last"] == 8
        assert path.variables["first"] == 0

    # FIXME: this is not really a deterministic test.
    def test_function_last3(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [ yes() -> print("$.line_count")
                last() -> print("the last row is $.line_count")
            ]
            """
        )
        print("")
        path.fast_forward()
        print(f"test_function_last: path vars: {path.variables}")

    def test_function_access_tracking(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*]
                            [
                                tally(#lastname) no()
                                @hmmm = @lastname.Bat
                                @ohhh = @hmmm.fish
                                last() -> @lastname.Bat = "fred"
                            ]
                   """
        )
        path.collect()
        print(f"test_function_access_tracking: path vars: {path.variables}")
        assert path.variables["lastname"]["Bat"] == "fred"
        assert path.variables["hmmm"] == 7
        assert path.variables["ohhh"] is None
