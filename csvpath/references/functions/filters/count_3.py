from ...reference_3 import Reference3
from ..function_3 import Function3
from .predicate_function_3 import PredicateFunction3


class Count3(Function3):
    #
    # the one exception to Idchain3/Message3's own "position decides
    # meaning" contract (compendium 4.13/4.14) -- normative examples
    # 489-491's worked example, ":errors(:count(:above(10)))". Nested
    # as :errors()'s own argument, same position as Idchain3/Message3,
    # but it cannot FILTER errors.json's own entries the way they do:
    # a count is an aggregate over the WHOLE array, there is no
    # per-entry notion of "this one entry's own count." So nested here
    # still means GATE (all-or-nothing on the whole, already-read,
    # unfiltered content), not FILTER -- an explicit, documented
    # exception to the rule, not a new general one (see Errors3's own
    # comment for the two, now three, shapes).
    #
    NAME = "count"
    SUMMARY = (
        "The number of entries in errors.json, tested against a nested "
        "predicate (e.g. ':above(10)') -- only meaningful nested inside "
        ":errors(). Unlike :idchain()/:message(), does not filter which "
        "entries come back; it gates whether the whole, unfiltered list "
        "is returned at all."
    )
    ROLE = Function3.VALUE
    # metadata_kind() override -- same reasoning as Idchain3/Message3's
    # own: no SOURCE of its own, so nothing would otherwise mark a
    # reference containing it METADATA_FIELD (see Function3.RESOLVES_AS's
    # own docstring). Makes no difference to ResultsReferenceFinder3's
    # own dispatch today (it already treats METADATA_FILE/METADATA_FIELD
    # identically for :errors()), kept for correctness of what
    # resolve_kind reports, matching Idchain3/Message3 exactly.
    RESOLVES_AS = Reference3.METADATA_FIELD
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = (PredicateFunction3,)
    ARG_REQUIRED = True

    def matches(self, data: list | None) -> bool:
        """true if `data` (errors.json's own parsed, UNFILTERED entry
        list, or None if the file was never written) satisfies this
        function's own nested predicate once reduced to a count -- a
        missing file counts as zero entries, same treatment as every
        other genuinely-optional well-known file."""
        return self._arg.matches(len(data) if data is not None else 0)
