import re

from ...reference_3 import Reference3
from ..function_3 import Function3


class ChoiceSelector3(Function3):
    #
    # root_major-only selector, same job RegexSelector3 already does --
    # compendium 3.9c/"Functions in root_major": "a pipe-delimited
    # sequence of matching names," e.g. ':choice("orders|invoices|
    # shipments")'. Never a registered function at all until now (first
    # of the 30 "does not yet support" sites catalogued 2026-10-20 --
    # this one is reference_finder_3.py's own "Does not yet support :X()
    # as a name_one path segment," since :choice() is explicitly listed
    # there, compendium 3.9c, as a path-segment-occupying pattern-
    # matching analog of :name()/:regex()).
    #
    # Compiles down to an anchored, each-alternative-escaped regex
    # alternation via its own .pattern property -- each name is
    # re.escape()d so it is compared as a LITERAL string, not
    # interpreted as a sub-pattern (a named-file called "a.b" must only
    # match the literal "a.b", not "a.b" as "a", any char, "b"). This
    # lets :choice() reuse :regex()'s own already-built root_major
    # dispatch/_compile_path_pattern/_is_traversal_root/_matching_names
    # machinery entirely UNCHANGED -- every one of those already just
    # reads whatever function was built's own `.pattern`, with no
    # per-function special-casing beyond "is this a recognized
    # function's own instance" -- so ':choice("orders|invoices")' and
    # ':regex("^(orders|invoices)$")' are, once built, literally
    # equivalent, matching the compendium's own framing of both as
    # "pattern-matching analogs of :name()".
    #
    NAME = "choice"
    SUMMARY = (
        "Selects among distinct named-files/named-paths groups/named-"
        "results groups (root_major), or a name_one path segment, by "
        "exact match against a pipe-delimited list of names -- e.g. "
        "':choice(\"orders|invoices|shipments\")'."
    )
    ROLE = Function3.CONTEXT_SETTER
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = (str,)
    ARG_REQUIRED = True
    POSITIONS = {
        Reference3.FILES: (Reference3.ROOT_MAJOR,),
        Reference3.CSVPATHS: (Reference3.ROOT_MAJOR,),
        Reference3.RESULTS: (Reference3.ROOT_MAJOR,),
    }

    @property
    def names(self) -> list:
        """the raw, un-escaped alternative names, trimmed of
        surrounding whitespace -- e.g. "a | b|c" -> ["a", "b", "c"]."""
        return [n.strip() for n in self._arg.split("|")]

    @property
    def pattern(self) -> str:
        """an anchored regex alternation matching exactly one of
        .names, each escaped so it is compared as a literal string --
        see this class's own top-of-file comment for why this alone
        is the whole implementation."""
        return "^(" + "|".join(re.escape(n) for n in self.names) + ")$"
