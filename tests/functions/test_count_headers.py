import unittest
from csvpath import CsvPath

PATH = "tests/test_resources/header_mismatch.csv"


class TestFunctionsCountHeaders(unittest.TestCase):
    def test_function_count_headers1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                gt(count_headers_in_line(),  count_headers()) -> @toomany = yes()
                lt(count_headers_in_line(),  count_headers()) -> @toofew = yes()
            ]"""
        )
        path.collect()
        assert path.variables["toomany"] is True
        assert path.variables["toofew"] is True

    def test_function_count_headers2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                gt(count_headers_in_line(),  count_headers()) -> @toomany = count_lines()
                lt(count_headers_in_line(),  count_headers()) -> @toofew = count_lines()
            ]"""
        )
        path.collect()
        assert path.variables["toomany"] == 4
        assert path.variables["toofew"] == 3
