import re

from ...reference_3 import Reference3, Regex3
from ...reference_exceptions_3 import ReferenceException3
from ..function_3 import Function3


class RegexSelector3(Function3):
    #
    # root_major-only selector -- added 2026-08-27 (deferred-work
    # bucket-list entry, "grammar / argument-type gaps": "root_major
    # does not accept a :regex(...) function"). Selects among distinct
    # named-files/named-paths groups/named-results groups THEMSELVES by
    # matching their own registered NAME against a pattern -- root_
    # major's own job (which entities are we even talking about), not a
    # path segment WITHIN one already-chosen entity the way Name3's own
    # Regex3 support is. Motivating case (David, 2026-08-27): a crowded
    # named-files/named-paths/named-results area -- "acme_orders",
    # "acme_invoices", "acme_shipping", and the same again for another
    # partner, e.g. "abba_invoices" -- is more manageable when a
    # reference can target "/abba_.*/" vs "/acme_.*/" directly, instead
    # of enumerating every exact name.
    #
    # Design settled 2026-08-27, before building (David):
    # - Function-only, no bare "/pattern/" form at root_major -- see
    #   reference_grammar_3.py's own note on why (consistent with the
    #   grammar's existing invariant that REGEX only ever appears inside
    #   an argument, never occupying a whole grammatical slot on its
    #   own).
    # - Symmetric across all three datatypes, not FILES-only -- the
    #   crowded-namespace motivation applies identically to named-paths/
    #   named-results groups.
    # - Composes with '*' traversal machinery: "every named-file/group
    #   whose name matches this pattern" is the SAME candidate-gathering
    #   each finder's own _query_star_traversal()/_discover_run_homes()
    #   already does for '*', just pre-filtered by the pattern before
    #   enumeration -- not a new traversal mode. See each finder's own
    #   query()/_query_star_traversal() for where that filter is
    #   actually applied.
    #
    # ARG_TYPES accepts a plain str too, not just Regex3 -- unlike
    # Name3 (where a plain str means "exact literal match", a different
    # thing from its Regex3 case), :regex()'s whole point is pattern
    # matching, so a plain str arg here IS the pattern, treated
    # identically to a Regex3's own .pattern (this also makes
    # :regex(@aregex) actually usable: a caller registering a variable
    # via set_variable() most naturally hands over a plain Python
    # string, not a v3-internal Regex3 instance -- see the "@variable as
    # some other function's own direct argument" done-list entry).
    #
    # ROLE is CONTEXT_SETTER, not POINTER -- mirrors Having3 exactly:
    # narrows the candidate NAME set without resolving to exactly one
    # entity.
    #
    NAME = "regex"
    SUMMARY = (
        "Selects among distinct named-files/named-paths groups/named-"
        "results groups by matching their own name against a pattern -- "
        "root_major only."
    )
    ROLE = Function3.CONTEXT_SETTER
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = (str, Regex3)
    ARG_REQUIRED = True
    POSITIONS = {
        Reference3.FILES: (Reference3.ROOT_MAJOR,),
        Reference3.CSVPATHS: (Reference3.ROOT_MAJOR,),
        Reference3.RESULTS: (Reference3.ROOT_MAJOR,),
    }

    def check_valid(self) -> None:
        """same ARG_TYPES/ARG_REQUIRED check every function gets, plus
        an eager regex-syntax check regardless of whether the arg is a
        Regex3 or a plain str (both are real patterns here, unlike
        Name3's own str-means-something-different case) -- fail at
        build time, not later, deep inside name matching, the first
        time a candidate name happens to be compared against it."""
        super().check_valid()
        pattern = self._arg.pattern if isinstance(self._arg, Regex3) else self._arg
        if isinstance(pattern, str):
            try:
                re.compile(pattern)
            except re.error as e:
                raise ReferenceException3(f":regex() pattern is invalid: {e}") from e

    @property
    def pattern(self) -> str:
        """the raw regex pattern string, regardless of whether the arg
        was written as a Regex3 (/pattern/) or a plain str
        ("pattern"/@variable) -- callers (each finder's own query())
        need this uniformly, without caring which form was used."""
        return self._arg.pattern if isinstance(self._arg, Regex3) else self._arg
