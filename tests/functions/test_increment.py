import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsIncrement(unittest.TestCase):
    def test_function_increment(self):
        path = CsvPath()
        Save._save(path, "test_function_increment")
        path.parse(
            f"""
            ${PATH}[*]
            [
                @i = increment.test(yes(), 3)
                @j = increment.double_check(yes(), 2)
                @k = increment.rand(random(0,1)==1, 2)
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert len(lines) == 9
        assert path.variables["test"] == 9
        assert path.variables["i"] == 3
        assert path.variables["j"] == 4
        assert path.variables["double_check_increment"] == 4

    def test_function_increment2(self):
        path = CsvPath()
        Save._save(path, "test_function_increment2")
        path.parse(
            f"""
            ${PATH}[*]
            [
                @i = increment.never.onmatch(yes(), 3)
                @j = increment.always(yes(), 3)
                @k = increment.onmatch.still_never(yes(), 3)
                no()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert len(lines) == 0
        assert path.variables["j"] == 3
        assert path.variables["i"] == 0
        assert path.variables["k"] == 0
        assert path.variables.get("still_never") is None

    # FIXME: this works to show that @var.onchange correctly matches when set to a
    # new value. it is not a deterministic test. there is a deterministic test in test_function_onchange2
    # leaving this as an example, for now.
    def test_function_onchange1(self):
        path = CsvPath()
        Save._save(path, "test_function_onchange1")
        path.parse(
            f""" ${PATH}[*] [
                increment.test( yes(), 3)
                ~comment
                 on lines
                ~
                @oc.onchange = @test_increment
                print.onmatch("printing: oc: $.variables.oc, test: $.variables.test, count: $.match_count")
            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_last: path vars: {path.variables}")
        print(f"test_function_last: lines: {lines}")
        assert path.variables["oc"] == 3.0
        assert len(lines) == 3
