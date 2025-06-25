import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsMetaphone(unittest.TestCase):
    def test_function_metaphone1(self):
        path = CsvPath()
        path.parse(
            f"""
                        ${PATH}[*][
                            @z1 = metaphone("zach")
                            @z2 = metaphone("zack")
                            @z = equals(@z1, @z2)

                            @s1 = metaphone("Sacks")
                            @s2 = metaphone("Sax")
                            @s = equals(@s1, @s2)
                        ]
                   """
        )
        path.fast_forward()
        assert path.variables["z"] is True
        assert path.variables["s"] is True
