import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsRound(unittest.TestCase):
    def test_function_round1(self):
        path = CsvPath()
        Save._save(path, "test_function_round1")
        path.parse(
            f""" ${PATH}[2] [
                @fourish = round( 4.5666666, 4 )
                @four = round(4)
                @fourzero = round(4.54, 0)
                @fourone = round(4.9, 1)
                @fouronetwo = round(4.9, 0)
                @fouronethree = round(4.33, 1)
                @fouronefour = round(4.498, 2)
                @none = round( none() )
                @false = round( false() )
            ]
            """
        )
        print("")
        path.fast_forward()
        print(f"test_function_round1: path vars: {path.variables}")
        assert path.variables["fourish"] == 4.5667
        assert path.variables["four"] == 4.00
        assert path.variables["fourone"] == 4.9
        assert path.variables["fouronetwo"] == 5.0
        assert path.variables["fouronethree"] == 4.3
        assert path.variables["fouronefour"] == 4.5
        assert path.variables["fourzero"] == 5.0
        assert path.variables["none"] == 0
        assert path.variables["false"] == 0
