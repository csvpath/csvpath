import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


class TestFunctionsPercent(unittest.TestCase):
    def test_function_percent(self):
        path = CsvPath()
        path.parse(f'${PATH}[*][@p = percent("match") #lastname=="Bat"]')
        lines = path.collect()
        print(f"test_function_count_in: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_count_in: line: {line}")
        print(f"test_function_count_in: path vars: {path.variables}")
        assert len(lines) == 7
        assert path.variables["p"] == 0.75

    def test_function_below_percent(self):
        path = CsvPath()
        path.parse(f'${PATH}[*][@p = percent("match")  below(@p,.35) #lastname=="Bat"]')
        lines = path.collect()
        print(f"test_function_below_percent: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_below_percent: line: {line}")
        print(f"test_function_below_percent: path vars: {path.variables}")
        assert len(lines) == 3
        assert path.variables["p"] == 0.375

    def test_function_above_percent(self):
        path = CsvPath()
        path.parse(f'${PATH}[*][@p=percent("line")  above(@p, .35) #lastname=="Bat"]')
        lines = path.collect()
        print(f"test_function_above_percent: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_above_percent: line: {line}")
        print(f"test_function_above_percent: path vars: {path.variables}")
        assert len(lines) == 6
        assert path.variables["p"] == 1
