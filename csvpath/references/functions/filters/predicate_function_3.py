from ..function_3 import Function3


class PredicateFunction3(Function3):
    """shared base for compendium 5.31's predicate-support functions
    (:true()/:false()/:none()/:not_none()/:empty()/:not_empty()) --
    exists so a consuming function (e.g. Idchain3) can declare its own
    ARG_TYPES generically as (..., PredicateFunction3) instead of
    enumerating every concrete predicate class by name one by one,
    matching the project's own declarative-over-hardcoded-list
    preference (see the resolve_kind bucket-list entry) -- a future
    predicate function automatically works with any existing consumer
    without that consumer's own ARG_TYPES needing to change at all.

    Each subclass implements matches(value) -- true if `value` (some
    other function's own content, e.g. an error entry's "source" field)
    satisfies this predicate. Not meant to be instantiated directly."""

    def matches(self, value) -> bool:
        raise NotImplementedError(
            f":{self.NAME}() does not implement matches()."
        )
