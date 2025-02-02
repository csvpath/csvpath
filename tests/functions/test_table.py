import unittest
import os
from csvpath import CsvPath
from csvpath.matching.matcher import Matcher
from csvpath.matching.functions.boolean.any import Any
from csvpath.matching.productions import Expression

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"
EMPTIES = f"tests{os.sep}test_resources{os.sep}test-4.csv"


class TestFunctionsTable(unittest.TestCase):
    def test_function_header_table1(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1][
                header_table()
            ]"""
        )
        path.fast_forward()
        line = path.printers[0].last_line
        assert line[0] == "┌"
        assert line[len(line) - 1] == "┘"
        assert line.find("#N │ #Name") > -1
        assert line.find("2 │ say") > -1

    def test_function_row_table1(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1][
                row_table()
            ]"""
        )
        path.fast_forward()
        line = path.printers[0].last_line
        assert line[0] == "┌"
        assert line[len(line) - 1] == "┘"
        assert line.find("firstname") > -1
        assert line.find("hi!") > -1

    def test_function_row_table2(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1][
                row_table(1)
            ]"""
        )
        path.fast_forward()
        line = path.printers[0].last_line
        assert line[0] == "┌"
        assert line[len(line) - 1] == "┘"
        assert line.find("lastname") > -1
        assert line.find("Kermit") > -1
        assert line.find("firstname") == -1
        assert line.find("say") == -1

    def test_function_row_table3(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1][
                row_table(1,2)
            ]"""
        )
        path.fast_forward()
        line = path.printers[0].last_line
        assert line[0] == "┌"
        assert line[len(line) - 1] == "┘"
        assert line.find("lastname") > -1
        assert line.find("Kermit") > -1
        assert line.find("say") > -1
        assert line.find("firstname") == -1

    def test_function_var_table1(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1-3][
                push("ln", line_number())
                @a = concat(#firstname, " ", #lastname)
                push("votes", vote_stack())
                @b = "123456 7890 abcdef gh ijklmn op"
                last() -> var_table()
            ]"""
        )
        path.fast_forward()
        line = path.printers[0].last_line
        assert line[0] == "┌"
        assert line[len(line) - 1] == "┘"
        assert line.find("ln") > -1
        assert line.find("votes") > -1
        assert line.find("Frog Bat") > -1

    def test_function_var_table2(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1-3][
                push("ln", line_number())
                @a = concat(#firstname, " ", #lastname)
                push("votes", vote_stack())
                @b = "123456 7890 abcdef gh ijklmn op"
                last() -> var_table("votes")
            ]"""
        )
        path.fast_forward()
        line = path.printers[0].last_line
        assert line[0] == "┌"
        assert line[len(line) - 1] == "┘"
        assert line.find("ln") == -1
        assert line.find("votes") > -1
        assert line.find("Frog Bat") == -1

    def test_function_var_table3(self):
        path = CsvPath()

        path.parse(
            f"""${PATH}[1*][
                tally(#firstname)
                last() -> var_table("tally_firstname")
            ]"""
        )
        path.fast_forward()
        line = path.printers[0].last_line
        assert line[0] == "┌"
        assert line[len(line) - 1] == "┘"
        assert line.find("firstname") > -1

    def test_function_var_table4(self):
        path = CsvPath()
        path.parse(
            f"""${EMPTIES}[1*][
                push("empties", empty_stack())
                last() -> var_table("empties")
            ]"""
        )
        path.fast_forward()
        line = path.printers[0].last_line
        assert line[0] == "┌"
        assert line[len(line) - 1] == "┘"
        assert line.find("firstname") > -1

    def test_function_run_table1(self):
        path = CsvPath()
        path.parse(
            f"""
                ~ name: fishery ~
                ${PATH}[*][
                push("empties", empty_stack())
                last() -> var_table()
                last() -> run_table()
            ]"""
        )
        path.fast_forward()
        line = path.printers[0].last_line
        assert line[0] == "┌"
        assert line[len(line) - 1] == "┘"
