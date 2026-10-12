import json
import pyjson5
from typing import Any

#
# the ext supports a "full" JSONPath syntax; whereas, w/o .ext is too limiting
# both should support single quotes in paths, which we need because atm csvpaths
# require double quotes for terms. if that becomes a problem we either have to
# allow single quoted strings (probably easily doable) or unwrapped jsonpaths,
# same as we do with regexes; but this would probably be a pain.
#
from jsonpath_ng.ext import parse

# from jsonpath_ng import jsonpath, parse
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Variable, Header, Reference
from ..function import Function
from ..args import Args
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.document_utility import DocumentUtility as dout
from csvpath.util.line_spooler import CsvLineSpooler, JsonLineSpooler
from csvpath.util.nos import Nos


class JsonPath(ValueProducer):
    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                """\
                   Finds the value of an JSONPath expression given a match component containing JSON.
                """
            ),
            self.wrap(
                """\
                   With only a JSONPath, jsonpath() evaluates the whole data file as
                   one JSON document, for rules-based validation of JSON files.
                   Each jsonpath() evaluates the document on one line only: scan [*]
                   and make stop() the last match component, or scan [0]. Use
                   .nocontrib on rules like
                   jsonpath.nocontrib("$.orders[?(@.qty < 1)]") -> print("...", fail())
                   so that a conforming document still matches. The run's data is
                   the JSON document.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="from this JSON",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[Any, self.args.EMPTY_STRING, None],
        )
        a.arg(
            name="select this JSONPath",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str],
        )
        a = self.args.argset(1)
        a.arg(
            name="select this JSONPath in the whole document",
            types=[Term, Variable, Function, Reference],
            actuals=[str],
        )
        self.args.validate(self.siblings())
        super().check_valid()
        if self._is_document_form():
            self._use_document_spooler()

    #
    # True when the JSONPath selected something on this line. the match
    # comes from the selection, not the value: a selected null or false
    # still matches.
    #
    _selected: bool = False
    #
    # the whole-document form: the parsed document and the line it was
    # evaluated on. not cleared by reset(); they last for the run.
    #
    _document = None
    _document_line: int | None = None

    def reset(self) -> None:
        super().reset()
        self._selected = False

    def _is_document_form(self) -> bool:
        return len(self.siblings()) == 1

    def _use_document_spooler(self) -> None:
        #
        # the run's data is the JSON document, as with jsonschema(). only
        # swap a CsvLineSpooler: a list needs nothing, and another jsonpath()
        # in the same csvpath may already have swapped it.
        #
        lines = self.matcher.csvpath.lines
        if isinstance(lines, CsvLineSpooler):
            nos = Nos(lines.path)
            if nos.exists():
                nos.remove()
            self.matcher.csvpath.lines = JsonLineSpooler(lines)

    def _document_json(self):
        self._document_line = dout.assert_one_line(
            function=self, first_line=self._document_line
        )
        if self._document is None:
            self._document = pyjson5.decode(dout.read_document(function=self))
        return self._document

    def _produce_value(self, skip=None) -> None:
        self._selected = False
        if self._is_document_form():
            j = self._document_json()
            v = self._value_one(skip=skip)
        else:
            j = self._value_one(skip=skip)
            if j is None or str(j).strip() == "":
                self.value = None
                return
            if isinstance(j, str):
                j = pyjson5.decode(j)
            v = self._value_two(skip=skip)
        jpath = parse(v)
        r = jpath.find(j)
        #
        # find() always returns a list: one value, a list of values, or []
        #
        self._selected = len(r) > 0
        if len(r) == 1:
            self.value = r[0].value
        else:
            self.value = [_.value for _ in r]

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self._selected
