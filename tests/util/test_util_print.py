import unittest
import os
from csvpath.matching.util.lark_print_parser import (
    LarkPrintParser,
    LarkPrintTransformer,
)


class TestUtilPrint(unittest.TestCase):
    def test_print_lark_print_parser_parse_and_transform(self):
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
        transformer = LarkPrintTransformer()
        ps = transformer.transform(t)
        j = 0
        for _ in ps:
            j = j + 1
            if f"{_}".strip() == "":
                j -= 1
        assert ps
        assert j == 5
