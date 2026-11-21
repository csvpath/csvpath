from datetime import datetime, timedelta

from ...reference_exceptions_3 import ReferenceException3
from .clock_utility import ClockUtility as clut
from .time_window_function_3 import TimeWindowFunction3


class DayRelativeFunction3(TimeWindowFunction3):
    """:today() and :yesterday(): a day, DAYS_BACK days before now, or
    before the moment an argument gives (compendium 6.27g: "Any of the
    above three functions relative to a datetime when passed that
    datetime. E.g. ':yesterday(:date("2026-01-02"))' returns the date,
    date range or string beginning at the first moment of 2026-01-01").

    With a time function argument the window runs from the argument's first
    moment, moved back DAYS_BACK days, to the end of that day. A whole-day
    argument gives the whole day (6.27g: "beginning at the first moment of
    2026-01-01"); a finer one keeps its time of day as the start, so
    ':yesterday(:hour(18))' is yesterday from 18:00 on, and as an anchor
    (':from(:yesterday(:hour(18)))', NRE 568, "since close of business
    yesterday") yesterday at 18:00. An argument coarser than a day
    (:year(), :month()) has no single day to move, so it raises.

    A string argument is a format for the date (6.27g: "when passed a
    format string, the formatted date"): ':yesterday("%A")' is yesterday's
    day name. The window stays the whole day. A string with no '%' is
    refused: a date there would come back unchanged, so
    ':yesterday("2026-01-02")' raises and says to use :date()."""

    DAYS_BACK = 0
    # arguments with no single day to move
    TOO_COARSE = ("year", "month")

    def check_valid(self) -> None:
        # these messages say more than the generic type check would
        arg = self._arg
        if isinstance(arg, bool) or isinstance(arg, int):
            raise ReferenceException3(
                f":{self.NAME}() takes a time function or a format string, "
                f'e.g. :{self.NAME}(:date("2026-01-02")) or :{self.NAME}("%A"), '
                f"not {arg!r}."
            )
        if isinstance(arg, str) and "%" not in arg:
            raise ReferenceException3(
                f":{self.NAME}() takes a format string, e.g. "
                f':{self.NAME}("%A"), and got {arg!r}; for a day relative to '
                f'a date use :{self.NAME}(:date("YYYY-MM-DD")).'
            )
        if getattr(arg, "NAME", None) in self.TOO_COARSE:
            raise ReferenceException3(
                f":{self.NAME}(:{arg.NAME}()) has no single day to start from; "
                f'use a day or a finer time, e.g. :{self.NAME}(:date("2026-01-02")).'
            )
        super().check_valid()

    def check_resolved(self) -> None:
        clut.check_format(function=self, value=self.arg)

    def _window(self) -> tuple:
        arg = self.arg
        if isinstance(arg, TimeWindowFunction3):
            start = arg.start_datetime()
            end = start.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            # no argument, a format string, or ':now()': the day of now. An
            # instant has no window of its own to move, and "relative to a
            # datetime" is that datetime's day (6.27g's ':yesterday(:date(
            # "2026-01-02"))' is the whole of 2026-01-01), so
            # ':yesterday(:now())' is ':yesterday()'.
            now = clut.moment(function=arg) if clut.is_moment(arg) else clut.now()
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        back = timedelta(days=self.DAYS_BACK)
        return start - back, end - back

    def compute(self) -> str:
        clut.check_format(function=self, value=self.arg)
        start = self._window()[0]
        if isinstance(self.arg, str):
            return start.strftime(self.arg)
        return start.date().isoformat()

    def start_datetime(self) -> datetime:
        clut.check_format(function=self, value=self.arg)
        return self._window()[0]

    def end_datetime(self) -> datetime:
        return self._window()[1]
