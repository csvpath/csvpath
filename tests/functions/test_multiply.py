import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsMultiply(unittest.TestCase):
    def test_function_multiply(self):
        path = CsvPath()
        Save._save(path, "test_function_multiply")
        path.parse(
            f"""
            ${PATH}[2-5]
            [ @l = multiply( count(#lastname), 100 ) ]"""
        )
        lines = path.collect()
        print(f"test_function_multiply: lines: {lines}")
        print(f"test_function_multiply: path vars: {path.variables}")
        assert len(lines) == 4
        assert path.variables["l"] == 400

    def test_function_multiply2(self):
        path = CsvPath()
        Save._save(path, "test_function_multiply2")
        path.parse(
            f"""
            ${PATH}[2-3]
            [ @l = multiply( count(), 100 ) ]"""
        )
        lines = path.collect()
        print(f"test_function_multiply2: lines: {lines}")
        print(f"test_function_multiply2: path vars: {path.variables}")
        assert len(lines) == 2
        assert path.variables["l"] == 200

    def test_function_multiply3(self):
        path = CsvPath()
        Save._save(path, "test_function_multiply3")
        path.parse(
            f"""
            ${PATH}[2+3]
            [ @l = multiply( count(), add(50,50,50,50) ) ]"""
        )
        lines = path.collect()
        print(f"test_function_multiply3: lines: {lines}")
        print(f"test_function_multiply3: path vars: {path.variables}")
        assert len(lines) == 2
        assert path.variables["l"] == 400

    def test_function_multiply4(self):
        path = CsvPath()
        Save._save(path, "test_function_multiply4")
        path.parse(
            f"""
            ${PATH}[2+3]
            [ @l = multiply( count(), add(50,50,50), 50 ) ]"""
        )
        lines = path.collect()
        print(f"test_function_multiply4: lines: {lines}")
        print(f"test_function_multiply4: path vars: {path.variables}")
        assert len(lines) == 2
        assert path.variables["l"] == 15000
