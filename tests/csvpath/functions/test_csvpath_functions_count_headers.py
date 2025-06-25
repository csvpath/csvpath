import unittest
import os
from csvpath import CsvPath

MISMATCH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}header_mismatch.csv"


class TestCsvPathFunctionsCountHeaders(unittest.TestCase):
    def test_function_count_headers1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${MISMATCH}[*]
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
            ${MISMATCH}[*]
            [
                gt(count_headers_in_line(),  count_headers()) -> @toomany = count_lines()
                lt(count_headers_in_line(),  count_headers()) -> @toofew = count_lines()
            ]"""
        )
        path.collect()
        assert path.variables["toomany"] == 4
        assert path.variables["toofew"] == 3
