from ...reference_3 import Reference3
from ..function_3 import Function3
from .predicate_function_3 import PredicateFunction3


class True3(PredicateFunction3):
    #
    # compendium 5.31's "predicate support functions" -- the first of
    # six missing ones (:having() already existed; :not_none()/:regex()
    # are tracked/built elsewhere). ROLE is VALUE, matching Idchain3's
    # own reasoning: this does not narrow/select anything itself, it is
    # a value fed to whatever function's own filtering logic it is
    # nested inside (currently only :idchain(), see Idchain3.matches()
    # -- added 2026-08-26; the generic "any field accessor accepts a
    # predicate argument" mechanism, e.g. :on_arrival(:not_none()), is
    # separate, bigger, still-undesigned follow-up work, tracked
    # independently on the bucket list). DATATYPES is every datatype on
    # purpose, even though the one consumer wired up so far is RESULTS-
    # only -- nothing about matching a JSON true is datatype-specific.
    #
    NAME = "true"
    SUMMARY = "Matches the JSON true / Python True value -- a predicate argument, not usable on its own."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False

    def matches(self, value) -> bool:
        return value is True
