import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/header_mismatch.csv"


class TestFunctionsCountHeaders(unittest.TestCase):
    def test_function_count_headers1(self):
        path = CsvPath()
        Save._save(path, "test_function_headers1")
        path.parse(
            f"""
            ${PATH}[*]
            [
                gt(count_headers_in_line(),  count_headers()) -> @toomany = yes()
                lt(count_headers_in_line(),  count_headers()) -> @toofew = yes()
            ]"""
        )
        path.collect()
        print(f"test_function_headers1: path vars: {path.variables}")
        assert path.variables["toomany"] is True
        assert path.variables["toofew"] is True

    def test_function_count_headers2(self):
        path = CsvPath()
        Save._save(path, "test_function_headers2")
        path.parse(
            f"""
            ${PATH}[*]
            [
                gt(count_headers_in_line(),  count_headers()) -> @toomany = count_lines()
                lt(count_headers_in_line(),  count_headers()) -> @toofew = count_lines()
            ]"""
        )
        path.collect()
        print(f"test_function_headers2: path vars: {path.variables}")
        assert path.variables["toomany"] == 1
        assert path.variables["toofew"] == 2
