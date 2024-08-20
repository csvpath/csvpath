import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsLength(unittest.TestCase):
    def test_function_length(self):
        path = CsvPath()
        Save._save(path, "test_function_length")
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = length("this") ]"""
        )
        lines = path.collect()
        print(f"test_function_length: lines: {lines}")
        print(f"test_function_length: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 4

    def test_function_length2(self):
        path = CsvPath()
        Save._save(path, "test_function_add1")
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( 4, length("this")) ]"""
        )
        lines = path.collect()
        print(f"test_function_length2: lines: {lines}")
        print(f"test_function_length2: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 8

    def test_function_length3(self):
        path = CsvPath()
        Save._save(path, "test_function_add2")
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( count(), length("this") ) ]"""
        )
        lines = path.collect()
        print(f"test_function_length3: lines: {lines}")
        print(f"test_function_length3: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 5

    def test_function_length4(self):
        path = CsvPath()
        Save._save(path, "test_function_add3")
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( count(), length("this"), 5 ) ]"""
        )
        lines = path.collect()
        print(f"test_function_length4: lines: {lines}")
        print(f"test_function_length4: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 10

    def test_function_length5(self):
        path = CsvPath()
        Save._save(path, "test_function_add4")
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( count(), length("this"), 5, 5 ) ]"""
        )
        lines = path.collect()
        print(f"test_function_length5: lines: {lines}")
        print(f"test_function_length5: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 15

    def test_function_length6(self):
        path = CsvPath()
        Save._save(path, "test_function_subtract")
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = subtract( count(), length("this") ) ]"""
        )
        lines = path.collect()
        print(f"test_function_length6: lines: {lines}")
        print(f"test_function_length6: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == -3

    def test_function_length7(self):
        path = CsvPath()
        Save._save(path, "test_function_subtract2")
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = subtract( 10, count(), length("this") ) ]"""
        )
        lines = path.collect()
        print(f"test_function_length7: lines: {lines}")
        print(f"test_function_length7: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 5

    def test_function_length8(self):
        path = CsvPath()
        Save._save(path, "test_function_subtract3")
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = subtract( 10, count(), length("this"), add( 2, 3) ) ]"""
        )
        lines = path.collect()
        print(f"test_function_length8: lines: {lines}")
        print(f"test_function_length8: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 0

    def test_function_match_length(self):
        path = CsvPath()
        Save._save(path, "test_function_match_length")
        path.parse(f"${PATH}[*][length(#lastname)==3]")
        lines = path.collect()
        print(f"test_function_match_length: lines: {len(lines)}")
        assert len(lines) == 7

    def test_function_not_length(self):
        path = CsvPath()
        Save._save(path, "test_function_not")
        path.parse(f"${PATH}[*][not(length(#lastname)==3)]")
        lines = path.collect()
        print(f"test_function_not_length: lines: {len(lines)}")
        assert len(lines) == 2
