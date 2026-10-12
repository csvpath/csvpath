"""The whole-document forms of xpath() and jsonpath() (#323).

With only a path, xpath("/orders/order") and jsonpath("$.orders") evaluate
the whole data file as one XML or JSON document, for rules-based
validation of documents: each rule fires a message when its path selects
something. Each whole-document call evaluates the document on one line
only. The usual form is [*] with stop() as the last match component, which
runs on the first line with data; [0] also works when the file does not
start with a blank line. Evaluating on a second line stops the run with an
error.
"""

import json
import os

import pytest
from lxml.etree import XMLSyntaxError
import pyjson5

from csvpath import CsvPath
from csvpath.matching.util.document_utility import DocumentUtility as dout
from csvpath.matching.util.exceptions import ChildrenException, MatchException
from csvpath.util.nos import Nos
from tests.csvpaths.builder import Builder

DOCS = os.path.join("tests", "csvpath", "test_resources", "documents")
NO_RAISE_FAIL = "print, no-raise, fail"

XML_RULES = """
    not.nocontrib( xpath("/orders/order") ) -> print("There must be at least one order", fail())
    xpath.nocontrib("/orders/order[not(sku)]") -> print("Every order must have a sku", fail())
    xpath.nocontrib("/orders/order[@id = preceding-sibling::order/@id]") -> print("Order ids must be unique", fail())
    @orders = xpath("count(/orders/order)")
"""

JSON_RULES = """
    not.nocontrib( jsonpath("$.orders[*]") ) -> print("There must be at least one order", fail())
    jsonpath.nocontrib("$.orders[?(@.qty < 1)]") -> print("Every qty must be at least 1", fail())
    @ids = jsonpath("$.orders[*].id")
"""


def _doc(name: str) -> str:
    return os.path.join(DOCS, name)


def _run(*, file: str, body: str, scan: str = "[*]", mode: str = NO_RAISE_FAIL):
    path = CsvPath()
    path.parse(f"~ validation-mode: {mode} ~ ${_doc(file)}{scan}[ {body} ]")
    lines = path.collect()
    return path, lines


#
# XML rules
#


def test_document_xpath_rules_conforming(capsys) -> None:
    path, lines = _run(file="orders_good.xml", body=f"{XML_RULES} stop()")
    assert path.is_valid is True
    assert path.variables["orders"] == 3.0
    assert len(lines) == 1
    out = capsys.readouterr().out
    assert "must" not in out


def test_document_xpath_rules_violating(capsys) -> None:
    path, lines = _run(file="orders_bad.xml", body=f"{XML_RULES} stop()")
    assert path.is_valid is False
    out = capsys.readouterr().out
    #
    # every rule ran on the one line
    #
    assert "Every order must have a sku" in out
    assert "Order ids must be unique" in out
    assert "There must be at least one order" not in out
    assert path.variables["orders"] == 3.0


def test_document_xpath_commas_and_quotes_do_not_matter() -> None:
    #
    # orders_good.xml has commas inside attributes. read as CSV lines they
    # would split; the whole-document form reads the raw file.
    #
    path, _ = _run(
        file="orders_good.xml",
        body='@note = xpath("/orders/order[@id=1]/@note") stop()',
    )
    assert path.variables["note"] == "say, hello"


#
# JSON rules
#


def test_document_jsonpath_rules_conforming(capsys) -> None:
    path, lines = _run(file="orders_good.json", body=JSON_RULES)
    assert path.is_valid is True
    assert path.variables["ids"] == [1, 2]
    assert len(lines) == 1
    assert "must" not in capsys.readouterr().out


def test_document_jsonpath_rules_violating(capsys) -> None:
    path, _ = _run(file="orders_bad.json", body=JSON_RULES)
    assert path.is_valid is False
    out = capsys.readouterr().out
    assert "Every qty must be at least 1" in out
    assert "There must be at least one order" not in out


#
# scan forms
#


def test_document_xpath_scan_zero() -> None:
    path, lines = _run(file="orders_good.xml", body=XML_RULES, scan="[0]")
    assert path.is_valid is True
    assert path.variables["orders"] == 3.0
    assert len(lines) == 1


def test_document_xpath_leading_blank_lines_with_stop() -> None:
    #
    # [0] is a blank line, which is skipped. [*] with a final stop() runs on
    # the first line with data.
    #
    path, lines = _run(
        file="orders_blank_lead.xml",
        body='@orders = xpath("count(/orders/order)") push("seen", line_number()) stop()',
    )
    assert path.variables["orders"] == 1.0
    assert path.variables["seen"] == [2]
    assert len(lines) == 1


def test_document_xpath_conditional_single_use_on_last_line() -> None:
    path, _ = _run(
        file="orders_good.xml",
        body='last.nocontrib() -> @orders = xpath("count(/orders/order)")',
    )
    assert path.is_valid is True
    assert path.variables["orders"] == 3.0


def test_document_xpath_one_line_file_without_stop() -> None:
    path, _ = _run(file="orders_one_line.xml", body=XML_RULES)
    assert path.is_valid is True
    assert path.variables["orders"] == 1.0


#
# one line only
#


def test_document_xpath_second_line_raises_in_raise_mode() -> None:
    with pytest.raises(MatchException, match="one line only"):
        _run(file="orders_good.xml", body=XML_RULES, mode="raise, print")


def test_document_xpath_second_line_stops_and_fails(capsys) -> None:
    path, _ = _run(
        file="orders_bad.xml", body=f'{XML_RULES} push("seen", line_number())'
    )
    assert path.stopped is True
    assert path.is_valid is False
    out = capsys.readouterr().out
    assert "one line only" in out
    #
    # the rules ran once, on line 0
    #
    assert out.count("Every order must have a sku") == 1
    assert path.variables["seen"] == [0]


def test_document_jsonpath_second_line_raises() -> None:
    #
    # a .json file is read as one line. the same JSON in a .txt file is read
    # line by line, so a missing stop() reaches a second line.
    #
    with pytest.raises(MatchException, match="one line only"):
        _run(file="orders_json_as_text.txt", body=JSON_RULES, mode="raise, print")


def test_document_jsonpath_from_text_file_with_stop() -> None:
    path, _ = _run(file="orders_json_as_text.txt", body=f"{JSON_RULES} stop()")
    assert path.is_valid is True
    assert path.variables["ids"] == [1, 2]


#
# arguments
#


@pytest.mark.parametrize("function", ["xpath", "jsonpath"])
def test_document_form_rejects_header_argument(function: str) -> None:
    path = CsvPath()
    with pytest.raises(ChildrenException):
        path.parse(
            f"~ validation-mode: raise, print ~ ${_doc('orders_good.xml')}[*][ {function}(#0) ]"
        )
        path.collect()


def test_document_form_from_variable() -> None:
    path, _ = _run(
        file="orders_good.xml",
        body='@p = "count(/orders/order)" @orders = xpath(@p) stop()',
    )
    assert path.variables["orders"] == 3.0


def test_two_argument_header_form_still_runs_every_line() -> None:
    path, lines = _run(
        file="orders_good.xml",
        body='xpath(#0, "/order/sku")',
        mode="print, no-raise, no-fail",
    )
    #
    # the <order> lines are well-formed on their own, except line 2: read as
    # CSV, the comma in its note attribute splits it. that is why the
    # whole-document form reads the raw file.
    #
    assert len(lines) == 2
    assert path.stopped is False


#
# malformed documents
#


def test_document_xpath_malformed_raise_mode() -> None:
    with pytest.raises(XMLSyntaxError):
        _run(
            file="orders_malformed.xml", body=f"{XML_RULES} stop()", mode="raise, print"
        )


def test_document_xpath_malformed_fail_mode() -> None:
    path, lines = _run(file="orders_malformed.xml", body=f"{XML_RULES} stop()")
    assert path.is_valid is False
    assert lines == []


def test_document_jsonpath_malformed_raise_mode() -> None:
    with pytest.raises(pyjson5.Json5Exception):
        _run(
            file="orders_malformed_json_as_text.txt",
            body=f"{JSON_RULES} stop()",
            mode="raise, print",
        )


def test_document_jsonpath_malformed_fail_mode() -> None:
    path, lines = _run(
        file="orders_malformed_json_as_text.txt", body=f"{JSON_RULES} stop()"
    )
    assert path.is_valid is False
    assert lines == []


@pytest.mark.parametrize("mode", ["raise, print", NO_RAISE_FAIL])
def test_document_malformed_json_file_fails_in_the_reader(mode: str) -> None:
    #
    # existing behavior, not part of jsonpath(): a .json file is parsed by
    # the file reader before any csvpath runs, in every validation mode
    #
    with pytest.raises(json.JSONDecodeError):
        _run(file="orders_malformed.json", body=JSON_RULES, mode=mode)


#
# the document is read once per call per run
#


def test_document_read_once_per_call(monkeypatch) -> None:
    reads = []
    original = dout.read_document

    def counting(*, function):
        reads.append(function.name)
        return original(function=function)

    monkeypatch.setattr(dout, "read_document", staticmethod(counting))
    path, _ = _run(
        file="orders_good.xml",
        body='@a = xpath("count(/orders/order)") @b = xpath("count(/orders/order)") @c = xpath("count(/orders/order)") stop()',
    )
    assert path.variables["a"] == 3.0
    assert reads == ["xpath", "xpath", "xpath"]


#
# DocumentUtility
#


def test_document_utility_bad_args() -> None:
    with pytest.raises(ValueError):
        dout.assert_one_line(function=None, first_line=None)
    with pytest.raises(ValueError):
        dout.read_document(function=None)


#
# the run's data is the document
#


def _named_run(*, name: str, file: str, csvpath: str):
    paths = Builder().build()
    paths.config.set(section="errors", name="csvpaths", value="print, no-raise, fail")
    paths.paths_manager.remove_named_paths(name)
    paths.paths_manager.add_named_paths(name=name, paths=[csvpath])
    paths.file_manager.add_named_file(name=name, path=_doc(file))
    ref = paths.collect_paths(pathsname=name, filename=name)
    results = paths.results_manager.get_named_results(ref)
    return paths, results


def test_document_xpath_run_data_is_the_document() -> None:
    name = "document_xpath_data_test"
    paths, results = _named_run(
        name=name, file="orders_good.xml", csvpath=f"$[*][ {XML_RULES} stop() ]"
    )
    try:
        assert len(results) == 1
        assert results[0].csvpath.is_valid is True
        home = results[0].instance_dir
        assert not Nos(Nos(home).join("data.csv")).exists()
        copy = Nos(home).join("data.xml")
        assert Nos(copy).exists()
        with (
            open(copy, encoding="utf-8") as a,
            open(_doc("orders_good.xml"), encoding="utf-8") as b,
        ):
            assert a.read() == b.read()
    finally:
        paths.paths_manager.remove_named_paths(name)
        paths.file_manager.remove_named_file(name)


def test_document_jsonpath_run_data_is_the_document() -> None:
    name = "document_jsonpath_data_test"
    paths, results = _named_run(
        name=name, file="orders_good.json", csvpath=f"$[*][ {JSON_RULES} ]"
    )
    try:
        assert len(results) == 1
        assert results[0].csvpath.is_valid is True
        home = results[0].instance_dir
        assert not Nos(Nos(home).join("data.csv")).exists()
        copy = Nos(home).join("data.json")
        assert Nos(copy).exists()
        with open(copy, encoding="utf-8") as f:
            data = json.load(f)
        with open(_doc("orders_good.json"), encoding="utf-8") as f:
            original = json.load(f)
        #
        # JsonLineSpooler writes the line, and a .json file's one line is
        # [document]. the same as jsonschema() runs produce.
        #
        assert data == [original]
    finally:
        paths.paths_manager.remove_named_paths(name)
        paths.file_manager.remove_named_file(name)


#
# a whole-document node-set returns all its values
#


def test_document_xpath_node_set_list() -> None:
    path, _ = _run(file="orders_good.xml", body='@skus = xpath("//order/sku") stop()')
    assert path.variables["skus"] == ["A-1", "B-2", "C-3"]


def test_document_xpath_node_set_list_as_a_stack() -> None:
    path, _ = _run(
        file="orders_good.xml",
        body='@skus = xpath("//order/sku") @last = pop("skus") @first = peek("skus", 0) stop()',
    )
    assert path.variables["last"] == "C-3"
    assert path.variables["first"] == "A-1"


def test_document_xpath_multi_node_rule_fires_once(capsys) -> None:
    path, _ = _run(
        file="orders_good.xml",
        body='xpath.nocontrib("//order/sku") -> print("found skus") stop()',
    )
    assert capsys.readouterr().out.count("found skus") == 1
