from datetime import datetime

from csvpath.util.date_util import DateUtility as daut

from ...reference_exceptions_3 import ReferenceException3, ReferenceRuntimeException3


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

    #
    # the coarser fields an int component resets first, so a day or month
    # that exists today cannot make another month or year impossible:
    # ':month(2)' on 30 January, ':year(2025)' on 29 February 2028
    # (reviewer on #788). The component's own window ignores them.
    #
    RESETS = {"year": {"month": 1, "day": 1}, "month": {"day": 1}}

    @staticmethod
    def is_moment(value) -> bool:
        """true when `value` is a built time function that names a moment:
        a window function (its first moment) or ':now()'"""
        #
        # imported here: both modules import this one
        #
        from .now_3 import Now3
        from .time_window_function_3 import TimeWindowFunction3

        return isinstance(value, (TimeWindowFunction3, Now3))

    @classmethod
    def moment(cls, *, function) -> datetime:
        """the moment a built time function names: a window function's
        first moment (6.27b), or now for ':now()'"""
        if function is None:
            raise ValueError("function cannot be None")
        if not cls.is_moment(function):
            raise TypeError(f"{function!r} is not a time function")
        if function.NAME == "now":
            return cls.now()
        return function.start_datetime()

    @staticmethod
    def now() -> datetime:
        return daut.now().replace(tzinfo=None)

    @classmethod
    def base(cls, *, function, component: "str | None" = None) -> datetime:
        """the moment `function` computes from: now with no argument; the
        argument's moment for a time function argument; now with its
        `component` field set for an int argument, or a string of digits,
        as an @variable taken from data usually is (NRE 102
        ':year(@the_year)'). Any other string is a format (:yesterday(),
        :today()) and leaves the moment at now."""
        if function is None:
            raise ValueError("function cannot be None")
        arg = function.arg
        if arg is None:
            return cls.now()
        if isinstance(arg, str):
            if component is None:
                return cls.now()
            if not arg.strip().isdigit():
                raise ReferenceException3(
                    f":{function.NAME}() takes a time function or a number, "
                    f"not {arg!r}."
                )
            arg = int(arg.strip())
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
        now = cls.now()
        try:
            return now.replace(**cls.RESETS.get(component, {})).replace(
                **{component: arg}
            )
        except ValueError:
            where = {"day": f" in {now.strftime('%B %Y')}"}.get(component, "")
            raise ReferenceException3(
                f":{function.NAME}({arg}) is not a valid {component}{where}."
            ) from None

    @staticmethod
    def check_format(*, function, value) -> None:
        """a :yesterday()/:today() string is a strftime format. One with no
        '%' would come back unchanged, so a date there is a silent wrong
        answer: it raises. Checked on the literal when the function is
        built and again on a resolved @variable or "{...}" value, which is
        only known later (reviewer on #788)."""
        if function is None:
            raise ValueError("function cannot be None")
        if isinstance(value, str) and "%" not in value:
            raise ReferenceRuntimeException3(
                f":{function.NAME}() takes a format string, e.g. "
                f':{function.NAME}("%A"), and got {value!r}; for a day '
                f'relative to a date use :{function.NAME}(:date("YYYY-MM-DD")).'
            )
