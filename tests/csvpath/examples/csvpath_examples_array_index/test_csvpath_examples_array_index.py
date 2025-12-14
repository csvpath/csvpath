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
               id: schema
               validation-mode: raise, print
               source-mode: preceding
               explain-mode: explain
            ~
            ${PATH}[1*][
                count_headers_in_line() == 1 -> skip()
                reset_headers()

                @order = eq(#0, "H")
                @item = eq(#0, "D")

                tally.entities(@order, @item)
                line_number.nocontrib() == 8 -> var_table("entities")

                @order.asbool.nocontrib -> line.orders(
                    string.notnone.type(#0,1,1),
                    integer.orderid( #1),
                    integer.customerid( #2),
                    string.customer(#3, 255, 3),
                    string(#4),
                    string.address(#5)
                )

                @item.asbool.nocontrib -> line.items(
                    string.notnone.type(#0, 1, 1),
                    integer.notnone.sku(#1, 99999999, 1 ),
                    string.description(#2,255, 5),
                    decimal.price(#3, none(), .10),
                    integer.quantity(#4, none(), 1)
                )
            ]
            """
        )
        path.fast_forward()
