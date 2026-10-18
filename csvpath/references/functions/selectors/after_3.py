from ...reference_3 import Reference3
from ...reference_exceptions_3 import ReferenceException3
from ..function_3 import Function3
from ..filters.predicate_function_3 import PredicateFunction3
from ..values.time_window_function_3 import TimeWindowFunction3
from .index_3 import Index3


class After3(PredicateFunction3):
    #
    # the EXCLUSIVE sibling of :from() -- compendium 6.28/6.28b/6.28c,
    # built 2026-10-16. See Before3's own comment for the shared
    # mechanism/alias-registration reasoning; this is the LOWER-bound
    # mirror of it. ":after(5)" starts at position 6, not 5;
    # ":after(:date('2025-01-31'))" excludes runs that arrived ON
    # 2025-01-31 itself, only strictly later ones. Aliased "above"/"gt"
    # (6.28b).
    #
    # 6.28c: combining with :from() (another LOWER bound) is illegal.
    # May pair with :before()/:to() (an UPPER bound) to form a range.
    #
    # Extends PredicateFunction3 (not just Function3), added 2026-10-17
    # -- the ":count(:above(10))" worked example (normative examples
    # 489-491) needs ":above()" to also work as a scalar predicate
    # (count > bound), not just as a range bound narrowing a list. One
    # class serves both roles, "position decides meaning" the same way
    # Idchain3's FILTER/GATE split already does: riding as a range bound
    # (':from()'/':to()' territory) still goes through _apply_range()/
    # _apply_date_range() exactly as before; nested inside :count() goes
    # through matches() instead. No separate predicate class needed --
    # see the deferred_work_bucket_list.md correction, David caught a
    # wrong "naming collision" claim here and this is the actual fix.
    #
    # ARG_TYPES widened 2026-10-17 from Date3 specifically to
    # TimeWindowFunction3 generically (compendium 6.27) -- ":after(
    # :year())"/etc are now equally legal as a RANGE bound, using that
    # function's own end_datetime() as the exclusive lower cutoff (see
    # TimeWindowFunction3's own docstring for the full four-way rule).
    # This is unrelated to this class's OWN separate, scalar-predicate
    # role (matches() below, used nested inside :count()) -- the two
    # roles share this class but not this widening's own reasoning;
    # matches() guards against a non-orderable TimeWindowFunction3 arg
    # being passed to IT (e.g. the nonsensical ":count(:above(:year()
    # ))"), which ARG_TYPES alone cannot distinguish from the
    # legitimate range-bound usage.
    #
    NAME = "after"
    SUMMARY = (
        "The exclusive start of a range over the current scope's "
        "ordered items -- index-mode: from, but NOT including, this "
        "0-based position (negative counts from the end) to the end, "
        "or to :before()'s/:to()'s position if present. date-mode: "
        "from, but not including, this calendar date onward (or the "
        "end of a coarser time-component function's own period, e.g. "
        ":year()/:month()), compared against each run's own arrival "
        "date. Aliases: ':above()'/':gt()'. Nested inside :count() "
        "(e.g. ':count(:above(10))'), acts as a scalar predicate "
        "instead: matches any value strictly greater than its own "
        "bound."
    )
    ROLE = Function3.CONTEXT_SETTER
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = (int, Index3, str, TimeWindowFunction3)
    ARG_REQUIRED = True
    #
    # see From3's own POSITIONS comment -- always paired, same positions.
    #
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }

    def matches(self, value) -> bool:
        """scalar-predicate mode, used nested inside :count() -- true
        if `value` is strictly greater than this function's own bound.
        Same unwrap as ReferenceFinder3._range_bound() (a bare int/str
        leaf, or a nested :index() wrapper's own .arg) -- not reused
        directly to avoid a circular import (that helper lives on the
        finder base class, which imports this function module, not the
        other way around). A TimeWindowFunction3 arg (e.g. the
        nonsensical ":count(:above(:year()))") is rejected clearly here
        rather than crashing on an unwrapped TypeError -- ARG_TYPES
        alone cannot distinguish this from the legitimate range-bound
        usage, since both roles share this one class."""
        bound = self._arg
        if isinstance(bound, TimeWindowFunction3):
            raise ReferenceException3(
                ":above()/:after() cannot compare against "
                f":{bound.NAME}() -- as a predicate (e.g. nested inside "
                ":count()), its bound must be a plain number, not a "
                "time-component function."
            )
        if not isinstance(bound, (int, str)):
            bound = bound.arg
        return value > bound
