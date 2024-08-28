import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsPercent(unittest.TestCase):
    def test_function_percent_match(self):
        path = CsvPath()
        Save._save(path, "test_function_percent")
        path.parse(
            f"""
            ${PATH}[*][
                @p = percent("match")
                #lastname=="Bat"
                print("$.headers.firstname: $.csvpath.count_lines")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_percent: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_percent: line: {line}")
        print(f"test_function_percent: path vars: {path.variables}")
        assert len(lines) == 7
        assert path.line_monitor.data_end_line_number == 8
        assert path.variables["p"] == 0.67

    def test_function_percent_below(self):
        path = CsvPath()
        Save._save(path, "test_function_percent_below")
        path.parse(f'${PATH}[*][@p = percent("match")  below(@p,.35) #lastname=="Bat"]')
        lines = path.collect()
        print(f"test_function_percent_below: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_below_percent: line: {line}")
        print(f"test_function_percent_below: path vars: {path.variables}")
        assert len(lines) == 4
        assert path.variables["p"] == 0.44

    def test_function_percent_above(self):
        path = CsvPath()
        Save._save(path, "test_function_percent_above")
        path.parse(f'${PATH}[*][@p=percent("line")  above(@p, .35) #lastname=="Bat"]')
        lines = path.collect()
        print(f"test_function_above_percent: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_percent_above: line: {line}")
        print(f"test_function_percent_above: path vars: {path.variables}")
        assert len(lines) == 6
        assert path.variables["p"] == 1
