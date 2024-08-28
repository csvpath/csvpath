import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestPop(unittest.TestCase):
    def test_function_push1(self):
        path = CsvPath()
        Save._save(path, "test_function_push1")
        path.parse(
            f"""
            ${PATH}[*]
            [
                push("pushed", count_lines())
                @popped = pop("pushed")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_push1: path vars: {path.variables}")
        assert len(lines) == 9
        assert len(path.variables["pushed"]) == 0
        assert path.variables["popped"] == 9

    def test_function_push2(self):
        path = CsvPath()
        Save._save(path, "test_function_push2")
        path.parse(
            f"""
            ${PATH}[*]
            [
                push_distinct("pushed", #lastname )
                push.distinct("dis", #lastname )
                ~ who was second? ~
                @peek = peek("dis", 1)
                @peeksize = peek_size("dis")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_push2: path vars: {path.variables}")
        assert len(lines) == 9
        assert len(path.variables["pushed"]) == 3
        assert len(path.variables["dis"]) == 3
        assert path.variables["peek"] == "Kermit"
        assert path.variables["peeksize"] == 3

    def test_function_pop1(self):
        path = CsvPath()
        Save._save(path, "test_function_pop1")
        path.parse(
            f"""
            ${PATH}[*]
            [
                push("pushed", count_lines())
                @popped = pop("pushed")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_pop1: path vars: {path.variables}")
        assert len(lines) == 9
        assert len(path.variables["pushed"]) == 0
        assert path.variables["popped"] == 9

    def test_function_stack1(self):
        path = CsvPath()
        Save._save(path, "test_function_stack1")
        path.parse(
            f"""
            ${PATH}[*]
            [
                @r = stack("st")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_stack1: path vars: {path.variables}")
        assert len(lines) == 9
        assert path.variables["r"] == []

    def test_function_stack2(self):
        path = CsvPath()
        Save._save(path, "test_function_stack2")
        path.parse(
            f"""
            ${PATH}[2+3]
            [
                push("st", #1)
                @r = stack("st")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_stack2: path vars: {path.variables}")
        assert len(lines) == 2
        assert path.variables["r"] == ["Bat", "Bat"]
