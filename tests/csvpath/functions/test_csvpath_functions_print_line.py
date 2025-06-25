import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.matcher import Matcher

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsPrintLine(unittest.TestCase):
    def test_function_print_line1(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                   last() -> print_line()
            ] """
        )
        path.fast_forward()
        assert path.printers[0].last_line == "Frog,Bat,growl"

    def test_function_print_line2(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                   last() -> print_line("default", "|","quotes")
            ] """
        )
        path.fast_forward()
        assert path.printers[0].last_line == '"Frog"|"Bat"|"growl"'

    def test_function_print_line3(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                   last() -> print_line("toads")
            ] """
        )
        path.fast_forward()
        assert len(path.printers) == 1
        # this will be printed to stdout:
        #    '[toads] Frog,Bat,growl'
        assert path.printers[0].last_line == "Frog,Bat,growl"

    def test_function_print_line4(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                   #0 == "Frog" -> replace(#0, "Toad")
                   last() -> print_line("toads")
            ] """
        )
        path.fast_forward()
        assert len(path.printers) == 1
        # this will be printed to stdout:
        #    '[toads] Toad,Bat,growl'
        assert path.printers[0].last_line == "Toad,Bat,growl"

    def test_function_print_line5(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                   collect(#0,#1)
                   #0 == "Frog" -> replace(#0, "Toad")
                   last() -> print_line("toads")
            ] """
        )
        path.fast_forward()
        assert len(path.printers) == 1
        # this will be printed to stdout:
        #    '[toads] Toad,Bat'
        assert path.printers[0].last_line == "Toad,Bat"

    def test_function_print_queue(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                    print("$.csvpath.line_number")
                    print_queue() == 5 -> stop()
            ] """
        )
        path.fast_forward()
        assert path.printers[0].last_line == "4"
