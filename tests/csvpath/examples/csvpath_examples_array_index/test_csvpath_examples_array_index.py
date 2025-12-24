import unittest
import pytest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}examples{os.sep}csvpath_examples_array_index{os.sep}August_2019_Orders.csv"


class TestCsvpathExamplesArrayIndex(unittest.TestCase):
    def test_csvpath_examples_array_index(self):
        path = CsvPath()
        path.parse(
            f"""
            ~
              This test demonstrates blank() and line() working in an OR. both were having troubles
              with default value and/or default match. It also shows a simple 2 entity schema. If
              we add print the run gets noisy. If we need print but don't want the noise we have to
              have a way to test for each entity type in a when/do statement. Should be easy to do
              in most cases.

                 id: schema
                 validation-mode: no-raise, no-print
                 source-mode: preceding
                 explain-mode: explain
                 logic-mode:OR
            ~
            ${PATH}[*][
                line.orders(
                    string.notnone.type(#0,1,1),
                    integer.orderid( #1),
                    integer.customerid( #2),
                    string.customer(#3, 255, 3),
                    string(#4),
                    string.address(#5)
                )
                line.items(
                    string.notnone.type(#0,1,1),
                    integer.sku(#1),
                    string.description(#2),
                    decimal.price(#3),
                    integer.quantity(#4),
                    blank()
                )
            ]
            """
        )
        lines = path.collect()
        assert len(lines) == 10
        for _ in lines:
            print(f" ... {_}")
