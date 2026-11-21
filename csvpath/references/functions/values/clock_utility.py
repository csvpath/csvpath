from datetime import datetime

from csvpath.util.date_util import DateUtility as daut

from ...reference_exceptions_3 import ReferenceException3


class ClockUtility:
    """the moment a time function is about (compendium 6.27g; NRE "Date and
    time functions"): now, or the moment its argument gives.

    "Time component functions ... have multiple modes: Returning their
    datetime component based on the datetime.now(); Returning their
    component based on a date passed as an argument; ..." So
    ':day_name(:date("2026-09-04"))' is "Friday" and ':year(:date(
    "2026-01-01"))' is 2026. An int argument is the component's own value:
    ':year(@the_year)' (NRE 102) is that year, ':hour_24(18)' is 18:00
    today. Shared by every time function, the window functions
    (TimeWindowFunction3) and the plain ones (:day_name(), :month_name()).

    All datetimes are naive UTC wall-clock, as TimeWindowFunction3's own
    docstring explains."""

    @staticmethod
    def is_moment(value) -> bool:
        """true when `value` is a built time function that names a moment:
        a window function (its first moment) or ':now()'"""
        #
        # imported here: both modules import this one
        #
        from .time_window_function_3 import TimeWindowFunction3

        return isinstance(value, TimeWindowFunction3) or (
            getattr(value, "NAME", None) == "now"
        )

    @classmethod
    def moment(cls, *, function) -> datetime:
        """the moment a built time function names: a window function's
        first moment (6.27b), or now for ':now()'"""
        if function is None:
            raise ValueError("function cannot be None")
        if not cls.is_moment(function):
            raise TypeError(f"{function!r} is not a time function")
        if getattr(function, "NAME", None) == "now":
            return cls.now()
        return function.start_datetime()

    @staticmethod
    def now() -> datetime:
        return daut.now().replace(tzinfo=None)

    @classmethod
    def base(cls, *, function, component: "str | None" = None) -> datetime:
        """the moment `function` computes from: now with no argument; the
        argument's moment for a time function argument; now with its
        `component` field set for an int argument. A string argument (a
        format string, :yesterday()/:today()) leaves the moment at now."""
        if function is None:
            raise ValueError("function cannot be None")
        arg = function.arg
        if arg is None or isinstance(arg, str):
            return cls.now()
        if cls.is_moment(arg):
            return cls.moment(function=arg)
        if isinstance(arg, bool) or not isinstance(arg, int):
            raise ReferenceException3(
                f":{function.NAME}() takes a time function, e.g. "
                f':{function.NAME}(:date("2026-01-02")), not {arg!r}.'
            )
        if component is None:
            raise ReferenceException3(
                f":{function.NAME}() takes a time function argument, e.g. "
                f':{function.NAME}(:date("2026-01-02")), not an int.'
            )
        try:
            return cls.now().replace(**{component: arg})
        except ValueError:
            raise ReferenceException3(
                f":{function.NAME}({arg}) is not a real {component} here (now is "
                f"{cls.now().isoformat(timespec='seconds')})."
            ) from None
