import unittest
import pytest
import logging
from io import StringIO as buffer
from csvpath import CsvPath, CsvPaths
from csvpath.util.log_utility import LogUtility
from csvpath.util.printer import LogPrinter
from csvpath.util.printer import TestPrinter
from csvpath.matching.functions.print.printf import Print, PrintParser
from csvpath.matching.util.lark_print_parser import (
    LarkPrintParser,
    LarkPrintTransformer,
)
from csvpath.matching.util.print_parser import PrintParserException
from tests.save import Save

PATH = "tests/test_resources/test.csv"
PATH2 = "tests/test_resources/test-3.csv"
MISMATCH = "tests/test_resources/header_mismatch.csv"


class TestPrint(unittest.TestCase):
    def test_function_log_printer1(self):
        buf = buffer()
        h = logging.StreamHandler(buf)
        path = CsvPath()
        logger = LogUtility.logger(path, "info")
        path.logger = logger
        path.logger.addHandler(h)
        printer = LogPrinter(path.logger)
        printer.print_to(None, "fish!")
        printer.print_to("info", "cat!")
        printer.print_to("what?", "bear!")
        printer.print_to("debug", "deer!")
        printer.print_to("warn", "mouse!")
        printer.print_to("error", "ox!")
        path.logger.removeHandler(h)
        text = buf.getvalue()
        buf.close()
        assert text.find("fish!") > -1
        assert text.find("cat!") > -1
        assert text.find("bear!") > -1
        assert text.find("deer!") == -1
        assert text.find("ox!") > -1
        assert text.find("mouse!") > -1

    def test_print_get_runtime_data_from_results(self):
        print("")
        paths = CsvPaths()
        paths.file_manager.add_named_files_from_dir("tests/test_resources/named_files")
        paths.paths_manager.add_named_paths_from_dir(
            directory="tests/test_resources/named_paths"
        )
        paths.collect_paths(filename="food", pathsname="food")
        results = paths.results_manager.get_named_results("food")
        parser = PrintParser()
        d = results[1].csvpath.delimiter
        q = results[1].csvpath.quotechar
        assert len(results) == 2
        with pytest.raises(PrintParserException):
            results[1].csvpath.delimiter = "#"
            parser._get_runtime_data_from_results(None, results)
        with pytest.raises(PrintParserException):
            results[1].csvpath.quotechar = "#"
            parser._get_runtime_data_from_results(None, results)
        results[1].csvpath.delimiter = d
        results[1].csvpath.quotechar = q
        data = parser._get_runtime_data_from_results(None, results)
        assert isinstance(data["file_name"], str)
        data2 = parser._get_runtime_data_from_results(None, [results[0]])
        assert data["lines_time"] > data2["lines_time"]
        print(f'cnt lines: {data["count_lines"]}')
        assert "candy check" in data["count_lines"]
        assert data["count_lines"]["candy check"] != data["count_lines"]["first type"]
        print(f'line no: {data["line_number"]}')
        assert "candy check" in data["line_number"]
        assert data["line_number"]["candy check"] != data["line_number"]["first type"]
        print(f'cnt matches: {data["count_matches"]}')
        assert "candy check" in data["count_matches"]
        assert (
            data["count_matches"]["candy check"] != data["count_matches"]["first type"]
        )
        print(f'cnt scans: {data["count_scans"]}')
        assert "candy check" in data["count_scans"]
        assert data["count_scans"]["candy check"] != data["count_scans"]["first type"]
        print(f'scan part: {data["scan_part"]}')
        assert "candy check" in data["scan_part"]
        assert data["scan_part"]["candy check"] != data["scan_part"]["first type"]
        print(f'match part: {data["match_part"]}')
        assert "candy check" in data["match_part"]
        assert data["match_part"]["candy check"] != data["match_part"]["first type"]
        print(f'last line time: {data["last_line_time"]}')
        assert "candy check" in data["last_line_time"]
        assert (
            data["last_line_time"]["candy check"]
            != data["last_line_time"]["first type"]
        )
        print(f'total lines: {data["total_lines"]}')
        assert isinstance(data["total_lines"], int)
        assert data["total_lines"] == 11
        print(f'headers: {data["headers"]}')
        assert "candy check" in data["headers"]
        assert isinstance(data["headers"]["candy check"], list)
        assert len(data["headers"]["candy check"]) == 5
        print(f'valid: {data["valid"]}')
        assert "candy check" in data["valid"]
        assert isinstance(data["valid"]["candy check"], bool)
        assert data["valid"]["candy check"] is False
        assert data["valid"]["candy check"] != data["valid"]["first type"]
        print(f'stopped: {data["stopped"]}')
        assert "candy check" in data["stopped"]
        assert isinstance(data["stopped"]["candy check"], bool)
        assert data["stopped"]["candy check"] is True
        assert data["stopped"]["candy check"] == data["stopped"]["first type"]

    def test_print_header_ref(self):
        print("")
        paths = CsvPaths()
        paths.file_manager.add_named_files_from_dir("tests/test_resources/named_files")
        paths.paths_manager.add_named_paths_from_dir(
            directory="tests/test_resources/named_paths"
        )
        paths.collect_paths(filename="food", pathsname="food")

        results = paths.results_manager.get_named_results("food")
        for r in results:
            print(f"r: {r}")
            print(f"r.headers: {r.csvpath.headers}")
        parser = PrintParser()
        data: dict = parser._get_headers(None, results)
        print(f"dict: {data}")
        assert len(data) == 2
        assert "candy check" in data
        assert len(data["candy check"]) == 5

    def test_print_once1(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_print_once1")
        printer = TestPrinter()
        path.set_printers([printer])
        path.parse(
            f"""${MISMATCH}[*] [
            yes()
                print.once(
                    "Number of headers changed by $.variables.header_change..")
        ]"""
        )
        lines = path.collect()
        print(f"test_print_once1: match lines: {len(lines)}")
        print(f"test_print_once1: match lines: {lines}")
        assert len(lines) == 4
        print(f"test_print_once1: print lines: {printer.lines}")
        assert len(printer.lines) == 1

    def test_print_once2(self):
        #
        # this test is unusual. the expected result is not intuitive:
        # the a var should in fact == "a". the reason is:
        #    - when a variable is not found the name requested is returned
        #    - a is not found
        #    - a comes before print, so you would think it had been set
        #    - however, count() counts matches. it implies the onmatch
        #           qualifier. the rest of the match components are run
        #           before count(), same as for any onmatch component
        #     - the result is that print() prints 'a == a' which we are
        #           capturing from the printer for our test
        # with this test we're just making sure the expected behavior
        # doesn't change. I can't think of a logical way to improve how
        # we make assignments, so I think we're just going to run across
        # this gotcha every so often.
        #
        print("")
        path = CsvPath()
        Save._save(path, "test_print_once2")
        printer = TestPrinter()
        path.set_printers([printer])
        path.parse(
            f"""${MISMATCH}[*] [
            yes()
            @a = count()
            print.onchange.once("a == $.variables.a")
        ]"""
        )
        lines = path.collect()
        print(f"\ntest_print_once2: match lines: {len(lines)}")
        print(f"test_print_once2: match lines: {lines}")
        print(f"test_print_once2: match vars: {path.variables}")
        assert len(lines) == 4
        print(f"test_print_once2: print lines: {printer.lines}")
        assert len(printer.lines) == 1
        assert printer.lines[0] == "a == a"

    def test_lark_print_parser_parse_and_transform(self):
        printstr = """$me.headers.level
            $me.headers.message
            $.headers.'this is a header'
            $.variables.'this is a variable'
            $.csvpath.count_lines
            """
        #    $.variables.'this is a variable'.day
        #    $.variables.news.day
        #    $.metadata.news.day

        parser = LarkPrintParser()
        t = parser.parse(printstr)
        print(f"tree: {t.pretty()}")
        transformer = LarkPrintTransformer()
        ps = transformer.transform(t)
        j = 0
        for _ in ps:
            j = j + 1
            if f"{_}".strip() == "":
                j -= 1
            print(f"\n ... ps[_]: {_}")
        assert ps
        assert j == 5

    def test_print_parser_transform_csvpath_data1(self):
        path = CsvPath()
        path.parse(f"""${PATH}[*] [ yes() ]""")
        lines = path.collect()
        print(f"test_print_parser_transform_csvpath_data1: lines: {len(lines)}")
        parser = PrintParser(path)

        printstr = """ $.csvpath.count_lines """
        result = parser.transform(printstr)
        assert result
        assert result.strip() == "9"

        printstr = """ $.csvpath.delimiter """
        result = parser.transform(printstr)
        assert result
        assert result.strip() == ","

        printstr = """ $.csvpath.quotechar """
        result = parser.transform(printstr)
        assert result
        assert result.strip() == '"'

        printstr = """ $.csvpath.scan_part """
        result = parser.transform(printstr)
        assert result
        assert result.strip() == f"${PATH}[*]"

        printstr = """ $.csvpath.match_part """
        result = parser.transform(printstr)
        assert result
        assert result.strip() == "[ yes() ]"

    def test_print_parser_transform_csvpath_data2(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1*] [
                not( count_lines() == 3 )
                print("count of lines: $.csvpath.count_lines")

                count_lines.nocontrib() == 6 -> stop()
            ]"""
        )
        lines = path.collect()
        print(f"test_print_parser_transform_csvpath_data2: lines: {len(lines)}")
        parser = PrintParser(path)

        printstr = """ $.csvpath.count_lines """
        result = parser.transform(printstr)
        assert result
        assert result.strip() == "6"

        printstr = """ $.csvpath.count_matches """
        result = parser.transform(printstr)
        assert result
        assert result.strip() == "4"

        printstr = """ $.csvpath.count_scans """
        result = parser.transform(printstr)
        assert result
        assert result.strip() == "5"

        printstr = """ $.csvpath.total_lines """
        result = parser.transform(printstr)
        assert result
        assert result.strip() == "9"

    def test_print_parser_transform_variables1(self):
        path = CsvPath()
        path.parse(f"""${PATH}[*] [ yes() ]""")
        lines = path.collect()
        print(f"test_print_parser_transform_variables1: lines: {len(lines)}")
        parser = PrintParser(path)

        path.variables["test"] = "test"
        path.variables["one"] = 1
        path.variables["stack"] = ["a", "b", "c"]
        path.variables["tracking"] = {}
        path.variables["tracking"]["value"] = "fish"
        path.variables["a name with spaces"] = "whoohoo"

        printstr = """ $.variables.test """
        result = parser.transform(printstr)
        assert result
        assert result.strip() == "test"

        printstr = """ $.variables.one """
        result = parser.transform(printstr)
        assert result
        assert result.strip() == "1"

        printstr = """ $.variables.'a name with spaces' """
        result = parser.transform(printstr)
        assert result
        assert result.strip() == "whoohoo"

    def test_print_parser_transform_variables2(self):
        path = CsvPath()
        path.parse(f"""${PATH}[*] [ yes() ]""")
        lines = path.collect()
        print(f"test_print_parser_transform_variables2: lines: {len(lines)}")
        parser = PrintParser(path)

        path.variables["test"] = "test"
        path.variables["one"] = 1
        path.variables["stack"] = ["a", "b", "c"]
        path.variables["tracking"] = {}
        path.variables["tracking"]["value"] = "fish"
        path.variables["a name with spaces"] = "whoohoo"

        if True:
            #
            # space
            #
            printstr = """ $.variables.tracking.value """
            result = parser.transform(printstr)
            assert result
            assert result.strip() == "fish"
            #
            # escaped .
            #
            printstr = """ $.variables.tracking.value.. another thing """
            result = parser.transform(printstr)
            assert result
            assert result.strip() == "fish. another thing"
            #
            # EOL
            #
            printstr = """ $.variables.tracking.value"""
            result = parser.transform(printstr)
            assert result
            assert result.strip() == "fish"
            #
            # space word
            #
            printstr = """ $.variables.tracking.value after"""
            result = parser.transform(printstr)
            assert result
            assert result.strip() == "fish after"
            #
            # non-alnum
            #
            printstr = """ $.variables.tracking.value-- after"""
            result = parser.transform(printstr)
            assert result
            assert result.strip() == "fish-- after"
            #
            # quoted reference
            #
            printstr = """ "$.variables.tracking.value" after"""
            result = parser.transform(printstr)
            assert result
            assert result.strip() == """ "fish" after""".strip()
            #
            # single quoted reference
            #
            printstr = """ '$.variables.tracking.value' after"""
            result = parser.transform(printstr)
            assert result
            assert result.strip() == """ 'fish' after""".strip()

    def test_print_parser_transform_variables3(self):
        path = CsvPath()
        path.parse(f"""${PATH}[*] [ yes() ]""")
        lines = path.collect()
        print(f"test_print_parser_transform_variables3: lines: {len(lines)}")
        parser = PrintParser(path)

        path.variables["test"] = "test"
        path.variables["one"] = 1
        path.variables["stack"] = ["a", "b", "c"]
        path.variables["tracking"] = {}
        path.variables["tracking"]["value"] = "fish"
        path.variables["a name with spaces"] = "whoohoo"

        if True:
            printstr = """ $.variables.stack.1 """
            result = parser.transform(printstr)
            assert result
            assert result.strip() == "b"

        if True:
            printstr = """ $.variables.stack.length """
            result = parser.transform(printstr)
            assert result
            assert result.strip() == "3"

    def test_print_parser_transform_headers(self):
        path = CsvPath()
        path.parse(f"""${PATH}[*] [ yes() ]""")
        lines = path.collect()
        print(f"test_function_concat: lines: {len(lines)}")
        parser = PrintParser(path)

        printstr = """ $.headers.say """
        assert path.line_monitor.data_line_count == 9
        result = parser.transform(printstr)
        assert result
        assert result.strip() == "growl"

        printstr = """ $.headers.2 """
        result = parser.transform(printstr)
        assert result
        assert result.strip() == "growl"

        path = CsvPath()
        path.parse(f"""${PATH2}[*] [ yes() ]""")
        lines = path.collect()
        parser = PrintParser(path)

        printstr = """ $.headers.'What I say' """
        result = parser.transform(printstr)
        assert result
        assert result.strip() == "growl"

    def test_print_parser_transform_metadata(self):
        path = CsvPath()
        pathstr = f"""
            ~ name: test path
              description: a way of checking things ~
            ${PATH}[*] [ yes() ]"""
        path.parse(pathstr)
        lines = path.collect()
        print(f"test_function_concat: lines: {len(lines)}")
        parser = PrintParser(path)

        printstr = """ $.metadata.description """
        result = parser.transform(printstr)
        assert result
        assert result.strip() == "a way of checking things"

        printstr = """ $.metadata.name """
        result = parser.transform(printstr)
        assert result
        assert result.strip() == "test path"

        printstr = """ $.metadata.fish """
        result = parser.transform(printstr)
        assert result.strip() == "fish"

    def test_print_parser_named_paths_data(self):
        paths = CsvPaths()
        LogUtility.logger(paths, "debug")

        paths.file_manager.add_named_files_from_dir("tests/test_resources/named_files")
        paths.paths_manager.add_named_paths_from_dir(
            directory="tests/test_resources/named_paths"
        )

        paths.fast_forward_paths(pathsname="food", filename="food")

        path = paths.csvpath()
        LogUtility.logger(path, "debug")

        pathstr = f"""
            ~ name: test path
              description: a way of checking things ~
            ${PATH}[*] [ yes() ]"""
        path.parse(pathstr)
        lines = path.collect()
        print(f"test_function_concat: lines: {len(lines)}")
        parser = PrintParser(path)

        printstr = """ $food.variables.type """
        result = parser.transform(printstr)
        assert result.strip() == "fruit"

        printstr = """ $food.metadata.valid """
        result = parser.transform(printstr)
        assert result.strip() == "False"

    # ==================

    def test_print_parser_variables1(self):
        path = CsvPath()
        LogUtility.logger(path, "debug")

        pathstr = f"""
            ${PATH}[*] [
                ~ problem: seeing the first var, but not the second ~
                @a = "test"
                @b = #firstname
        ]"""
        path.parse(pathstr)
        lines = path.collect()
        print(f"test_print_parser_variables1: lines: {len(lines)}")
        parser = PrintParser(path)

        printstr = """ $.variables.a, $.variables.b """
        result = parser.transform(printstr)
        assert result.strip() == "test, Frog"

    def test_print_parser_variables2(self):
        path = CsvPath()
        LogUtility.logger(path, "info")

        pathstr = f"""
            ${PATH}[*] [
                @a = "test"
                @b = #firstname
                @c = "see"
                @d = "dee"
                @e = "eee"
                @f = "f"
                @g = "g"
                @h = "h"
                @i = "i"
                @j = "j"
                @k = "k"
                @l = "l"
                @m = "m"
                @n = "n"
                @o = "o"
                @p = "p"
        ]"""
        path.parse(pathstr)
        lines = path.collect()
        print(f"test_print_parser_variables2: lines: {len(lines)}")
        parser = PrintParser(path)
        #
        # notice the double dot escape for $.variables.a..
        #
        printstr = """
            b: $.variables.b,
            a: $.variables.a..
            c: $.variables.c;
            d: $.variables.d%
            (e: $.variables.e)
            f: $.variables.f#
            g: $.variables.g@
            h: $.variables.h{
            i: $.variables.i}
            j: $.variables.j[
            k: $.variables.k]
            l: $.variables.l/
            m: $.variables.m|
            n: $.variables.n<
            o: $.variables.o>
            p: $.variables.p&
        """

        result = parser.transform(printstr)
        print(f"test_print_parser_variables2: result: {result}")
        assert (
            result.strip()
            == """
            b: Frog,
            a: test.
            c: see;
            d: dee%
            (e: eee)
            f: f#
            g: g@
            h: h{
            i: i}
            j: j[
            k: k]
            l: l/
            m: m|
            n: n<
            o: o>
            p: p&
        """.strip()
        )
