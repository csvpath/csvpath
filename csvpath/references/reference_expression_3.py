from .functions.function_3 import Function3
from .functions.reference_function_factory_3 import ReferenceFunctionFactory
from .reference_exceptions_3 import ReferenceException3
from .reference_finder_factory_3 import ReferenceFinderFactory3
from .reference_parser_3 import ReferenceParser3
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
    # UNION's own compatibility check is LHS-driven and purely
    # structural (settled 2026-08-26, see _check_union_compatible) -- if
    # the left side is PATHS, any right side unions freely, by path
    # alone. If the left side is VALUES, the right side's own terminal
    # accessor must be IDENTICAL to the left's (same function name, same
    # argument, via FunctionCall3's own __eq__), not merely "the same
    # kind" or "both produce a uuid" -- comparing the accessors
    # themselves, not the values they resolve to, is what decides
    # comparability; the values are a downstream question, not this
    # class's.
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

    #
    # paths-vs-values compatibility matrix, settled 2026-08-23 (see
    # references_v3_expressions.md's own "paths vs. values sides"
    # section for the full matrix this implements) -- built 2026-08-26,
    # governs INTERSECT/SUBTRACT only (UNION has its own, separate,
    # accessor-equality rule -- see _check_union_compatible and the
    # UNION paragraph in this class's own top comment block).
    # A side is VALUES if its own terminal function chain includes a
    # ROLE == VALUE function (a real scalar lands in .data), or PATHS
    # if it does not (plain path+uuid, .data is always None). Computed
    # statically, from the parsed reference's own terminal_functions
    # (Reference3.terminal_functions), never from resolved data -- a
    # per-item legitimate None (e.g. an optional field absent for one
    # entity) must stay distinct from "this reference structurally has
    # no accessor at all". Checked directly against each function's own
    # ROLE via the registry, not via Reference3.resolve_kind's hardcoded
    # name tuples -- deliberately avoiding adding a second consumer of
    # that already-flagged debt (see the resolve_kind bucket-list entry).
    #
    PATHS = "paths"
    VALUES = "values"

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
            self._check_union_compatible()
            return self._union(left_results, right_results)
        keep = self._op == self.INTERSECT
        right_kind = self._kind(self._right)
        if right_kind == self.PATHS:
            # paths/paths, or values(LHS)/paths(RHS) -- RHS defines the
            # comparison basis either way: identity (path+uuid), never
            # .data. LHS's own .data (if any) is preserved unchanged in
            # the output regardless -- only the comparison basis changes.
            return self._filter_by_identity(left_results, right_results, keep=keep)
        left_kind = self._kind(self._left)
        if left_kind == self.PATHS:
            # paths(LHS)/values(RHS) -- LHS has no value of its own to
            # compare against RHS's, unless RHS's own accessor is
            # specifically uuid-valued, in which case LHS's native uuid
            # (always present, no accessor needed) is the real
            # comparison basis instead.
            if not self._produces_uuid(self._right):
                raise ReferenceException3(
                    f"ReferenceExpression3 {self._op} cannot compare a "
                    "'paths' left side (no value of its own) against a "
                    "'values' right side unless the right side's own "
                    "accessor is uuid-valued (e.g. :uuid()/:run_uuid()/"
                    ":named_file_uuid()/:named_paths_uuid()) -- there is "
                    "otherwise nothing on the left to compare with."
                )
            return self._filter_by_native_uuid(left_results, right_results, keep=keep)
        # values/values -- established behavior, unchanged.
        if self._op == self.INTERSECT:
            return self._intersect(left_results, right_results)
        return self._subtract(left_results, right_results)

    def _resolve_side(self, side: "str | ReferenceExpression3") -> ReferenceResults3:
        if isinstance(side, ReferenceExpression3):
            return side.resolve()
        return ReferenceFinderFactory3.for_reference(
            reference=side, csvpaths=self._csvpaths
        ).resolve()

    def _side_reference_parsed(self, side: "str | ReferenceExpression3"):
        """the single, definitive parsed Reference3 that determines a
        side's own kind (PATHS/VALUES) and PRODUCES_UUID-ness -- for a
        plain reference string, that is just its own parse; for a
        sub-ReferenceExpression3, recurses into ITS OWN left side
        (regardless of that sub-expression's own op) -- INTERSECT/
        SUBTRACT's own output always mirrors left's shape (see this
        module's own docstring), and UNION's own left/right are already
        required (above) to share the same kind, so left is an equally
        valid representative there too. A deliberate simplification for
        the rare case of a deeply-nested sub-expression used as the
        uuid-valued side of an outer paths/values comparison -- not
        exhaustively tracing every possible nesting shape."""
        if isinstance(side, ReferenceExpression3):
            return side._side_reference_parsed(side._left)
        return ReferenceParser3(string=side, csvpaths=self._csvpaths).parsed

    def _kind(self, side: "str | ReferenceExpression3") -> str:
        return (
            self.VALUES if self._terminal_value_call(side) is not None else self.PATHS
        )

    def _terminal_value_call(self, side: "str | ReferenceExpression3"):
        """the first ROLE == VALUE FunctionCall3 in `side`'s own terminal
        chain, or None if the side is PATHS (no such accessor at all).
        Shared by _kind (True/False only) and _check_union_compatible,
        which needs the actual call -- not just whether one exists -- to
        compare accessor identity (name+arg together) via FunctionCall3's
        own __eq__."""
        parsed = self._side_reference_parsed(side)
        for f in parsed.terminal_functions:
            function_cls = ReferenceFunctionFactory.get_registered_class(f.name)
            if function_cls is not None and function_cls.ROLE == Function3.VALUE:
                return f
        return None

    def _check_union_compatible(self) -> None:
        """UNION's own compatibility rule -- LHS-driven, purely
        structural, settled 2026-08-26 directly from David's own "compare
        the accessors, not the value types" proposal: a :uuid() side and
        a :run_uuid() side both produce a uuid, but they are NOT the same
        accessor, so they are not union-compatible under this rule --
        only two sides whose own terminal accessor (function name and
        argument together) are identical qualify, e.g. :uuid()==:uuid()
        or :type()==:type() (a bare :type() vs. another bare :type() is
        accessor-equal even though the two sides' actual resolved values
        may or may not agree -- that is a downstream question, not this
        method's). :type("csv") and :type("xlsx") are NOT accessor-equal
        (different argument), so they would not be union-compatible
        either, if either side's own trailing accessor were :type()
        itself -- in practice :type(...) is normally a mid-chain filter,
        not the terminal accessor, so this rarely applies to it directly.
        If the left side is PATHS (no terminal VALUE-role accessor at
        all), any right side unions freely, by path alone -- this is the
        "RHS added by path" case from the design note."""
        left_call = self._terminal_value_call(self._left)
        if left_call is None:
            return
        right_call = self._terminal_value_call(self._right)
        if right_call != left_call:
            raise ReferenceException3(
                f"ReferenceExpression3 UNION cannot combine the left "
                f"side's accessor {left_call!r} with the right side's "
                f"accessor {right_call!r} -- both sides' own terminal "
                "accessor (function name and argument together) must "
                "match exactly to be comparable."
            )

    def _produces_uuid(self, side: "str | ReferenceExpression3") -> bool:
        parsed = self._side_reference_parsed(side)
        for f in parsed.terminal_functions:
            function_cls = ReferenceFunctionFactory.get_registered_class(f.name)
            if function_cls is not None and function_cls.PRODUCES_UUID:
                return True
        return False

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
    def _filter_by_identity(
        cls, left: ReferenceResults3, right: ReferenceResults3, *, keep: bool
    ) -> ReferenceResults3:
        """paths/paths, or values(LHS)/paths(RHS) -- the right side has
        no value of its own (or its own kind means identity is what
        actually defines membership regardless of the left side's
        kind), so the comparison basis is identity: path+uuid together
        -- path alone is not always enough (e.g. CSVPATHS shares one
        group.csvpath path across every version). `keep=True` is
        INTERSECT (keep matches), `keep=False` is SUBTRACT (keep non-
        matches). The left side's own .data (if any) is preserved
        unchanged in the output regardless -- only the comparison basis
        changed, not the result shape."""
        right_keys = {(item.path, item.uuid) for item in right.results}
        kept = []
        for item in left.deduplicated().results:
            matched = (item.path, item.uuid) in right_keys
            if matched == keep:
                kept.append(item)
        return ReferenceResults3(results=kept)

    @classmethod
    def _filter_by_native_uuid(
        cls, left: ReferenceResults3, right: ReferenceResults3, *, keep: bool
    ) -> ReferenceResults3:
        """paths(LHS)/values(RHS), where the right side's own accessor
        is uuid-valued (Function3.PRODUCES_UUID) -- the left side has
        no value of its own, but its own NATIVE uuid (always present,
        no accessor needed) is compared directly against the right
        side's own .data as a real uuid-to-uuid match. This is what
        makes "every named-file whose uuid intersects the named-file-
        uuids recorded across a set of runs" possible -- a genuine
        cross-datatype capability, not just an edge case."""
        right_keys = cls._keys(right)
        kept = []
        for item in left.deduplicated().results:
            matched = item.uuid is not None and cls._hashable(item.uuid) in right_keys
            if matched == keep:
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
