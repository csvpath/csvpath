# pylint: disable=C0114
from datetime import date, datetime, timezone
from csvpath.matching.productions import Term, Variable, Header, Reference
from csvpath.matching.functions.function import Function
from csvpath.matching.util.exceptions import ChildrenException, MatchException
from csvpath.matching.util.expression_utility import ExpressionUtility as exut
from ..args import Args
from ..function_focus import ValueProducer


class DatePart(ValueProducer):
    def check_valid(self) -> None:
        if self.name not in ["year", "month", "day"]:
            msg = "Function name must be one of year, month, or day"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise:
                raise ChildrenException(msg)
        self.description = [
            self._cap_name(),
            self.wrap(
                f"""\
            A convenience function that returns the {self.name} component of a date
            or datetime as a string.
            """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.argset(1).arg(
            name="date",
            types=[Term, Function, Header, Variable, Reference],
            actuals=[None, date, datetime],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        x = self._value_one(skip=skip)
        if x is None:
            return
        xd = exut.to_datetime(x)
        #
        # exut returns the thing offered if it cannot convert.
        # this would mean a ''.
        #
        if x == xd:
            return
        form = None
        if self.name == "year":
            form = "%Y"
        elif self.name == "month":
            form = "%m"
        elif self.name == "day":
            form = "%d"
        xs = xd.strftime(form)
        self.value = xs

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()  # pragma: no cover


class DateFormat(ValueProducer):
    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """Outputs a date or datetime as a string using strftime formatting.
                If a date format does not include date parts a match error is raised. """
            ),
        ]
        self.value_qualifiers.append("notnone")
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="date",
            types=[Term, Function, Header, Variable, Reference],
            actuals=[None, date, datetime],
        )
        a.arg(
            name="format",
            types=[Term, Function, Header, Variable],
            actuals=[str],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        x = self._value_one(skip=skip)
        if x is None:
            return
        xd = exut.to_datetime(x)
        if x == xd:
            return
        form = self._value_two(skip=skip)
        xs = xd.strftime(form)
        if xs == form:
            msg = "Incorrect date format"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
            self.value = None
            return
        self.value = xs

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()  # pragma: no cover
