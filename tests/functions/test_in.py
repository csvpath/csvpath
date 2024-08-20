import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"
FOOD = "tests/test_resources/food.csv"


class TestFunctionsIn(unittest.TestCase):
    def test_function_header_in(self):
        path = CsvPath()
        Save._save(path, "test_function_header_in")
        path.parse(f'${PATH}[*][in(#firstname,"Bug|Bird|Ants")]')
        lines = path.collect()
        print(f"test_function_count_in: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_count_in: line: {line}")
        print(f"test_function_count_in: path vars: {path.variables}")
        assert len(lines) == 3

    def test_function_count_header_in1(self):
        """~this test is also in with count but there using onmatch"""
        path = CsvPath()
        Save._save(path, "test_function_count_header_in1")
        path.parse(
            f"""
                        ${PATH}
                        [*]
                        [count.one( in(#firstname,"Bug|Bird|Ants") ) == 2]
                   """
        )
        lines = path.collect()
        print(f"test_function_count_in: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_count_in: line: {line}")
        print(f"test_function_count_in: path vars: {path.variables}")
        assert len(lines) == 2
        assert "one" in path.variables
        assert path.variables["one"][True] == 3
        assert path.variables["one"][False] == 6

    def test_function_count_header_in_ever(self):
        path = CsvPath()
        Save._save(path, "test_function_count_header_in_ever")
        path.parse(
            f"""
                ${PATH}
                [*]
                [
                    @x.onmatch = count()
                    in(#firstname,"Bug|Bird|Ants")
                ]
                   """
        )
        lines = path.collect()
        print(f"test_function_count_in: lines: {len(lines)}")
        for line in lines:
            print(f"test_function_count_in: line: {line}")
        print(f"test_function_count_in: path vars: {path.variables}")
        assert "x" in path.variables
        assert path.variables["x"] == 3
        assert len(lines) == 3

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
        print(f"test_function_first: path vars: {path.variables}")
        assert "year" in path.variables
        assert path.variables["year"]["1643"] == 4

    def test_function_in(self):
        path = CsvPath()
        Save._save(path, "test_function_in")
        path.parse(f'${PATH}[*][in( #0 , "Bug|Bird|Ants" )]')
        lines = path.collect()
        print(f"test_function_in: lines: {len(lines)}")
        assert len(lines) == 3

    def test_function_concat1(self):
        path = CsvPath()
        Save._save(path, "test_function_concat1")
        path.parse(
            f"""
                        ${PATH}[*]
                               [ #0 == concat("B" , "ird") ]
                   """
        )
        lines = path.collect()
        print(f"test_function_concat: lines: {len(lines)}")
        assert len(lines) == 1

    def test_function_onchange2(self):
        path = CsvPath()
        Save._save(path, "test_function_onchange2")
        path.parse(
            f""" ${PATH}[*] [
                @oc.onchange.onmatch = in(#firstname, "Frog|Bug|Fish")
                print.onmatch("printing: oc: $.variables.oc, count: $.match_count")
            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_onchange2: path vars: {path.variables}")
        print(f"test_function_onchange2: lines: {lines}")
        assert path.variables["oc"] is True
        assert len(lines) == 4
