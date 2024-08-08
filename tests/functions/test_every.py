import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


class TestFunctionsEvery(unittest.TestCase):
    def test_function_every_qualifier1(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}
                        [*]
                        [
                            @t.onmatch=count()
                            every.fish(#lastname=="Bat", 2)
                            #lastname=="Bat"
                        ]
                   """
        )
        #
        # we capture 1 #lastname!="Bat" because there are 2 such lines
        # and we capture 3 #lastname=="Bat" because there are 7 such lines
        #
        lines = path.collect()
        print(f"test_function_every_qualifier: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_every_qualifier: line: {line}")
        print(f"test_function_every_qualifier: path vars: {path.variables}")
        assert len(lines) == 3
        assert path.variables["t"] == 3
        assert "fish" in path.variables
        assert path.variables["fish"][True] == 4

    def test_function_every_qualifier2(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}
                        [*]
                        [
                            @t.onmatch=count()
                            every.who(#lastname, 2)
                        ]
                   """
        )
        #
        # we capture 3 #lastnames because there are 3 total in 9
        # and we match on 3 #lastnames because there are 7 "Bat"
        #
        lines = path.collect()
        print(f"test_function_every_qualifier: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_every_qualifier: line: {line}")
        print(f"test_function_every_qualifier: path vars: {path.variables}")
        assert len(lines) == 3
        assert path.variables["t"] == 3
        assert "who" in path.variables
        assert path.variables["who"][True] == 3

    def test_function_every1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                every(#lastname=="Bat", 3 )
            ]"""
        )
        lines = path.collect()
        print(f"test_function_every: path vars: {path.variables}")
        print(f"lines: {lines}")
        assert len(lines) == 2
