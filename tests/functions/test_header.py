import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"
EMPTY = "tests/test_resources/empty.csv"


class TestFunctionsHeader(unittest.TestCase):
    def test_function_header1(self):
        path = CsvPath()
        Save._save(path, "test_function_any_function1")
        path.parse(
            f"""
            ${PATH}[3]
            [
                @frog = any(headers(), "Frog")
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["frog"] is True

    def test_function_header3(self):
        path = CsvPath()
        Save._save(path, "test_function_any_function3")
        path.parse(
            f"""
            ${PATH}[3]
            [
                @v = any(variables())
                @frog = any(headers(), "Frog")
                @found = any()
                @slug = any("slug")
                @bear = any(headers(),"Bear")
                @me = any("True")
                @h = any(headers())
                @v2 = any(variables())
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["frog"] is True
        assert path.variables["found"] is True
        assert path.variables["slug"] is False
        assert path.variables["bear"] is False
        assert path.variables["v"] is False
        assert path.variables["v2"] is True
        assert path.variables["h"] is True

    def test_function_header4(self):
        path = CsvPath()
        Save._save(path, "test_function_any_function4")
        path.parse(
            f"""
            ${EMPTY}[1-2]
            [
                @found = any(headers())
                @notfound = not(any(headers()))
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        assert len(lines) == 2
        assert path.variables["found"] is False
        assert path.variables["notfound"] is True

    def test_function_header5(self):
        path = CsvPath()
        Save._save(path, "test_function_any_function5")
        path.parse(
            f"""
            ${PATH}[1-2]
            [
                no()
                ~ 81 is returning its value, not its match, because it's being
                  assigned. it isn't participating because onmatch fails so
                  its value is None, rather than its default match which is
                  True, as for all components. so None is the right answer ~
                @found = any.onmatch.81(headers())
                @found2 = any.82(headers())
                ~ 83 is similar to 81; however, we are getting the match
                  not the value because we're not being assigned. that means True.
                  when not(True) False. the trick is realizing that not() is being
                  assigned, but the contents of not() are being matched.
                  assignment is not transitive.
                ~
                @notfound = not(any.onmatch.83(headers()))
            ]"""
        )
        lines = path.collect()
        print(f"json: {path.matcher.dump_all_expressions_to_json()}")
        print(f"\n test_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        assert path.variables["found"] is None
        assert path.variables["found2"] is True
        assert path.variables["notfound"] is False

    def test_function_header6(self):
        path = CsvPath()
        Save._save(path, "test_function_header_exists")
        path.parse(
            f"""
            ${PATH}[*]
            [
                @has_firstname = headers("firstname")
                @has_space_aliens = headers("it is aliens")
                @fn = header_names_mismatch("firstname|lastname|say")
            ]"""
        )
        path.fast_forward()
        print(f"test_function_any_function: path vars: {path.variables}")
        assert path.variables["has_firstname"] is True
        assert path.variables["has_space_aliens"] is False
        assert path.variables["fn"] is True
