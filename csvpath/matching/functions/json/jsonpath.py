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
from csvpath.matching.util.exceptions import DataException, MatchException


class JsonPath(ValueProducer):
    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                """\
                   Finds the value of an JSONPath expression given a match component containing JSON.
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
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        j = self._value_one(skip=skip)
        if j is None or str(j).strip() == "":
            self.value = None
            return
        if isinstance(j, str):
            j = pyjson5.decode(j)
        v = self._value_two(skip=skip)
        jpath = parse(v)
        r = jpath.find(j)
        if r is not None and len(r) == 1:
            self.value = r[0].value
        elif r is not None:
            self.value = [_.value for _ in r]
        else:
            raise DataException("No value for jsonpath")

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()
