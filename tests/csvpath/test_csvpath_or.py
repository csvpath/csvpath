import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
T = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}trivial.csv"


class TestCsvPathOr(unittest.TestCase):
    def test_csvpath_logical_or1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.AND = False
        c = f"""
            ${PATH}[*][
               #firstname == "Ants"
               #firstname == "Slug"
        ]"""
        lines = path.collect(c)
        assert len(lines) == 2

    def test_csvpath_logical_or2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.AND = False
        lines = path.collect(
            f"""${PATH}[*][
            mod(count_lines(), 2) == 0
            mod(count_lines(), 3) == 0
        ]"""
        )
        assert len(lines) == 6

    def test_csvpath_logical_or3(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.AND = False
        path.parse(
            f"""${T}[*][
                ~ this is a problem? it was because expression with only comment ~
                missing(headers())
                too_long(#lastname, 30)
          ]"""
        )
        lines = path.collect()
        assert len(lines) == 2
