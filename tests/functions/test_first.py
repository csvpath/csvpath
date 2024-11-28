import unittest
from csvpath import CsvPath

PATH = "tests/test_resources/test.csv"
FOOD = "tests/test_resources/food.csv"


class TestFunctionsFirst(unittest.TestCase):
    def test_function_first1(self):
        path = CsvPath()
        path.parse(f"${PATH}[*][first.surnames(#lastname)]")
        lines = path.collect()
        assert len(lines) == 3
        assert "surnames" in path.variables
        assert path.variables["surnames"]["Bat"] == 2

    def test_function_first2(self):
        path = CsvPath()
        path.parse(f"${PATH}[*][first.folks(#firstname)]")
        lines = path.collect()
        assert len(lines) == 8
        assert "folks" in path.variables
        assert path.variables["folks"]["Frog"] == 3

    def test_function_first3(self):
        path = CsvPath()
        path.parse(f"${PATH}[*][first.dude(#firstname, #lastname)]")
        lines = path.collect()
        assert len(lines) == 8
        assert "dude" in path.variables
        assert path.variables["dude"]["FrogBat"] == 3

    def test_function_first4(self):
        path = CsvPath()
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
        assert "year" in path.variables
        assert path.variables["year"]["1643"] == 4
