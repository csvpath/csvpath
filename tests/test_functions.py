import unittest
from csvpath.matching.matcher import Matcher
from csvpath.matching.functions.count import Count
from csvpath.matching.functions.function_factory import FunctionFactory
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"

class TestFunctions(unittest.TestCase):

#============= count ================

    def test_function_factory(self):
        count = FunctionFactory.get_function(None, name="count", child=None)
        assert count

    def test_function_count_empty(self):
        f = FunctionFactory.get_function(None, name="count", child=None)
        assert f.to_value() == 0 # no matcher or csvpath == -1 + eager match 1

    def test_function_count_equality(self):
        path = CsvPath()
        scanner = path.parse(f'${PATH}[*][count(#lastname="Bat")=7]')
        lines = path.collect()
        print(f"test_function_count_equality: lines: {lines}")
        assert len(lines) == 1
        assert lines[0][0] == "Frog"

    def test_function_header_in(self):
        path = CsvPath()
        scanner = path.parse(f'${PATH}[*][in(#firstname,"Bug|Bird|Ants")]')
        lines = path.collect()
        print(f"test_function_count_in: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_count_in: line: {line}")
        print(f"test_function_count_in: path vars: {path.variables}")
        assert len(lines) == 3

    def test_function_count_header_in(self):
        path = CsvPath()
        scanner = path.parse(f'${PATH}[*][count(in(#firstname,"Bug|Bird|Ants"))=2]')
        lines = path.collect()
        print(f"test_function_count_in: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_count_in: line: {line}")
        print(f"test_function_count_in: path vars: {path.variables}")
        assert len(lines) == 1

    def test_function_percent(self):
        path = CsvPath()
        scanner = path.parse(f'${PATH}[*][@p = percent("match") #lastname="Bat"]')
        lines = path.collect()
        print(f"test_function_count_in: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_count_in: line: {line}")
        print(f"test_function_count_in: path vars: {path.variables}")
        assert len(lines) == 7
        assert path.variables["p"] == .75


    def test_function_below_percent(self):
        path = CsvPath()
        scanner = path.parse(f'${PATH}[*][@p = percent("match")  below(@p,.35) #lastname="Bat"]')
        lines = path.collect()
        print(f"test_function_below_percent: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_below_percent: line: {line}")
        print(f"test_function_below_percent: path vars: {path.variables}")
        assert len(lines) == 3
        assert path.variables["p"] == .375



    def test_function_first(self):
        path = CsvPath()
        scanner = path.parse(f'${PATH}[*][first(#lastname)]')
        lines = path.collect()
        print(f"test_function_first: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_first: line: {line}")
        print(f"test_function_first: path vars: {path.variables}")
        assert len(lines) == 3
        print(f'test_function_first: lastname vars: {path.variables.get("lastname")}' )

        path = CsvPath()
        scanner = path.parse(f'${PATH}[*][first(#firstname)]')
        lines = path.collect()
        print(f"test_function_first: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_first: line: {line}")
        print(f"test_function_first: path vars: {path.variables}")
        assert len(lines) == 8
        print(f'test_function_first: firstname vars: {path.variables.get("lastname")}' )


    def test_function_above_percent(self):
        path = CsvPath()
        scanner = path.parse(f'${PATH}[*][@p = percent("line")  above(@p,.35) #lastname="Bat"]')
        lines = path.collect()
        print(f"test_function_above_percent: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_above_percent: line: {line}")
        print(f"test_function_above_percent: path vars: {path.variables}")
        assert len(lines) == 6
        assert path.variables["p"] == 1


    def test_function_upper_and_lower(self):
        path = CsvPath()
        scanner = path.parse(f'${PATH}[*][ @upper = upper(#firstname) @lower = lower(#firstname) ]')
        lines = path.collect()
        print(f"test_function_count_in: lines: {len(lines)}")
        print(f"test_function_count_in: path vars: {path.variables}")
        assert "upper" in path.variables
        assert "lower" in path.variables
        assert path.variables["lower"] == "frog"
        assert path.variables["upper"] == "FROG"


    def test_function_length(self):
        path = CsvPath()
        scanner = path.parse(f'${PATH}[*][length(#lastname)=3]')
        lines = path.collect()
        print(f"test_function_length: lines: {len(lines)}")
        assert len(lines) == 7

    def test_function_not(self):
        path = CsvPath()
        scanner = path.parse(f'${PATH}[*][not(length(#lastname)=3)]')
        lines = path.collect()
        print(f"test_function_not: lines: {len(lines)}")
        assert len(lines) == 2

    def test_function_now(self):
        path = CsvPath()
        # obviously this will break and need updating 1x a year
        scanner = path.parse(f'${PATH}[*][now("%Y") = "2024"]')
        lines = path.collect()
        print(f"test_function_now: lines: {len(lines)}")
        assert len(lines) == 9

    def test_function_in(self):
        path = CsvPath()
        scanner = path.parse(f'${PATH}[*][in( #0 , "Bug|Bird|Ants" )]')
        lines = path.collect()
        print(f"test_function_in: lines: {len(lines)}")
        assert len(lines) == 3

    def test_function_concat(self):
        path = CsvPath()
        scanner = path.parse(f'${PATH}[*][ #0 = concat("B" , "ird") ]')
        lines = path.collect()
        print(f"test_function_concat: lines: {len(lines)}")
        assert len(lines) == 1


