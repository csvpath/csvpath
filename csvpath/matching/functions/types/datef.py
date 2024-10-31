# pylint: disable=C0114
import datetime
from ..function_focus import ValueProducer
from ..args import Args
from ..function import Function

# from csvpath.matching.functions.validity.line import Line
from csvpath.matching.productions import Header, Variable, Reference, Term
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import ChildrenException


class Date(ValueProducer):
    """parses a date from a string"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="an actual date",
            types=[Term, Header, Variable, Function, Reference],
            actuals=[datetime.datetime, datetime.date],
        )
        a = self.args.argset(1)
        a.arg(
            name="guess the date",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str],
        )
        a = self.args.argset(2)
        a.arg(
            name="header name or dynamicly found",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str],
        )
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[str])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        v = None
        sibs = self.siblings()
        isline = ExpressionUtility.get_ancestor(self, "Line") is not None
        if isline:
            # if we're in a line() we assume we'll have a string and optionally format
            v = self._from_header(skip=skip)
        elif len(sibs) == 1:
            # we have a date object or a string to guess at
            v = self._from_one()
        elif len(sibs) == 2:
            # should be a date string and a format
            v = self._from_two()
        else:
            # pln = self.matcher.csvpath.line_monitor.physical_line_number
            self.value = None
            self.parent.raise_if(
                ChildrenException(
                    "Expected a date or a date as a string, optionally with a format"
                )
            )
            return
        #
        if isinstance(v, (datetime.datetime, datetime.date)):
            if isinstance(v, datetime.datetime) and not self.name == "datetime":
                v = v.date()
            self.value = v
            return
        #
        # no date, but that could be Ok
        #
        elif v is None or v == "":
            if self.notnone:
                self.value = None
                # pln = self.matcher.csvpath.line_monitor.physical_line_number
                self.parent.raise_if(ChildrenException("Date cannot be empty"))
            return
        #
        # not sure what this value is
        #
        self.value = None
        # pln = self.matcher.csvpath.line_monitor.physical_line_number
        self.parent.raise_if(ChildrenException(f"'{v}' is not a date or datetime"))

    def _from_one(self):
        v = self._value_one()
        if v and isinstance(v, (datetime.datetime, datetime.date)):
            return v
        elif v and isinstance(v, str):
            return ExpressionUtility.to_date(v)

    def _from_two(self):
        v = self._value_one()
        v = f"{v}".strip()
        fmt = self._value_two()
        r = self._date_from_strings(v, fmt)
        return r

    def _date_from_strings(self, adate, aformat):
        try:
            aformat = f"{aformat}".strip()
            return datetime.datetime.strptime(adate, aformat)
        except Exception as e:
            if adate == "" and not self.notnone:
                return None
            # pln = self.matcher.csvpath.line_monitor.physical_line_number
            self.parent.raise_if(
                ChildrenException(f"Cannot parse date '{adate}' using '{aformat}'"),
                cause=e,
            )
            return None

    def _from_header(self, skip=None):
        v = self._value_one(skip=skip)
        v = f"{v}".strip()
        hv = self.matcher.get_header_value(v)
        if hv is None or f"{hv}".strip() == "" and self.notnone is True:
            # pln = self.matcher.csvpath.line_monitor.physical_line_number
            self.parent.raise_if(ChildrenException(f": '{v}' cannot be empty"))
            return None
        else:
            fmt = self._value_two(skip=skip)
            ret = None
            if fmt:
                ret = self._date_from_strings(hv, fmt)
            else:
                ret = ExpressionUtility.to_datetime(hv)
            return ret

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip) is not None  # pragma: no cover
