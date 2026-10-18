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

    Resolved against four directional rules (David confirmed 2026-10-17,
    reconciling 6.27b's literal "first moment" text against 6.27f's own
    worked example and the already-shipped day-granular :before()/
    :after() "excludes the whole day it names" behavior -- using only
    the first moment does not reproduce either for the exclusive-upper/
    lower cases):
        :from(X)   keeps candidates >= X.start_datetime
        :to(X)     keeps candidates <= X.end_datetime
        :before(X) keeps candidates <  X.start_datetime
        :after(X)  keeps candidates >  X.end_datetime
    and, bare/standalone (no :from()/:to()/:before()/:after() riding
    with it), as the implicit two-sided range this same rule set gives
    for ":from(X):to(X)" -- see ReferenceFinder3._resolve_time_bound()
    and the per-finder date-range filters that consume it."""

    def start_datetime(self) -> datetime:
        raise NotImplementedError(
            f":{self.NAME}() does not implement start_datetime()."
        )

    def end_datetime(self) -> datetime:
        raise NotImplementedError(
            f":{self.NAME}() does not implement end_datetime()."
        )
