import unittest
import os
from csvpath.matching.functions.function_factory import FunctionFactory
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
PHYSICAL = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}count_physical_lines.csv"


class TestCsvPathFunctionsCount(unittest.TestCase):
    def test_function_factory_count(self):
        count = FunctionFactory.get_function(None, name="count", child=None)
        assert count

    def test_function_factory_count_empty(self):
        f = FunctionFactory.get_function(None, name="count", child=None)
        assert f.to_value() == 0  # no matcher or csvpath == -1 + eager match 1

    def test_function_count_equality(self):
        path = CsvPath()
        path.parse(f'${PATH}[*][count(#lastname=="Bat")==7]')
        lines = path.collect()
        assert len(lines) == 1
        assert lines[0][0] == "Frog"

    def test_function_count_headers_in(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}
                [*][
                    count.firstname_is_one.onmatch( in(#firstname,"Bug|Bird|Ants") ) == 2
                ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert "firstname_is_one" in path.variables
        assert path.variables["firstname_is_one"][True] == 3

    def test_function_count_header_in_ever1(self):
        path = CsvPath()
        path.parse(
            f"""
                ${PATH}
                [1*]
                [
                    @x.onmatch = count()
                    in(#firstname,"Bug|Bird|Ants")
                ]
                   """
        )
        lines = path.collect()
        assert "x" in path.variables
        assert path.variables["x"] == 3
        assert len(lines) == 3

    def test_function_count_lines(self):
        path = CsvPath()

        path.parse(f'${PATH}[*][ #firstname=="David" @david.onmatch=count_lines() ]')
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["david"] == 2

    def test_function_count_scans(self):
        path = CsvPath()

        path.parse(
            f'${PATH}[*][ #firstname=="Frog" @frogs_seen=count() @scanned_for_frogs=count_scans()  ]'
        )
        lines = path.collect()
        assert len(lines) == 2
        assert path.variables["frogs_seen"] == 2
        assert path.variables["scanned_for_frogs"] == 9

    def test_function_count_nocount(self):
        path = CsvPath()

        path.parse(
            f"""
            ${PATH}[*][ @imcounting = count() no()]
            """
        )
        lines = path.collect()
        assert "imcounting" not in path.variables
        assert len(lines) == 0

    def test_function_count_allcount(self):
        path = CsvPath()

        path.parse(
            f"""
            ${PATH}[*][ @imcounting = count() yes()]
            """
        )
        lines = path.collect()
        assert "imcounting" in path.variables
        assert path.variables["imcounting"] == 9
        assert len(lines) == 9

    def test_function_count_linecount1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*][ @imcounting = count_lines() no()]
            """
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert "imcounting" in path.variables
        # lines are zero-based, unlike match counts
        assert path.variables["imcounting"] == 9
        assert len(lines) == 0

    def test_function_count_linecount2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*][ @imcounting.onmatch = count_lines() no()]
            """
        )
        lines = path.collect()
        assert "imcounting" not in path.variables
        # lines are zero-based, unlike match counts
        # assert path.variables["imcounting"] == 0
        assert len(lines) == 0

    def test_function_count_linecount3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PHYSICAL}[*][
                push( "physical", line_number() )
                push( "data", count_lines())
            ]
            """
        )
        path.fast_forward()
        assert "physical" in path.variables
        assert "data" in path.variables
        assert path.variables["physical"] == [0, 1, 5, 7]
        assert path.variables["data"] == [1, 2, 3, 4]
