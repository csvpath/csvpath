# pylint: disable=C0114
from datetime import timedelta, date, datetime, timezone
from dateutil.relativedelta import relativedelta
from csvpath.matching.productions import Term, Variable, Header, Reference
from csvpath.matching.functions.function import Function
from csvpath.matching.util.exceptions import ChildrenException, MatchException
from ..args import Args
from ..function_focus import ValueProducer


class Roll(ValueProducer):
    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
            Rolls a date or datetime forward or backwards by a number of units.

            The units accepted are: seconds, minutes, hours, days, months, years.
            Both singular and plural forms are accepted.
            """
            ),
        ]
        self.value_qualifiers.append("notnone")
        self.args = Args(matchable=self)
        a = self.args.argset(3)

        a.arg(
            name="date",
            types=[Function, Header, Variable, Reference],
            actuals=[None, date, datetime],
        )
        a.arg(
            name="how_many",
            types=[Function, Header, Variable, Reference, Term],
            actuals=[int],
        )
        a.arg(name="unit", types=[Term], actuals=[str])

        self.args.validate(self.siblings())
        #
        # at this point we know we have a units Term. and we know it's not None.
        # and we know we're not going to do this check again, so we don't care
        # about skips.
        #
        v = self._child_three()
        units = v.to_value(skip=None)
        if units not in [
            "year",
            "month",
            "day",
            "hour",
            "minute",
            "second",
        ] and units not in ["years", "months", "days", "hours", "minutes", "seconds"]:
            msg = "Units must be one of years, months, days, hours, minutes, or seconds"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise:
                raise ChildrenException(msg)
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        d = self._value_one(skip=skip)
        if d is None:
            if self.notnone is True:
                msg = "Value cannot be empty because notnone is set"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)
            self.value = None
            return
        roll = self._value_two(skip=skip)
        units = self._value_three(skip=skip)

        if isinstance(d, datetime):
            d = d.replace(tzinfo=timezone.utc)
        if units in ["second", "seconds"]:
            self.value = d + timedelta(seconds=roll)
        elif units in ["minute", "minutes"]:
            self.value = d + timedelta(minutes=roll)
        elif units in ["hour", "hours"]:
            self.value = d + timedelta(hours=roll)
        elif units in ["day", "days"]:
            self.value = d + timedelta(days=roll)
        elif units in ["month", "months"]:
            self.value = d + relativedelta(months=roll)
        elif units in ["year", "years"]:
            self.value = d + relativedelta(years=roll)

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()  # pragma: no cover
