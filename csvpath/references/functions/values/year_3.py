from ...reference_3 import Reference3
from ..function_3 import Function3
from csvpath.util.date_util import DateUtility as daut


class Year3(Function3):
    #
    # compendium 5.29's "dumb value-producing functions" -- the first
    # of ten, added 2026-08-26. SOURCE == "clock" (function_3.py's own
    # docstring): never stored anywhere, no dependency on any resolved
    # entity/reference state, computed purely from the current moment.
    # Datatype-independent, like :log() -- these are meant to be used
    # as a name_one path segment (e.g. "$acme.files.orders/:year()"
    # -> "acme/orders/2026", see ReferenceFinder3._compile_path_
    # pattern()) or inside "{...}" string interpolation (e.g.
    # ':name("partner-{:year()}-orders")', see InterpolatedString3's
    # own evaluation) -- not resolved as a bare, standalone reference
    # on their own (no POSITIONS declared, same precedent as :date()/
    # :idchain(), which are also argument-only/nested-only VALUE
    # wrappers).
    #
    # DateUtility (csvpath/util/date_util.py, aliased "daut" per the
    # project's own utility-alias convention) is the framework's
    # already-established single source of "now" -- same one
    # Metadata.set_time() etc. use -- rather than calling datetime.now()
    # directly here. Bonus: DateUtility.OFFSET_DAYS/MONTHS/YEARS give
    # every one of these ten functions a free, deterministic test hook
    # with no datetime mocking needed.
    #
    NAME = "year"
    SUMMARY = "The current year, e.g. 2026 -- computed from the clock, not any resolved entity."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "clock"

    def compute(self) -> int:
        return daut.now().year
