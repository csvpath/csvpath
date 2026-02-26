import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}hnm.csv"


class TestCsvPathFunctionsHeaderNamesMatch(unittest.TestCase):
    def test_function_header_names_match_1(self):
        path = CsvPath().parse(
            f""" ${PATH}[*][
                header_names_match("product_id|name|price|in_stock")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 3

    def test_function_header_names_match_2(self):
        path = CsvPath().parse(
            f""" ${PATH}[*][
                header_names_mismatch("product_id|name|price|in_stock")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_function_header_names_match_3(self):
        path = CsvPath().parse(
            f""" ${PATH}[*][
                header_names_match("name|product_id|price|in_stock")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_function_header_names_match_4(self):
        path = CsvPath().parse(
            f""" ${PATH}[*][
                header_names_mismatch("name|product_id|price|in_stock")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 3

    def test_function_header_names_match_5(self):
        path = CsvPath().parse(
            f""" ${PATH}[*][
                header_names_match("|product_id|name|price|in_stock|")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 3

    def test_function_header_names_match_6(self):
        path = CsvPath().parse(
            f""" ${PATH}[*][
                ~ assignment doesn't affect matching so we match by default ~
                @a = header_names_match("product_id|name|price|in_stock")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 3
        assert path.variables["a"] is True

    def test_function_header_names_match_7(self):
        path = CsvPath().parse(
            f""" ${PATH}[*][
                ~ assignment doesn't affect matching but we request an explict
                  consideration of @a. @a is True so we match. ~
                @a.asbool = header_names_match("product_id|name|price|in_stock")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 3
        assert path.variables["a"] is True

    def test_function_header_names_match_8(self):
        path = CsvPath().parse(
            f""" ${PATH}[*][
                ~ assignment doesn't affect matching but rather than match by default
                  asbool requests an evaluation of the value assigned to @a, which is False ~
                @a.asbool = header_names_mismatch("product_id|name|price|in_stock")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0
        assert path.variables["a"] is False

    def test_function_header_names_match_9(self):
        path = CsvPath().parse(
            f""" ${PATH}[*][
                ~ assignment doesn't affect matching so we match by default
                  however, @a is still false ~
                @a = header_names_mismatch("product_id|name|price|in_stock")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 3
        assert path.variables["a"] is False
