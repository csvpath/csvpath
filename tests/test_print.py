import unittest
from csvpath import CsvPath, CsvPaths
from csvpath.util.log_utility import LogUtility
from csvpath.matching.functions.printf import Print, PrintParser
from csvpath.matching.util.lark_print_parser import (
    LarkPrintParser,
    LarkPrintTransformer,
)

PATH = "tests/test_resources/test.csv"
PATH2 = "tests/test_resources/test-3.csv"


class TestPrint(unittest.TestCase):
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

    def test_print_parser_transform_csvpath_data(self):
        path = CsvPath()
        path.parse(f"""${PATH}[*] [ yes() ]""")
        lines = path.collect()
        print(f"test_function_concat: lines: {len(lines)}")
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

        path = CsvPath()
        path.parse(
            f"""${PATH}[1*] [
                not( count_lines() == 3 )
                print("count of lines: $.csvpath.count_lines")
                count_lines.nocontrib() == 6 -> stop() ]"""
        )
        lines = path.collect()
        print(f"test_function_concat: lines: {len(lines)}")
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

    def test_print_parser_transform_variables(self):
        path = CsvPath()
        path.parse(f"""${PATH}[*] [ yes() ]""")
        lines = path.collect()
        print(f"test_function_concat: lines: {len(lines)}")
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

        """
        printstr = "" $.variables.stack.1 ""
        result = parser.transform(printstr)
        assert result
        assert result.strip() == "b"
        """
        """
        printstr = "" $.variables.stack.length ""
        result = parser.transform(printstr)
        assert result
        assert result.strip() == "3"
        """
        """
        printstr = "" $.variables.tracking.value ""
        result = parser.transform(printstr)
        assert result
        assert result.strip() == "fish"
        """

        printstr = """ $.variables.'a name with spaces' """
        result = parser.transform(printstr)
        assert result
        assert result.strip() == "whoohoo"

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

        paths.files_manager.add_named_files_from_dir("tests/test_resources/named_files")
        paths.paths_manager.add_named_paths_from_dir("tests/test_resources/named_paths")

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
