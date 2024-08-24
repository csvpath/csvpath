import unittest
import pytest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsRegex(unittest.TestCase):
    def test_function_regex1(self):
        path = CsvPath()
        Save._save(path, "test_function_regex1")
        path.parse(
            f"""
            ${PATH}[0-7]
            [
                regex(#say, /sniffle/)
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_regex1: lines: {lines}")
        print(f"test_function_regex1: path vars: {path.variables}")
        assert len(lines) == 1

    def test_function_bad_regex1(self):
        path = CsvPath()
        with pytest.raises(Exception):
            path.parse(f"""${PATH}[0-7][regex(#say, /`\&`\_\L\J/)]""")  # noqa: W605
            lines = path.collect()
            assert len(lines) == 0

    def test_function_good_regex1(self):
        path = CsvPath()
        Save._save(path, "test_function_good_regex1")
        path.parse(
            f"""
            ${PATH}[0-7][ regex(#say, /^sniffl[Ee]/) ]
            """
        )
