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

    With a time function argument the window is the argument's own window,
    moved back DAYS_BACK days, so a finer argument keeps its precision:
    ':yesterday(:hour_24(18))' is 18:00-18:59 yesterday, and as an anchor
    (':from(:yesterday(:hour_24(18)))', NRE "since close of business
    yesterday") its first moment, yesterday at 18:00. An argument coarser
    than a day (:year(), :month()) has no single day to move, so it raises.

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
                f":{self.NAME}({arg!r}) takes a format string, e.g. "
                f':{self.NAME}("%A"); for a day relative to a date use '
                f":{self.NAME}(:date({arg!r}))."
            )
        if getattr(arg, "NAME", None) in self.TOO_COARSE:
            raise ReferenceException3(
                f":{self.NAME}(:{arg.NAME}()) has no single day to start from; "
                f'use a day or a finer time, e.g. :{self.NAME}(:date("2026-01-02")).'
            )
        super().check_valid()

    def _window(self) -> tuple:
        arg = self.arg
        if isinstance(arg, TimeWindowFunction3):
            start, end = arg.start_datetime(), arg.end_datetime()
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
        start = self._window()[0]
        if isinstance(self.arg, str):
            return start.strftime(self.arg)
        return start.date().isoformat()

    def start_datetime(self) -> datetime:
        return self._window()[0]

    def end_datetime(self) -> datetime:
        return self._window()[1]
