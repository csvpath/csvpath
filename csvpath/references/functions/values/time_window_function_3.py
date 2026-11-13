from datetime import datetime

from ..function_3 import Function3


class TimeWindowFunction3(Function3):
    """shared base for compendium 6.27's time component functions that
    can also act as a date-range context setter (riding bare in a
    chain, e.g. ":yesterday():last()") or as a nested anchor argument
    to :from()/:to()/:before()/:after() (e.g. ":from(:year())") --
    added 2026-10-17.

    Each subclass implements start_datetime/end_datetime -- the first
    and last moment (both naive, UTC wall-clock -- see DateUtility's
    own always-UTC `now()`; tzinfo is stripped so these compare cleanly
    against RESULTS' run-directory-derived datetimes, which never carry
    an offset at all, see ResultsReferenceFinder3._run_dir_datetime())
    of the calendar period this function represents, at its own
    granularity (a whole year for :year(), a whole day for :today(), a
    single second for :second(), etc.). The two differ for any
    granularity coarser than its own finest unit (:year()'s start is
    Jan 1 00:00:00, its end is Dec 31 23:59:59.999999) and are equal
    only in the sense that a function with no finer sub-unit (i.e.
    :second() itself) still spans a full second, not a true instant --
    there is deliberately no zero-width case.

    Not :now() (an exact instant, never given the three-role context-
    setter/anchor/value treatment in the compendium -- 6.27g describes
    only its VALUE role) and not :month_name()/:day_name() (a bare name
    with no year attached has no single absolute date to anchor to) --
    those three stay plain SOURCE == "clock" VALUE functions, extending
    Function3 directly, unchanged.

    As an anchor of a directional function it is its first moment
    (compendium 6.27b; 6.27g: "the first moment of the day prior when
    used as a direction anchor"):
        :from(X)   keeps candidates >= X.start_datetime
        :to(X)     keeps candidates <= X.start_datetime
        :before(X) keeps candidates <  X.start_datetime
        :after(X)  keeps candidates >  X.start_datetime
    So ':to(:date("2026-01-31"))' "effectively misses one day", and
    ':after()' of a day needs that day's last moment to mean after it
    (normative examples; David, review item 7, 2026-10-31: "the specs
    are in consistent agreement, so the code is wrong"). Until
    2026-11-12 ':to()' and ':after()' used X.end_datetime, a four-way
    rule confirmed 2026-10-17 (decision D8). Bare and standalone, with
    no directional function, it is its whole window, start to end."""

    def start_datetime(self) -> datetime:
        raise NotImplementedError(
            f":{self.NAME}() does not implement start_datetime()."
        )

    def end_datetime(self) -> datetime:
        raise NotImplementedError(
            f":{self.NAME}() does not implement end_datetime()."
        )
