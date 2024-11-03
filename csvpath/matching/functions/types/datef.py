# pylint: disable=C0114
import datetime
from csvpath.matching.productions import Header, Variable, Reference, Term
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import ValueProducer
from ..args import Args
from ..function import Function
from .type import Type


class Date(ValueProducer, Type):
    """parses a date from a string"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        #
        # we check if a term is a date first. if it isn't, we go to the headers.
        #
        a = self.args.argset(2)
        a.arg(
            name="date string or object",
            types=[Term, Header, Variable, Function, Reference],
            actuals=[datetime.datetime, datetime.date],
        )
        a.arg(
            name="format",
            types=[None, Term, Header],
            actuals=[str],
        )

        a = self.args.argset(2)
        a.arg(
            name="header name",
            types=[Term],
            actuals=[str],
        )
        a.arg(
            name="format",
            types=[None, Term],
            actuals=[str],
        )

        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        isheader = self._is_header(skip=skip)
        sibs = self.siblings()
        inaline = ExpressionUtility.get_ancestor(self, "Line") is not None
        if inaline:
            v = self._from_header_if(skip=skip)
        else:
            v = self._from_header_if(skip=skip, quiet=True)
            if not v and not isheader and len(sibs) == 1:
                v = self._from_one()
            if not v and not isheader and len(sibs) == 2:
                v = self._from_two()
        if isinstance(v, (datetime.datetime, datetime.date)):
            if isinstance(v, datetime.datetime) and not self.name == "datetime":
                v = v.date()
            self.value = v
        elif ExpressionUtility.is_none(v):
            if self.notnone:
                self.value = None
                msg = self.decorate_error_message("Date cannot be empty")
                self.parent.raise_if(ChildrenException(msg))
        else:
            msg = self.decorate_error_message(f"'{v}' is not a date or datetime")
            self.parent.raise_if(ChildrenException(msg))

    def _is_header(self, skip=None):
        h = self._value_one(skip=skip)
        h = f"{h}".strip()
        for _ in self.matcher.csvpath.headers:
            if _.strip() == h:
                return True
        return False

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
            msg = self.decorate_error_message(
                f"Cannot parse date '{adate}' using '{aformat}'"
            )
            self.parent.raise_if(ChildrenException(msg), cause=e)
            return None

    def _from_header_if(self, skip=None, quiet=False):
        v = self.resolve_value(skip=skip, quiet=quiet)
        if not v:
            return None
        fmt = self._value_two(skip=skip)
        ret = None
        if fmt:
            ret = self._date_from_strings(v, fmt)
        else:
            ret = ExpressionUtility.to_datetime(v)
        return ret

    def _decide_match(self, skip=None) -> None:
        #
        # if we're deciding a match and we have a term we'll be reffing a header
        #
        """
        t = self._child_one()
        if isinstance(t, Term):
            v = self._from_header(skip=skip)
            self.match = ExpressionUtility.is_date_type(v)
        else:
        """
        self.match = self.to_value(skip=skip) is not None
