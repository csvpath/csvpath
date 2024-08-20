import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"
FOOD = "tests/test_resources/food.csv"


class TestFunctionsFirst(unittest.TestCase):
    def test_function_first1(self):
        path = CsvPath()
        Save._save(path, "test_function_first1")
        path.parse(f"${PATH}[*][first.surnames(#lastname)]")
        lines = path.collect()
        print(f"test_function_first: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_first: line: {line}")
        print(f"test_function_first1: path vars: {path.variables}")
        for _ in path.variables:
            print(f"  ..._:{_}")
            for k, v in enumerate(path.variables[_].items()):
                print(f"     ... {k} = {v}")
        assert len(lines) == 3
        assert "surnames" in path.variables
        assert path.variables["surnames"]["Bat"] == 2

    def test_function_first2(self):
        path = CsvPath()
        Save._save(path, "test_function_first2")
        path.parse(f"${PATH}[*][first.folks(#firstname)]")
        lines = path.collect()
        print(f"test_function_first: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_first: line: {line}")
        print(f"test_function_first2: path vars: {path.variables}")
        assert len(lines) == 8
        assert "folks" in path.variables
        assert path.variables["folks"]["Frog"] == 3

    def test_function_first3(self):
        path = CsvPath()
        Save._save(path, "test_function_first3")
        path.parse(f"${PATH}[*][first.dude(#firstname, #lastname)]")
        lines = path.collect()
        print(f"test_function_first: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_first: line: {line}")
        print(f"test_function_first3: path vars: {path.variables}")
        assert len(lines) == 8
        assert "dude" in path.variables
        assert path.variables["dude"]["FrogBat"] == 3

    def test_function_first4(self):
        path = CsvPath()
        Save._save(path, "test_function_first4")
        path.parse(
            f"""${FOOD}[*]
                        [ ~ Find the first time fruit were the most popular ~
                            @fruit = in( #food, "Apple|Pear|Blueberry")
                            ~@food.onmatch = #food~
                            @fruit.asbool -> print("$.headers.food $.headers.year")
                            first.year.onmatch( #year )
                            exists( @fruit.asbool )
                            last.nocontrib() -> print("First years most popular: $.variables.year")
                        ]
                    """
        )
        path.collect()
        print(f"test_function_first4: path vars: {path.variables}")
        assert "year" in path.variables
        assert path.variables["year"]["1643"] == 4
