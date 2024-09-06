import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsEvery(unittest.TestCase):
    def test_function_every1(self):
        path = CsvPath()
        print("")
        Save._save(path, "test_function_every1")
        path.parse(
            f"""${PATH}
                        [*]
                        [
                            push( "chk", every.fishy(#lastname=="Bat", 2) )
                            every.fishing(#lastname=="Bat", 2)
                        ]
                   """
        )
        #
        # we capture 1 #lastname!="Bat" because there are 2 such lines
        # and we capture 3 #lastname=="Bat" because there are 7 such lines
        #
        lines = path.collect()
        print(f"test_function_every1: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_every1: line: {line}")
        print(f"test_function_every1: path vars: {path.variables}")
        assert len(lines) == 4

    def test_function_every2(self):
        path = CsvPath()
        Save._save(path, "test_function_every2")
        path.parse(
            f"""${PATH}[*]
                        [
                            @t.onmatch=count()
                            every.who(#lastname, 2)
                        ]
                   """
        )
        #
        # TODO: has dup in test_qualifiers test_every_qualifier2
        # doing: every.who.onmatch() would be a great new test,
        # but not ready for it yet.
        #
        lines = path.collect()
        print(f"test_function_every2: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_every2: line: {line}")
        print(f"test_function_every2: path vars: {path.variables}")
        assert "who" in path.variables
        assert path.variables["who"]["Bat"] == 7

    def test_function_every3(self):
        path = CsvPath()
        Save._save(path, "test_function_every3")
        path.parse(
            f"""
            ${PATH}[*]
            [
                every(#lastname=="Bat", 3 )
            ]"""
        )
        lines = path.collect()
        print(f"test_function_every3: path vars: {path.variables}")
        print(f"lines: {lines}")
        assert len(lines) == 2
