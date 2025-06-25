import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsEvery(unittest.TestCase):
    def test_function_every1(self):
        path = CsvPath()
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
        assert len(lines) == 4

    def test_function_every2(self):
        path = CsvPath()
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
        path.collect()
        assert "who" in path.variables
        assert path.variables["who"]["Bat"] == 7

    def test_function_every3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                every(#lastname=="Bat", 3 )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 2
