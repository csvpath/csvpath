from .reference_exceptions_3 import ReferenceException3
from .reference_finder_factory_3 import ReferenceFinderFactory3
from .reference_results_3 import ReferenceResults3


class ReferenceExpression3:
    #
    # a logical operation (UNION/SUBTRACT/INTERSECT) applied to two
    # references, for questions a single reference cannot answer alone
    # -- see references_notes/notes/reference_expressions_notes.txt for
    # the full worked-through design (SEMANTICS/ARCHITECTURE sections,
    # settled 2026-08-17). Each side is either a plain reference string
    # (dispatched through ReferenceFinderFactory3, so it can be any of
    # the three datatypes) or another ReferenceExpression3
    # (sub-expressions) -- either way, each side is fully resolve()d to
    # its own ReferenceResults3 before the operation combines them.
    #
    # UNION never looks at resolved data at all -- it is pure
    # concatenation of both sides' own native results, with duplicates
    # (by ReferenceResult3's own __eq__) collapsed via
    # ReferenceResults3.deduplicated(). If the caller wants to see which
    # items on one side correlate with which on the other, that is done
    # AFTER the union, by the caller, comparing .data across the merged
    # results themselves -- not something this computes.
    #
    # INTERSECT/SUBTRACT use a join key instead: whatever scalar each
    # side's own trailing field accessor resolved to (result.data,
    # already populated by resolve() -- e.g. :identity(), :uuid(),
    # :named_paths_name()), NOT path/uuid, which mean different things
    # per datatype and are not comparable across them. Both are FILTERS,
    # not joins that multiply rows: a left-hand ITEM survives
    # (INTERSECT) or is dropped (SUBTRACT) based on whether its key
    # exists anywhere on the right, regardless of how many right-hand
    # items share that key.
    #
    # Only the RIGHT side is reduced to a plain set of keys -- which
    # right-hand item carried a given key never matters, since right-
    # hand items never appear in the output, only their key VALUES do.
    # The LEFT side is NOT collapsed by key -- corrected 2026-08-18,
    # caught by testing against David's own "orders" example (two
    # named-paths groups, 2 runs for one, 3 for the other): an earlier
    # draft of this class deduplicated the left side by key too, before
    # filtering, which silently collapsed group A's 2 runs and group
    # B's 3 runs down to 1 each -- wrong, since "give me all the runs"
    # means every matching run, not one exemplar per distinct group
    # name. The left side IS still deduplicated by full ReferenceResult3
    # equality first (dropping true duplicate items, never a different
    # item that merely shares a key) -- that is always safe, regardless
    # of which of these two examples you are in. A caller who genuinely
    # wants "one result per distinct key" output (the overnight-
    # regression example's own goal, not this one) gets that by calling
    # ReferenceResults3.deduplicated() themselves on whichever side
    # needs it before handing it to an expression -- not something this
    # class forces on every INTERSECT/SUBTRACT.
    #
    # A None-valued key never matches anything, on either side -- for
    # INTERSECT that means a None-keyed left item can never be confirmed
    # to match, so it never survives; for SUBTRACT it means a None-keyed
    # left item can never be matched away, so it always survives. A key
    # that is not hashable (e.g. a side's trailing accessor resolved to
    # a list/dict -- :named_paths_identities(), :file_fingerprints(),
    # :scripts()/:webhooks()/:transfers()) raises clearly here rather
    # than failing confusingly deep inside a set.
    #
    # Output is always a flat ReferenceResults3, same shape as a single
    # reference's own results -- each surviving item keeps its own real
    # path/uuid/data intact, in the left-hand side's own original order;
    # nothing pairs/merges two sides' items into one row.
    #
    UNION = "union"
    SUBTRACT = "subtract"
    INTERSECT = "intersect"
    _OPERATIONS = (UNION, SUBTRACT, INTERSECT)

    def __init__(
        self,
        *,
        left: "str | ReferenceExpression3",
        op: str,
        right: "str | ReferenceExpression3",
        csvpaths,
    ) -> None:
        if not isinstance(left, (str, ReferenceExpression3)) or left == "":
            raise ValueError(
                "ReferenceExpression3 left must be a non-empty reference "
                "string or another ReferenceExpression3"
            )
        if op not in self._OPERATIONS:
            raise ValueError(
                f"ReferenceExpression3 op must be one of {self._OPERATIONS}, "
                f"got {op!r}"
            )
        if not isinstance(right, (str, ReferenceExpression3)) or right == "":
            raise ValueError(
                "ReferenceExpression3 right must be a non-empty reference "
                "string or another ReferenceExpression3"
            )
        if csvpaths is None:
            raise ValueError("ReferenceExpression3 csvpaths cannot be None")
        self._left = left
        self._op = op
        self._right = right
        self._csvpaths = csvpaths

    def resolve(self) -> ReferenceResults3:
        left_results = self._resolve_side(self._left)
        right_results = self._resolve_side(self._right)
        if self._op == self.UNION:
            return self._union(left_results, right_results)
        if self._op == self.INTERSECT:
            return self._intersect(left_results, right_results)
        return self._subtract(left_results, right_results)

    def _resolve_side(self, side: "str | ReferenceExpression3") -> ReferenceResults3:
        if isinstance(side, ReferenceExpression3):
            return side.resolve()
        return ReferenceFinderFactory3.for_reference(
            reference=side, csvpaths=self._csvpaths
        ).resolve()

    @staticmethod
    def _union(left: ReferenceResults3, right: ReferenceResults3) -> ReferenceResults3:
        combined = ReferenceResults3(results=[*left.results, *right.results])
        return combined.deduplicated()

    @classmethod
    def _intersect(
        cls, left: ReferenceResults3, right: ReferenceResults3
    ) -> ReferenceResults3:
        right_keys = cls._keys(right)
        kept = []
        for item in left.deduplicated().results:
            if item.data is None:
                continue
            if cls._hashable(item.data) in right_keys:
                kept.append(item)
        return ReferenceResults3(results=kept)

    @classmethod
    def _subtract(
        cls, left: ReferenceResults3, right: ReferenceResults3
    ) -> ReferenceResults3:
        right_keys = cls._keys(right)
        kept = []
        for item in left.deduplicated().results:
            if item.data is None:
                kept.append(item)
                continue
            if cls._hashable(item.data) not in right_keys:
                kept.append(item)
        return ReferenceResults3(results=kept)

    @classmethod
    def _keys(cls, results: ReferenceResults3) -> set:
        """the set of distinct, hashable, non-None join-key values
        present in `results` -- used only to test LEFT-hand membership
        for INTERSECT/SUBTRACT. Which item on this side carried a given
        key never matters here -- see this class's own docstring for
        why RIGHT-hand items themselves never appear in the output."""
        keys = set()
        for item in results.results:
            if item.data is None:
                continue
            keys.add(cls._hashable(item.data))
        return keys

    @staticmethod
    def _hashable(key):
        try:
            hash(key)
        except TypeError:
            raise ReferenceException3(
                f"ReferenceExpression3 cannot use a {type(key).__name__} "
                f"({key!r}) as a join key -- INTERSECT/SUBTRACT need each "
                "side's trailing accessor to resolve to a hashable scalar "
                "(e.g. :identity(), :uuid(), :named_paths_name()), not a "
                "list/dict-valued one."
            ) from None
        return key
