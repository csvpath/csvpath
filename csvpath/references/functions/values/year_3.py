from datetime import datetime

from ...reference_3 import Reference3
from ..function_3 import Function3
from .time_window_function_3 import TimeWindowFunction3
from csvpath.util.date_util import DateUtility as daut


class Year3(TimeWindowFunction3):
    #
    # compendium 5.29's "dumb value-producing functions" -- the first
    # of ten, added 2026-08-26. SOURCE == "clock" (function_3.py's own
    # docstring): never stored anywhere, no dependency on any resolved
    # entity/reference state, computed purely from the current moment.
    # Datatype-independent, like :log() -- usable as a name_one path
    # segment (e.g. "$acme.files.orders/:year()" -> "acme/orders/2026",
    # see ReferenceFinder3._compile_path_pattern()) or inside "{...}"
    # string interpolation (e.g. ':name("partner-{:year()}-orders")',
    # see InterpolatedString3's own evaluation).
    #
    # DateUtility (csvpath/util/date_util.py, aliased "daut" per the
    # project's own utility-alias convention) is the framework's
    # already-established single source of "now" -- same one
    # Metadata.set_time() etc. use -- rather than calling datetime.now()
    # directly here. Bonus: DateUtility.OFFSET_DAYS/MONTHS/YEARS give
    # every one of these ten functions a free, deterministic test hook
    # with no datetime mocking needed.
    #
    # Extends TimeWindowFunction3 (added 2026-10-17, compendium 6.27) --
    # also usable bare in a chain (e.g. ":yesterday():last()", extended
    # here to ":year():last()") as a context setter narrowing the
    # candidate pool to this function's own period, or nested as an
    # anchor argument to :from()/:to()/:before()/:after() (e.g.
    # ":from(:year())"). ROLE stays VALUE, deliberately NOT changed to
    # CONTEXT_SETTER -- a first attempt tried that and broke this very
    # function's own, pre-existing, compendium-explicit VALUE usage
    # (6.42's own worked example, ":name(\"partner-{:year()}-orders\")")
    # since reference_3.py's interpolation check hard-requires ROLE ==
    # VALUE. ROLE is one static attribute per function (the bucket
    # list's own "ROLE is currently static... never usage-dependent"
    # gap), so it cannot encode both roles at once -- the new bare-
    # context-setter/anchor capability is detected structurally
    # instead, via isinstance(f, TimeWindowFunction3), wherever a
    # finder processes a chain or a directional function's own arg.
    #
    NAME = "year"
    SUMMARY = (
        "The current year, e.g. 2026 -- computed from the clock, not "
        "any resolved entity. Also usable as a date-range context "
        "setter/anchor -- see TimeWindowFunction3."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "clock"
    #
    # POSITIONS added 2026-10-17 alongside the bare-context-setter
    # capability -- same positions From3/To3/Before3/After3 already
    # occupy (the places a date-range bound is meaningful). Without
    # this, _check_position() rejects a bare ":year()" riding in the
    # chain outright, even though nothing else about this class changed
    # -- a function with no POSITIONS entry was previously only legal
    # as a name_one path segment or {...} interpolation span, neither
    # of which goes through _check_position() at all.
    #
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }

    def compute(self) -> int:
        return daut.now().year

    def start_datetime(self) -> datetime:
        now = daut.now().replace(tzinfo=None)
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    def end_datetime(self) -> datetime:
        now = daut.now().replace(tzinfo=None)
        return now.replace(
            month=12, day=31, hour=23, minute=59, second=59, microsecond=999999
        )
