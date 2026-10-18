from ...reference_3 import Reference3
from ..function_3 import Function3


class HasErrors3(Function3):
    #
    # mirrors csvpath.managers.results.result.Result.has_errors()
    # (literally `self.errors_count > 0`) -- added 2026-10-18, David:
    # "it seems like it would help a user a good deal to be able to
    # filter or resolve items that have errors, or that don't, without
    # having to use the errors count with boolean logic." Reads the
    # SAME "error_count" manifest field ErrorCount3 does (both run and
    # instance level, see that class's own comment for the per-instance
    # field confirmation) and reduces it to a bool via transform_value()
    # -- cheap (one small manifest field read, no need to open
    # errors.json at all), not built as sugar for ":errors(:count(
    # :above(0)))" despite the two being semantically equivalent (same
    # underlying Error collection, two different persisted
    # representations) -- that composition is exactly the "errors count
    # with boolean logic" David asked NOT to have to write.
    #
    NAME = "has_errors"
    SUMMARY = (
        "True if the run (name_one) or this one csvpath statement's "
        "own instance (name_three) recorded at least one error."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "error_count",
        Reference3.RESULT: "error_count",
    }
    POSITIONS = {
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }

    @classmethod
    def transform_value(cls, value) -> bool:
        """the raw "error_count" int, reduced to a bool -- a missing or
        non-int value (the field is genuinely optional, same treatment
        every other well-known manifest field gets) means "no errors
        recorded," False, not an error of its own."""
        return isinstance(value, int) and value > 0
