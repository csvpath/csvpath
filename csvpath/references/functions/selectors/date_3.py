from datetime import datetime

from ...reference_3 import Reference3
from ...reference_exceptions_3 import ReferenceException3
from ..function_3 import Function3
from ..values.time_window_function_3 import TimeWindowFunction3


class Date3(TimeWindowFunction3):
    #
    # a literal calendar date, added 2026-08-13 as :from()/:to()'s
    # date-mode bound -- David: "arrival and run order is even more
    # important than indexing." DATE-only granularity for this pass
    # (a plain "YYYY-MM-DD" string, compared against a run's own
    # arrival date) -- hour/minute-level filtering is handled by its
    # new TimeWindowFunction3 siblings (:hour()/:minute()/:second(),
    # added 2026-10-17) instead of extending :date() itself; :date()
    # stays day-granular, matching its own literal "YYYY-MM-DD" arg.
    #
    # Now also usable bare in a chain (e.g.
    # "$acme.files.:date(\"2025-01-01\")", every registration on that
    # day) or nested as a directional anchor, same as its siblings --
    # see TimeWindowFunction3, added 2026-10-17 (compendium 6.27). ROLE
    # stays VALUE, NOT CONTEXT_SETTER -- see year_3.py's own comment
    # for why (6.42's interpolation role check hard-requires VALUE; the
    # new bare-context-setter/anchor capability is detected
    # structurally via isinstance(f, TimeWindowFunction3) instead).
    # Still gives the same result nested as a bare date string did
    # before (":from(:date('2025-01-01'))" == ":from('2025-01-01')") --
    # unaffected either way, see From3's own ARG_TYPES comment for why
    # both shapes stay accepted.
    #
    # DATATYPES widened 2026-08-13's own (Reference3.RESULTS,) scope was
    # too narrow -- corrected 2026-10-17: FILES/CSVPATHS already accept
    # a Date3-wrapped bound via From3/To3/Before3/After3's own ARG_TYPES
    # and already run it through the shared
    # ReferenceFinder3._apply_manifest_date_range(), confirmed live
    # (registration/load time, same "time" manifest field as RESULTS'
    # own runtime) -- this was a real, if previously harmless, gap
    # between this class's own self-reported DATATYPES and what the
    # finders already did with it.
    #
    NAME = "date"
    SUMMARY = (
        "A literal calendar date (YYYY-MM-DD), or the Framework's own "
        "run-dir timestamp form (YYYY-MM-DD_HH-MM-SS) when the time "
        "matters too -- used as :from()'s/:to()'s date-mode bound, "
        "e.g. ':from(:date(\"2025-01-01\"))' for 'runs from this date "
        "onward,' or bare/nested as a date-range context setter/"
        "anchor -- see TimeWindowFunction3."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = (str,)
    ARG_REQUIRED = True
    # POSITIONS added 2026-10-17 -- see year_3.py's own comment for why
    # (a bare chain member, even one that always carries its own
    # required argument like this one, was previously rejected by
    # _check_position() with no POSITIONS entry at all).
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }

    def check_valid(self) -> None:
        super().check_valid()
        # Function3's own generic ARG_TYPES check only confirms the arg
        # IS a str, not that its content is a real calendar date -- a
        # malformed bound would otherwise be silently compared as an
        # ordinary string (or raise a raw, unwrapped ValueError once
        # start_datetime()/end_datetime() are actually called), rather
        # than failing clearly and immediately at construction. Mirrors
        # ReferenceFinder3._validate_date_format() exactly, duplicated
        # rather than shared to avoid a finder<->function circular
        # import (finders import functions, never the reverse).
        try:
            self._window(self._arg)
        except ValueError:
            raise ReferenceException3(
                ":date() requires a real calendar date in 'YYYY-MM-DD' "
                "form, optionally with a time ('YYYY-MM-DD_HH-MM-SS', "
                "the Framework's own run-dir timestamp form -- the "
                f"time is never required), got {self._arg!r}."
            ) from None

    def start_datetime(self) -> datetime:
        return self._window(self._arg)[0]

    def end_datetime(self) -> datetime:
        return self._window(self._arg)[1]

    @staticmethod
    def _window(value: str) -> tuple:
        """(start, end) for a literal date-mode bound -- accepts
        either plain "YYYY-MM-DD" (day granularity, spans the whole
        day) or the Framework's own run-dir timestamp form "YYYY-MM-
        DD_HH-MM-SS" (second granularity, spans just that one second)
        -- the time portion is optional, never required (issue #409:
        David -- v2 references allowed this; the code never caught
        up). Raises ValueError, same as a plain strptime() would, if
        neither form matches -- check_valid() catches it the same way
        it always has. Mirrors ReferenceFinder3._bound_window()
        exactly, duplicated for the same reason check_valid()'s own
        docstring gives."""
        try:
            start = datetime.strptime(value, "%Y-%m-%d_%H-%M-%S")
            return start, start.replace(microsecond=999999)
        except ValueError:
            pass
        start = datetime.strptime(value, "%Y-%m-%d")
        return start, start.replace(hour=23, minute=59, second=59, microsecond=999999)
