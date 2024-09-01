import unittest
import pytest
from csvpath.csvpath import CsvPath
from csvpath.matching.matcher import Matcher
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsPrintLine(unittest.TestCase):
    def test_function_print_line1(self):
        path = CsvPath()
        Save._save(path, "test_function_print_line1")
        path.parse(
            f"""${PATH}[*][
                   last() -> print_line()
            ] """
        )
        path.fast_forward()
        print(
            f"test_function_print_line1: last printed: {path.printers[0]}: {path.printers[0].last_line}"
        )
        assert path.printers[0].last_line == "Frog,Bat,growl"

    def test_function_print_line2(self):
        path = CsvPath()
        Save._save(path, "test_function_print_line2")
        path.parse(
            f"""${PATH}[*][
                   last() -> print_line("|","quotes")
            ] """
        )
        path.fast_forward()
        print(
            f"test_function_print_line2: last printed: {path.printers[0]}: {path.printers[0].last_line}"
        )
        assert path.printers[0].last_line == '"Frog"|"Bat"|"growl"'

    def test_function_print_queue(self):
        path = CsvPath()
        Save._save(path, "test_function_print_queue")
        path.parse(
            f"""${PATH}[*][
                    print("$.csvpath.line_number")
                    print_queue() == 5 -> stop()
            ] """
        )
        path.fast_forward()
        print(
            f"test_function_print_queue: last printed: {path.printers[0]}: {path.printers[0].last_line}"
        )
        assert path.printers[0].last_line == "4"
