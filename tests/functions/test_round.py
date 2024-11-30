import unittest
from csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


class TestFunctionsRound(unittest.TestCase):
    def test_function_round1(self):
        path = CsvPath()
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
        path.fast_forward()
        assert path.variables["fourish"] == 4.5667
        assert path.variables["four"] == 4.00
        assert path.variables["fourone"] == 4.9
        assert path.variables["fouronetwo"] == 5.0
        assert path.variables["fouronethree"] == 4.3
        assert path.variables["fouronefour"] == 4.5
        assert path.variables["fourzero"] == 5.0
        assert path.variables["none"] == 0
        assert path.variables["false"] == 0
