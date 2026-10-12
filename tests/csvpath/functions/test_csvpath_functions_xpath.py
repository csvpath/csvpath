from lxml.etree import XPathEvalError, XMLSyntaxError
import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException


PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsXPath(unittest.TestCase):
    def test_function_xpath1(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise, print ~
            ${PATH}[*][
                @s = xpath("<xml><is>great</is></xml>", "/xml/is")
            ]"""
        )
        path.fast_forward()
        assert "s" in path.variables
        assert path.variables["s"] == "great"

    def test_function_xpath2(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise, print ~
            ${PATH}[*][
                @s = xpath("<xml><is><great degree='ish'/></is></xml>", "/xml/is/great/@degree")
            ]"""
        )
        path.fast_forward()
        assert "s" in path.variables
        assert path.variables["s"] == "ish"

    def test_function_xpath3(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise, print ~
            ${PATH}[*][
                @s = xpath("<xml><is><great degree='ish'/></is></xml>", "")
            ]"""
        )
        with pytest.raises(XPathEvalError):
            path.fast_forward()

    def test_function_xpath4(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise, print ~
            ${PATH}[*][
                @s = xpath("", "/xml/is/great/@degree")
            ]"""
        )
        #
        # should pass, not raise exception
        #
        path.fast_forward()

    def test_function_xpath5(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise, print ~
            ${PATH}[*][
                @s = xpath(none(), "/xml/is/great/@degree")
            ]"""
        )
        #
        # should pass, not raise exception
        #
        path.fast_forward()


#
# #323: xpath() matches only when the XPath selects something, and returns
# the value of what it selected. before, as a match component it matched
# every line without parsing anything, and several result types came back
# wrong or as None.
#

HEADERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}xpath_headers.csv"
ORDERS_XML = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}xpath_orders.xml"
DOC = "<a><b>xyz</b><b>q</b><c><d>deep</d></c><m>hi <i>you</i></m><e/><!-- note --></a>"
NO_RAISE = "print, no-raise, no-fail, no-stop"


def _collect(*, body: str, file: str = PATH, scan: str = "[1]", mode: str = NO_RAISE):
    path = CsvPath()
    path.parse(f"~ validation-mode: {mode} ~ ${file}{scan}[ {body} ]")
    lines = path.collect()
    return path, lines


def _value(xpath: str, *, xml: str = DOC):
    path, _ = _collect(body=f'@v = xpath("{xml}", "{xpath}")', mode="raise, print")
    return path.variables["v"]


@pytest.mark.parametrize(
    "xpath,expected",
    [
        ("/a/b", 1),
        ("/a/z", 0),
        ("/a/e", 1),  # selected, though it has no text
        ("/a/b/@nope", 0),
        ("boolean(/a/b)", 1),
        ("boolean(/a/z)", 0),
        ("count(/a/b)", 1),
        ("count(/a/z)", 1),  # 0 is a value
        ("number(/a/z)", 0),  # NaN
        ("string(/a/b)", 1),
        ("string(/a/z)", 0),  # ""
    ],
)
def test_function_xpath_match_component_literal(xpath: str, expected: int) -> None:
    _, lines = _collect(body=f'xpath("{DOC}", "{xpath}")')
    assert len(lines) == expected


@pytest.mark.parametrize(
    "xpath,expected",
    [
        #
        # DOC has two <b>s: a node-set of several gives a list, as jsonpath()
        #
        ("/a/b", ["xyz", "q"]),
        ("/a/b/text()", ["xyz", "q"]),
        ("/a/b[1]", "xyz"),
        ("string(/a/b)", "xyz"),
        ("/a/c", "deep"),
        ("/a/m", "hi you"),
        ("count(/a/b)", 2.0),
        ("boolean(/a/b)", True),
        ("boolean(/a/z)", False),
        ("/a/z", []),
        ("/a/e", ""),
        ("/a/comment()", "note"),
    ],
)
def test_function_xpath_values(xpath: str, expected) -> None:
    assert _value(xpath) == expected


def test_function_xpath_value_attribute() -> None:
    assert _value("/a/@k", xml="<a k='w'/>") == "w"


def test_function_xpath_value_with_encoding_declaration() -> None:
    xml = "<?xml version='1.0' encoding='UTF-8'?><a><b>x</b></a>"
    assert _value("/a/b", xml=xml) == "x"
    _, lines = _collect(body=f'xpath("{xml}", "/a/b")')
    assert len(lines) == 1


def test_function_xpath_header_match_by_line() -> None:
    _, lines = _collect(body='xpath(#doc, "/order/sku")', file=HEADERS, scan="[1*]")
    assert [line[0] for line in lines] == ["1", "3"]
    _, lines = _collect(
        body="xpath(#doc, \"/order[sku != '']\")", file=HEADERS, scan="[1*]"
    )
    assert [line[0] for line in lines] == ["1"]
    _, lines = _collect(
        body='not( xpath(#doc, "/order/sku") )', file=HEADERS, scan="[1*]"
    )
    assert [line[0] for line in lines] == ["2"]


def test_function_xpath_header_selection_does_not_carry_to_next_line() -> None:
    #
    # line 1 selects, line 2 does not, line 3 selects an empty <sku>
    #
    path, lines = _collect(
        body='xpath(#doc, "/order/sku") -> push("v", xpath(#doc, "/order/sku"))',
        file=HEADERS,
        scan="[1*]",
    )
    assert [line[0] for line in lines] == ["1", "3"]
    assert path.variables["v"] == ["A-1", ""]


def test_function_xpath_xml_file_lines_do_not_match() -> None:
    #
    # #323: a multi-line XML file read line by line. no line is the document,
    # so a path written for the document matches no line. <orders> and
    # </orders> are not well-formed and are reported as errors.
    #
    path, lines = _collect(
        body='xpath(#0, "/orders/order/sku")', file=ORDERS_XML, scan="[*]"
    )
    assert lines == []
    path, lines = _collect(
        body='xpath(#0, "/orders/order/sku")',
        file=ORDERS_XML,
        scan="[*]",
        mode="print, no-raise, fail",
    )
    assert lines == []
    assert path.is_valid is False


def test_function_xpath_xml_file_well_formed_line_can_match() -> None:
    #
    # xpath() evaluates exactly the value it is given. an <order> line is
    # well-formed on its own, so a path written for that fragment matches it.
    #
    _, lines = _collect(body='xpath(#0, "/order/sku")', file=ORDERS_XML, scan="[1-2]")
    assert len(lines) == 2


def test_function_xpath_malformed_match_component() -> None:
    _, lines = _collect(body='xpath("<a><b>", "/a")')
    assert lines == []
    path, lines = _collect(body='xpath("<a><b>", "/a")', mode="print, no-raise, fail")
    assert lines == []
    assert path.is_valid is False


def test_function_xpath_malformed_raises_in_raise_mode() -> None:
    with pytest.raises(XMLSyntaxError):
        _collect(body='xpath("<a><b>", "/a")', mode="raise, print")


def test_function_xpath_empty_value_does_not_match() -> None:
    _, lines = _collect(body='xpath("", "/a")')
    assert lines == []
    _, lines = _collect(body='xpath(none(), "/a")')
    assert lines == []


#
# a node-set returns all its values: one node gives its value, several give
# a list in document order, none gives [], as jsonpath() does
#


def test_function_xpath_node_set_list_header_form() -> None:
    assert _value("/r/i", xml="<r><i>one</i><i>two</i><i>three</i></r>") == [
        "one",
        "two",
        "three",
    ]
    assert _value("/r/i", xml="<r><i>one</i></r>") == "one"


def test_function_xpath_node_set_list_items_are_stripped() -> None:
    assert _value("/r/i", xml="<r><i>  one </i><i> two</i></r>") == ["one", "two"]


def test_function_xpath_node_set_list_mixed_node_kinds() -> None:
    assert _value("/r/i | /r/@k", xml="<r k='w'><i>one</i></r>") == ["w", "one"]


def test_function_xpath_node_set_list_is_a_stack() -> None:
    xml = "<r><i>one</i><i>two</i><i>three</i></r>"
    path, _ = _collect(
        body=f'@s = xpath("{xml}", "/r/i") @top = pop("s") @bottom = peek("s", 0)',
        mode="raise, print",
    )
    assert path.variables["top"] == "three"
    assert path.variables["bottom"] == "one"
    assert path.variables["s"] == ["one", "two"]


def test_function_xpath_node_set_list_match_unchanged() -> None:
    xml = "<r><i>one</i><i>two</i></r>"
    _, lines = _collect(body=f'xpath("{xml}", "/r/i")')
    assert len(lines) == 1
    _, lines = _collect(body=f'xpath("{xml}", "/r/z")')
    assert lines == []
