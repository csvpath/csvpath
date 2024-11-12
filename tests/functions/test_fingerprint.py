import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsFingerprint(unittest.TestCase):
    def test_function_fingerprint_1(self):
        path = CsvPath()
        Save._save(path, "test_function_fingerprint_1")
        path.parse(
            f"""
            ${PATH}[3-6]
            [
                last() -> file_fingerprint()
                last() -> file_fingerprint.hash()
            ]"""
        )
        path.collect()
        print(f"path meta: {path.metadata}")
        assert "file_fingerprint" in path.metadata
        assert "hash" in path.metadata
        assert path.metadata["hash"] == path.metadata["file_fingerprint"]

    def test_function_fingerprint_2(self):
        path = CsvPath()
        Save._save(path, "test_function_fingerprint_2")
        path.parse(
            f"""
            ${PATH}[*]
            [
                line_fingerprint()
                last() -> store_line_fingerprint()
            ]"""
        )
        path.collect()
        print(f"path meta: {path.metadata}")
        print(f"path vars: {path.variables}")
        assert "by_line_fingerprint" in path.metadata
        assert "by_line_fingerprint" not in path.variables
