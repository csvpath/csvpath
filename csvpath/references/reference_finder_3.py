import os
import re
from abc import ABC, abstractmethod
from datetime import datetime

from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos

from .functions.function_3 import Function3
from .functions.filters.predicate_function_3 import PredicateFunction3
from .functions.reference_function_factory_3 import ReferenceFunctionFactory
from .functions.selectors.name_3 import Name3
from .functions.values.time_window_function_3 import TimeWindowFunction3
from .reference_3 import (
    FunctionCall3,
    InterpolatedString3,
    Reference3,
    Regex3,
    Star3,
    Variable3,
)
from .reference_exceptions_3 import ReferenceException3, ReferenceRuntimeException3
from .reference_parser_3 import ReferenceParser3
from .reference_results_3 import ReferenceResult3, ReferenceResults3
from .sources.filesystem_reference_source import FilesystemReferenceSource
from .sources.reference_source import ReferenceSource


class ReferenceFinder3(ABC):
    #
    # one concrete subclass per v3 reference datatype (files, csvpaths,
    # results) -- each datatype's storage layout differs enough (files:
    # SHA256-named version files; csvpaths: manifest-array-index
    # versions; results: run-directory versions) that query() has no
    # generic implementation and is left abstract. resolve()/
    # resolve_from() are shared here: "call query(), then maybe extract
    # a value" is the same shape regardless of datatype.
    #
    def __init__(
        self, *, csvpaths, ref: ReferenceParser3, variables: dict | None = None
    ) -> None:
        if csvpaths is None:
            raise ValueError("Csvpaths cannot be None")
        if ref is None:
            raise ValueError("Reference cannot be None")
        self._csvpaths = csvpaths
        self._ref = ref
        #
        # compendium 3.12: "prior to query, a reference finder can be
        # given variables that may be used in references... a variable
        # can be any Python object, but the variable value will be put
        # into a string context so its __str__ must make sense."
        # Registration is deliberately simple and explicit -- a plain
        # {name: value} mapping the caller hands the finder, not a
        # lookup into any live CsvPath instance's own runtime variables
        # (those are scoped to one running statement, which does not
        # exist at all when a reference is resolved standalone -- v3
        # is not wired into production yet, see the bucket list). Added
        # 2026-08-26, added alongside @variable's first real consumer,
        # "{...}" interpolation (see _resolve_value()) -- usability as
        # some OTHER function's own direct argument is a separate,
        # still-open question, not addressed by this.
        #
        self._variables: dict = dict(variables) if variables else {}
        self._source: ReferenceSource | None = None
        # the 5.20b ambiguity warnings this finder has already logged; one
        # resolve() reads the same chain once per result (2026-11-13)
        self._warned: set = set()

    @property
    def source(self) -> ReferenceSource:
        """where manifests, ledgers, names and run homes are read from.
        every such read goes through here; see ReferenceSource."""
        if self._source is None:
            #
            # a CsvPaths chooses its source by [references] sql. getattr
            # because finders also run over duck-typed stand-ins (e.g. test
            # fakes) that only have the managers; those read the filesystem.
            #
            source = getattr(self._csvpaths, "reference_source", None)
            if source is None:
                source = FilesystemReferenceSource(csvpaths=self._csvpaths)
            self._source = source
        return self._source

    @property
    def ref(self) -> ReferenceParser3:
        return self._ref

    @property
    def csvpaths(self):
        return self._csvpaths

    @property
    def variables(self) -> dict:
        return self._variables

    def set_variable(self, name: str, *, value) -> None:
        """registers one @name -> value mapping, usable inside "{...}"
        interpolation once this finder resolves a reference containing
        it. Callable any time before resolve() actually needs the
        value -- see __init__'s own docstring comment for the design."""
        if not name:
            raise ValueError("name cannot be None or empty")
        self._variables[name] = value

    def set_variables(self, variables: dict) -> None:
        """bulk form of set_variable() -- merges `variables` into
        whatever is already registered, rather than replacing it."""
        if variables is None:
            raise ValueError("variables cannot be None")
        self._variables.update(variables)

    @abstractmethod
    def query(self) -> ReferenceResults3:
        """finds the path+uuid of everything this reference matches.
        does not fetch any data -- see resolve()/resolve_from()."""

    def resolve(self) -> ReferenceResults3:
        """query(), then resolve every result found. for a caller that
        wants to narrow down first, see resolve_from()."""
        return self.resolve_from(self.query())

    def resolve_from(self, selection: ReferenceResults3 | list) -> ReferenceResults3:
        """
        resolves a selection rather than always re-querying and
        resolving everything -- this is what keeps "cheap search, then
        selective fetch" real: a caller can query(), narrow down
        externally (or just eyeball the paths/uuids), and only pay for
        resolving the part they actually want.

        selection is either a ReferenceResults3 (resolve all of it) or
        a list[str | UUID] of specific paths/uuids to pull out of a
        fresh query() first.

        Rule 1 (manifest_field_functions_proposal.md's "Entity
        resolution and pooling" section) -- reading a whole-resource
        content accessor (:manifest(), :definition(), :errors(), etc.)
        always touches exactly one entity -- is enforced HERE, not in
        query(), as of 2026-08-26 (see the ":path()" retirement/Rule 1
        bucket-list entry). query() is always allowed to return more
        than one match, regardless of which accessor is present; a
        finder's own query() instead flags the ReferenceResults3 it
        returns (ReferenceResults3.ambiguous_content_read) when it found
        more than one raw, unreduced candidate for such an accessor with
        no pointer to pick one -- deliberately NOT a generic "is the
        final count > 1" check computed here: a pointer applied WITHIN
        each of several matched entities (e.g. ':all():last():manifest()'
        across several named-paths groups, one manifest entry per group)
        is perfectly legitimate even though the final count is > 1, so
        only each finder's own query() -- which alone knows whether a
        pointer actually reduced its candidates -- can tell a genuine
        Rule 1 violation apart from several already-disambiguated
        entities. Kept as a flag rather than an immediate raise purely
        so query() itself never raises for this -- only resolve()/
        resolve_from() (actually reading content) does.
        """
        if isinstance(selection, ReferenceResults3):
            results = selection
        else:
            results = self.query().select(selection)
        if results.ambiguous_content_read and len(results) > 1:
            raise ReferenceException3(
                f"{type(self).__name__} cannot resolve more than one match "
                "at once for a whole-resource content accessor (e.g. "
                ":manifest(), :definition(), :errors()) -- a pointer "
                "(:first()/:last()/:index(n)) or a narrower identity is "
                "required to pick exactly one entity. query() itself is "
                "unaffected -- it may still return every match."
            )
        for result in results.results:
            result.data = self._extract_data(result)
        return results

    @abstractmethod
    def _extract_data(self, result: ReferenceResult3):
        """returns whatever this reference's resolve_kind calls for --
        first-party data (raw bytes/content), a whole metadata file, or
        one metadata field (see Reference3.resolve_kind) -- for the
        given already-queried result. datatype-specific -- reading raw
        file bytes vs errors.json vs vars.json differs enough there is
        no generic implementation."""

    @staticmethod
    def _apply_pointer(pointer, candidates: list) -> dict | None:
        """reduces a list of manifest-entry dicts to the one a pointer
        function selects -- :first()/:last()/:index(n) are plain list-
        position lookups (arrival/registration order is array order,
        confirmed against real manifests for both files and csvpaths),
        so this is identical across every datatype that reads a flat
        manifest array. shared here rather than duplicated per finder."""
        if not candidates:
            return None
        if pointer.name == "first":
            return candidates[0]
        if pointer.name == "last":
            return candidates[-1]
        if pointer.name == "index":
            try:
                return candidates[pointer.arg]
            except IndexError:
                return None
        raise ReferenceException3(f"Unsupported pointer function: {pointer.name}")

    @staticmethod
    def _range_bound(function) -> "int | str | TimeWindowFunction3":
        """the plain int/str value a built ':from()'/':to()' function's
        arg represents -- handles bare leaf values (int for index-mode,
        str for date-mode, added 2026-08-13), nested ":index(n)"
        (unwrapped via its own `.arg`), and a TimeWindowFunction3
        instance (":year()"/":date(...)"/etc, compendium 6.27, widened
        2026-10-17) -- returned AS-IS, not further unwrapped, since
        _bound_window() below needs the instance itself (to call its
        own start_datetime()/end_datetime()), not a raw value. Date3 is
        a TimeWindowFunction3 like its siblings now (previously
        special-cased to unwrap to its own plain date string here --
        that unwrap moved to TimeWindowFunction3.start_datetime()/
        end_datetime() instead, consistent treatment for all ten).

        A ':name()' bound raises here: it is a statement identity, which
        only a name_three statement range has (_identity_bound()). Runs
        and versions take a string bound as a date, so unwrapping it here
        would silently read ':name("2026-01-01")' as one (2026-11-13)."""
        arg = function.arg
        if isinstance(arg, (int, str)):
            return arg
        if isinstance(arg, Name3):
            raise ReferenceException3(
                f"':{function.name}(:name())' takes a statement identity, "
                "which only a name_three range over statements has; runs "
                "and versions have no statement identity."
            )
        if isinstance(arg, TimeWindowFunction3):
            return arg
        return arg.arg

    @staticmethod
    def _range_calls_from_built(built: list) -> tuple:
        """(lower_call, upper_call) -- the built range-bound function(s)
        in `built`, if present. Added 2026-10-16 (compendium 6.28/6.28b/
        6.28c) generalizing the old plain "from_call = next(f for f in
        built if f.name == 'from')" lookup every finder used to write by
        hand: ':after()' is also a LOWER bound (exclusive, where
        ':from()' is inclusive) and ':before()' is also an UPPER bound
        (exclusive, where ':to()' is inclusive) -- a built instance's
        own `.name` always reads back as one of these four canonical
        values regardless of which alias (':below()'/':lt()'/etc, see
        Before3/After3's own docstrings) was actually typed, so no alias
        handling is needed here at all.

        Raises if two LOWER bounds or two UPPER bounds are both present
        (6.28c: "using multiple directional functions indicating the
        same direction is not meaningful so not legal" -- e.g.
        ':from()'+':after()', or ':to()'+':before()'). A LOWER and an
        UPPER together are always legal even when they are dissimilar
        functions (':after()'+':to()', ':from()'+':before()') -- 6.28's
        own explicit example, ':from(:index(5)):to(:yesterday())', pairs
        two different-mode functions without issue; mixing INDEX-mode
        and DATE-mode bounds in one pair is applied, or for the unsettled
        shapes raised, by _apply_mixed_range()."""
        lowers = [f for f in built if f.name in ("from", "after")]
        uppers = [f for f in built if f.name in ("to", "before")]
        if len(lowers) > 1:
            raise ReferenceException3(
                "Combining two lower-bound range functions (':from()'/"
                "':after()', or their aliases) is not legal -- both "
                "indicate the same direction."
            )
        if len(uppers) > 1:
            raise ReferenceException3(
                "Combining two upper-bound range functions (':to()'/"
                "':before()', or their aliases) is not legal -- both "
                "indicate the same direction."
            )
        return (lowers[0] if lowers else None, uppers[0] if uppers else None)

    @classmethod
    def _apply_range(cls, items: list, lower_call, upper_call) -> list:
        """slices `items` (already in the scope's own natural order)
        using ':from()'/':to()' (inclusive) or their exclusive siblings
        ':after()'/':before()' (compendium 6.28, added 2026-10-16,
        generalizing this method's own original :from()/:to()-only
        shape) -- added 2026-08-13, RESULTS' index-mode range selector,
        David's own framing: "our version of BETWEEN in SQL or range()
        in Python." ':to()' is INCLUSIVE of its own position (matches
        SQL BETWEEN and :index(n) itself pointing AT a position --
        ':from(2):to(5)' is positions 2 through 5, both ends included);
        ':before()' EXCLUDES its own position (':before(5)' is
        positions 0 through 4). Either bound may be absent (an open
        range on that side); negative bounds count from the end, same
        convention :index(n) already has.

        `lower_call`/`upper_call` are whichever of the four functions is
        actually present (see _range_calls_from_built() above) -- an
        exclusive LOWER bound (':after()') simply moves one position
        later (`start + 1`, correct for negative bounds too: "after
        position -3" is one position closer to the end, i.e. -2);
        Python slicing already handles everything else (including a
        negative, exclusive UPPER bound -- ':before(-1)' is exactly
        `items[:-1]`, no special-casing needed) except an INCLUSIVE
        UPPER bound of exactly -1 (the last item): "+1" for inclusivity
        would otherwise wrap -1 to 0, which means "nothing" in a slice,
        not "to the end" -- that one case still needs the explicit fix
        _slice_by_position() already had."""
        start = cls._range_bound(lower_call) if lower_call is not None else None
        end = cls._range_bound(upper_call) if upper_call is not None else None
        # an index range takes integer positions. Its callers hand it only
        # index bounds (_apply_mixed_range() filters date bounds itself, and
        # name_three ranges use _apply_identity_range() instead); a bound
        # that still reaches here raised a bare TypeError from the slice
        # until 2026-11-12. (A bool is an int in Python, so it is excluded
        # explicitly; the grammar gives none.)
        for call, bound in ((lower_call, start), (upper_call, end)):
            if bound is not None and (
                isinstance(bound, bool) or not isinstance(bound, int)
            ):
                shown = (
                    f":{bound.NAME}()"
                    if isinstance(bound, TimeWindowFunction3)
                    else f'"{bound}"'
                    if isinstance(bound, str)
                    else repr(bound)
                )
                raise ReferenceException3(
                    f"':{call.name}({shown})' is not an index position here "
                    "-- this range takes integer positions only (e.g. "
                    f"':{call.name}(2)')."
                )
        if lower_call is not None and lower_call.name == "after" and start is not None:
            start = start + 1
        end_inclusive = upper_call is None or upper_call.name == "to"
        return cls._slice_by_position(items, start, end, end_inclusive=end_inclusive)

    @classmethod
    def _apply_identity_range(
        cls, *, items: list, identities: list, lower_call, upper_call
    ) -> list:
        """a name_three statement range (compendium 3.19b: name_three is a
        statement identity; NRE "Identities": "the directional/range
        functions can work on identities"): an int bound is a position, a
        string bound the position of that identity in `identities` (in the
        same order as `items`). An identity that does not match gives no
        results, no error (the NRE). A date bound raises: statements have no
        arrival date of their own (as CSVPATHS, 2026-09-22). Added for
        RESULTS 2026-11-12, mirroring CSVPATHS' identity mode."""
        if items is None or identities is None:
            raise ValueError("items and identities cannot be None")
        if len(items) != len(identities):
            raise ValueError("items and identities must be the same length")
        # every bound is checked before any identity is looked up, so an
        # illegal bound raises even beside an identity that does not match
        # (as CSVPATHS, which checks its bounds up front; reviewer on #596)
        bounds = [
            None if call is None else cls._identity_bound(call)
            for call in (lower_call, upper_call)
        ]
        for call, bound in zip((lower_call, upper_call), bounds):
            if call is None:
                continue
            if isinstance(bound, TimeWindowFunction3):
                shown = f'"{bound.arg}"' if isinstance(bound.arg, str) else ""
                raise ReferenceException3(
                    f"':{call.name}()' does not support a date-mode bound "
                    f"(:{bound.NAME}({shown})) in name_three -- statements "
                    "have no arrival date of their own. A bare string bound "
                    "selects by statement identity instead."
                )
            if not isinstance(bound, str) and (
                isinstance(bound, bool) or not isinstance(bound, int)
            ):
                raise ReferenceException3(
                    f"':{call.name}({bound!r})' is neither a statement identity "
                    "nor an index position."
                )
        positions = []
        for bound in bounds:
            if isinstance(bound, str):
                bound = cls._find_by_identity(bound, identities)
                if bound is None:
                    return []
            positions.append(bound)
        start, end = positions
        if lower_call is not None and lower_call.name == "after" and start is not None:
            start = start + 1
        end_inclusive = upper_call is None or upper_call.name == "to"
        return cls._slice_by_position(items, start, end, end_inclusive=end_inclusive)

    @classmethod
    def _identity_bound(cls, function) -> "int | str | TimeWindowFunction3":
        """a name_three statement-range bound: ':name("x")' is the
        identity "x", the same as a bare string (NRE "Identities":
        "`:name()` with a string, int, or variable equaling the statement
        identity"; 2026-11-13). The string form, and a variable that
        resolves to a string (_resolve_arg() resolves the nested arg
        before this runs), are supported. Name3 does not take an int, so
        `:name(0)` and a variable resolving to an int raise; a /regex/ is
        not an identity, so it raises here. Any other bound is
        _range_bound()'s."""
        if function is None:
            raise ValueError("function cannot be None")
        arg = function.arg
        if isinstance(arg, Name3):
            if not isinstance(arg.arg, str):
                raise ReferenceException3(
                    f"':{function.name}(:name())' takes a statement identity "
                    "string, not a regex."
                )
            return arg.arg
        return cls._range_bound(function)

    @staticmethod
    def _slice_by_position(
        items: list,
        start: "int | None",
        end: "int | None",
        end_inclusive: bool = True,
    ) -> list:
        """the positional half of _apply_range()'s own slicing rule
        (':to()' inclusive of its own position, -1 meaning 'to the end'
        rather than wrapping to nothing; ':before()' -- `end_inclusive=
        False`, added 2026-10-16 -- plain exclusive Python slicing, no
        -1 special case needed), extracted 2026-09-22 so
        CsvpathsReferenceFinder3's own name_three identity-mode range
        (see its own query() docstring) can share it -- there, `start`/
        `end` are int positions already resolved from string identity
        bounds via _find_by_identity(), not raw ':from()'/':to()'
        function calls, so _range_bound()'s own str/int unwrapping does
        not apply. `_apply_identity_range()` (shared by CSVPATHS and
        RESULTS since 2026-11-12) passes `end_inclusive=False` for a
        ':before()' upper bound, as _apply_range() does."""
        if end is None:
            return items[start:]
        if not end_inclusive:
            return items[start:end]
        if end == -1:
            return items[start:]
        return items[start : end + 1]

    @staticmethod
    def _validate_date_format(value: str) -> None:
        """raises unless `value` is a real calendar date in "YYYY-MM-DD"
        form, optionally with a time ("YYYY-MM-DD_HH-MM-SS", the
        Framework's own run-dir timestamp form -- never required,
        issue #409) -- shared 2026-08-13 (previously RESULTS-only)
        alongside FILES/CSVPATHS getting their own date-mode ':from()'/
        ':to()'. Function3.check_valid()'s own generic ARG_TYPES check
        only confirms an arg is A str, not that its CONTENT is a valid
        date -- a malformed date bound would otherwise be silently
        compared as an ordinary string (no crash, just a meaningless
        answer), which is worse than a clear, immediate rejection."""
        try:
            ReferenceFinder3._date_window(value)
        except ValueError:
            raise ReferenceException3(
                "date-mode ':from()'/':to()'/':after()'/':before()' "
                "requires a real calendar date in 'YYYY-MM-DD' form, "
                "optionally with a time ('YYYY-MM-DD_HH-MM-SS'), got "
                f"{value!r}."
            ) from None

    @staticmethod
    def _date_window(value: str) -> tuple:
        """(start, end) for a literal "YYYY-MM-DD"/"YYYY-MM-DD_HH-MM-
        SS" date-mode bound -- day granularity spans the whole day;
        an explicit time narrows to just that one second. The time
        portion is optional, never required (issue #409: David -- v2
        references allowed this; the code never caught up). Raises
        ValueError, same as a plain strptime() would, if neither form
        matches. Mirrors Date3._window() exactly (functions/selectors/
        date_3.py), duplicated to avoid a finder<->function circular
        import (finders import functions, never the reverse)."""
        try:
            start = datetime.strptime(value, "%Y-%m-%d_%H-%M-%S")
            return start, start.replace(microsecond=999999)
        except ValueError:
            pass
        start = datetime.strptime(value, "%Y-%m-%d")
        return start, start.replace(hour=23, minute=59, second=59, microsecond=999999)

    @classmethod
    def _bound_window(cls, call) -> tuple:
        """(start_datetime, end_datetime) for a built ':from()'/':to()'/
        ':before()'/':after()' call's own date-mode bound -- added
        2026-10-17 (compendium 6.27) alongside TimeWindowFunction3.
        `call.arg` is either a plain "YYYY-MM-DD"/"YYYY-MM-DD_HH-MM-SS"
        string (see _date_window()) or a TimeWindowFunction3 instance
        (":year()"/":date(...)"/etc), each of which already knows its
        own [start, end] window at whatever granularity it represents.
        See TimeWindowFunction3's own docstring for the directional
        rule (_apply_manifest_date_range()/
        ResultsReferenceFinder3._apply_date_range()) that consumes this
        pair -- every directional bound uses the start (decision D8,
        2026-11-12); a bare window uses both. The caller decides which,
        not this method."""
        bound = cls._range_bound(call)
        if isinstance(bound, TimeWindowFunction3):
            return bound.start_datetime(), bound.end_datetime()
        return cls._date_window(bound)

    @staticmethod
    def _parse_manifest_time(value) -> datetime:
        """the real datetime a manifest entry's own stored timestamp
        (`Metadata.time_string`'s `isoformat()` output, always UTC via
        DateUtility -- see metadata.py's own `set_time()`) represents,
        with tzinfo stripped so it compares cleanly against
        TimeWindowFunction3's own naive UTC wall-clock values. A
        missing/malformed value resolves to `datetime.min` -- the exact
        same "sorts before every real date" behavior the previous
        day-only string comparison gave a missing/empty field for free
        (an empty string sorts first lexicographically too), preserved
        here deliberately rather than silently dropping such an entry
        from a range filter that only has an UPPER bound (where it
        would previously have still been kept)."""
        if not value:
            return datetime.min
        try:
            return datetime.fromisoformat(str(value)).replace(tzinfo=None)
        except ValueError:
            return datetime.min

    @classmethod
    def _apply_mixed_range(
        cls, *, entries: list, lower_call, upper_call, date_filter
    ) -> list:
        """a range whose bounds may mix index-mode and date-mode
        (compendium 6.32; NRE: '$alpha.results.*:from(2):to(:date(...))'
        is "the 3rd ... through the last result that happened before" the
        date). An index bound is a position in the ordered list, a date
        bound a filter on each entry's time, so the range is both: the
        index bound slices, then the date bound filters. Only a
        non-negative index lower bound with a date upper bound is mixed
        (the NRE's shape): there an index counted from the start and one
        counted from the date anchor agree. The other mixes raise until
        David settles the anchor (decision log W4). With one mode only, it
        is that mode's own range. `date_filter` is the datatype's date
        filter, called as date_filter(entries, lower, upper). Mixing
        raised until 2026-11-12 (David, spec review item 3: "the specs are
        consistent and not illogical, therefore the code is wrong")."""
        if entries is None:
            raise ValueError("entries cannot be None")
        if date_filter is None:
            raise ValueError("date_filter cannot be None")

        def is_date(call) -> bool:
            return call is not None and isinstance(
                cls._range_bound(call), (str, TimeWindowFunction3)
            )

        index_lower = None if is_date(lower_call) else lower_call
        index_upper = None if is_date(upper_call) else upper_call
        date_lower = lower_call if is_date(lower_call) else None
        date_upper = upper_call if is_date(upper_call) else None
        mixed = (index_lower is not None or index_upper is not None) and (
            date_lower is not None or date_upper is not None
        )
        if mixed and not (
            index_lower is not None
            and isinstance(cls._range_bound(index_lower), int)
            and cls._range_bound(index_lower) >= 0
        ):
            # only a non-negative index lower bound with a date upper
            # bound is supported: there an index counted from the start of
            # the list and one counted from the date anchor (compendium
            # 6.29, 6.30) give the same answer. Otherwise they differ, and
            # which one is meant waits for David (decision log W4).
            raise ReferenceException3(
                "Mixing a date lower bound with an index upper bound, or a "
                "negative index with a date bound, is not supported yet: "
                "whether the index counts from the start of the list or "
                "from the date anchor (compendium 6.29, 6.30) is not "
                "settled."
            )
        if index_lower is not None or index_upper is not None:
            entries = cls._apply_range(entries, index_lower, index_upper)
        if date_lower is not None or date_upper is not None:
            entries = date_filter(entries, date_lower, date_upper)
        return entries

    @classmethod
    def _apply_manifest_date_range(
        cls, entries: list, lower_call, upper_call, key: str = "time"
    ) -> list:
        """filters `entries` (manifest-entry dicts) to those whose own
        `entries[i][key]` (an ISO datetime string, e.g. FILES/CSVPATHS'
        own "time" field -- registration/load time, see functions/
        fields/time_3.py's own SUMMARY) falls within the date range
        `lower_call`/`upper_call` describe -- date-mode ':from()'/
        ':to()' (both INCLUSIVE) for FILES/CSVPATHS, added 2026-08-13;
        generalized 2026-10-16 (compendium 6.28) to also accept their
        exclusive siblings ':after()'/':before()', mirroring
        _apply_range()'s own generalization. Unlike index-mode
        (_apply_range, a POSITIONAL slice), this is a FILTER, not a
        slice -- comparing positions would be meaningless for a date
        bound.

        Rewritten 2026-10-17 (compendium 6.27, TimeWindowFunction3) from
        a fixed day-only ("YYYY-MM-DD"[:10]) string-prefix comparison to
        real datetime comparison, confirmed against David directly --
        the old day-only truncation was never a property of the DATA
        (the stored "time" field is always a full, real-precision
        isoformat() string), only of the bounds that happened to exist
        so far (:date()/:yesterday()/:today(), all day-granular); once
        :hour()/:minute()/:second() exist as real bounds, a fixed day-
        level truncation would silently flatten them to mean the same
        thing as :today(), which has no principled basis. Every bound is
        its first moment (compendium 6.27b, 6.27g; decision D8,
        2026-11-12; ':to()' and ':after()' used X's end until then):
            ':from(X)'   keeps candidates >= X.start
            ':to(X)'     keeps candidates <= X.start
            ':before(X)' keeps candidates <  X.start
            ':after(X)'  keeps candidates >  X.start
        See TimeWindowFunction3's own docstring for the full reasoning."""
        # every bound is its first moment (6.27b, 6.27g; decision D8)
        lower_start = upper_start = None
        if lower_call is not None:
            lower_start, _ = cls._bound_window(lower_call)
        lower_inclusive = lower_call is None or lower_call.name == "from"
        if upper_call is not None:
            upper_start, _ = cls._bound_window(upper_call)
        upper_inclusive = upper_call is None or upper_call.name == "to"
        result = []
        for entry in entries:
            d = cls._parse_manifest_time(entry.get(key))
            if lower_start is not None:
                if lower_inclusive and d < lower_start:
                    continue
                if not lower_inclusive and d <= lower_start:
                    continue
            if upper_start is not None:
                if upper_inclusive and d > upper_start:
                    continue
                if not upper_inclusive and d >= upper_start:
                    continue
            result.append(entry)
        return result

    @classmethod
    def _apply_bare_time_window_to_manifest(
        cls, entries: list, call: "TimeWindowFunction3", key: str = "time"
    ) -> list:
        """filters `entries` (manifest-entry dicts) to those whose own
        `entries[i][key]` falls within `call`'s own [start_datetime(),
        end_datetime()] window -- Gap 1 of compendium 6.27/
        TimeWindowFunction3, added 2026-10-17: a bare time-component
        function riding in the chain (e.g. ":year()"), with no explicit
        ':from()'/':to()' of its own. FILES'/CSVPATHS' own manifest-
        entry counterpart to ResultsReferenceFinder3._apply_bare_time_
        window() (run directories there, manifest dicts here) -- always
        INCLUSIVE on both ends, same reasoning: the bare function always
        means its own whole period, both ends included, with no
        separate directional function to pick otherwise."""
        start = call.start_datetime()
        end = call.end_datetime()
        return [
            entry
            for entry in entries
            if start <= cls._parse_manifest_time(entry.get(key)) <= end
        ]

    @staticmethod
    def _check_position(function, position: str, datatype: str) -> None:
        """raises unless `function` declares `position` as legal for
        `datatype` in its own Function3.POSITIONS -- added 2026-08-14,
        the enforced replacement for the scattered, inconsistent "is
        this recognized" guards each Finder used to hand-write on its
        own (the gap that let "$acme.csvpaths.:name('x')" silently
        no-op instead of raising -- CsvpathsReferenceFinder3.
        _resolve_versions() had no such guard at all, while query()'s
        name_three handling did). Rolled out incrementally per Finder
        (CSVPATHS first) rather than all at once -- a function with no
        POSITIONS entry for a given datatype has simply not been
        migrated to this mechanism yet by that datatype's own Finder,
        not necessarily rejected everywhere; only a Finder that
        actually calls this method enforces it. See Function3.POSITIONS
        and Reference3.NAME_ONE/TWO/THREE's own docstrings."""
        legal = function.POSITIONS.get(datatype, ())
        if position not in legal:
            raise ReferenceException3(
                f":{function.name}() is not legal at {position} for {datatype}."
            )

    @staticmethod
    def _apply_implied_star(name_one) -> None:
        """compendium 3.9c/3.9d: "a function starting name_one or
        following directly after a path separator implies a '*'
        wildcard," unless it is itself a wildcard (:all()/:flatten()/
        :groups()), fully occupies a path segment (:name()/:regex()/
        :choice()/a clock value function like :year(), per
        _compile_path_pattern()'s own equivalent exemption -- both
        compute a VALUE that becomes part of the match itself, not a
        pointer/reader of something the match produces), or does not
        operate in a path segment at all (:manifest()/:definition()/
        :on_arrival()/:fingerprint()/etc). Added 2026-09-24. Only the
        first two exemption categories are checked explicitly below --
        the third is already filtered out by each finder's own
        dedicated bare-shape checks (e.g. _is_bare_pointer_reference(
        reference, "manifest")), which run BEFORE this and intercept
        those functions with their own early return; confirmed by
        direct reading that every currently-registered "doesn't operate
        in a path segment" function already has such a check, so none
        of them ever reach this method at all in practice.

        Mutates `name_one` in place: when its OWN LAST path segment is
        a non-exempt function (this covers both "starting name_one" --
        a bare, sole-content function -- and "following a path
        separator" -- any position, since a function can only ever
        legally be the LAST written path segment; an earlier position
        would mean more path after a value-reducing/reading function,
        which is not meaningful), it is popped off, a Star3() is
        appended in its place, and the function itself is moved to the
        FRONT of name_one.functions. This is deliberately a
        NORMALIZATION, not new dispatch logic of its own: the result is
        the exact same shape a literal '*' followed directly by that
        same function already produces (e.g. "*:last()"), which every
        existing call site already knows how to handle correctly --
        confirmed this also correctly reroutes the bare-pointer-alone
        case (e.g. "$acme.results.:last()") onto the SAME zero-level
        candidate set the dedicated bare-function-only handling already
        produces, since a bare/trailing Star3 is itself already
        special-cased to degenerate to zero-level (the 2026-09-21 fix)
        -- not a new or different outcome, just a more uniform path to
        the identical one.

        Not applied to '*' traversal (_query_star_traversal()) or to
        CSVPATHS (which has no literal path at all in name_one) -- see
        the bucket list for the traversal scoping note."""
        path = name_one.path
        if not path or not isinstance(path[-1], FunctionCall3):
            return
        if path[-1].name in (
            "all",
            "flatten",
            "groups",
            "name",
            "regex",
            # ':choice()' -- added 2026-10-20, same reasoning as
            # ':name()'/':regex()' just above: compendium 3.9c groups
            # all three as "fully occupies a path segment," so none of
            # them implies a '*' wildcard.
            "choice",
            # ':manifest()' -- added 2026-10-15, closing a real gap: it
            # was previously ONLY exempt by accident, never by name.
            # David caught this live (not a code bug yet, since FILES
            # has no implied-'*' wiring at all -- but a real design
            # trap for whichever future fix touches it): per 3.9c's own
            # "doesn't operate in a path segment at all" category,
            # :manifest() must NEVER trigger implied-'*', because unlike
            # a pointer/field accessor (which this normalization exists
            # to route through the ordinary path-matching machinery),
            # :manifest() riding alongside a pointer in a bare chain
            # means "whichever entity the REST of the chain already
            # selects, give its manifest" -- not a second, independent
            # thing to match against a wildcarded path. Confirmed live
            # before this fix: RESULTS' own bare ":manifest():last()"
            # already got silently normalized into "*:manifest():last()"
            # by this method, and happened to still give the right
            # answer ONLY because RESULTS' own :manifest() always means
            # "this one already-selected run's own file" (one run, one
            # manifest.json -- no shared-array-across-candidates
            # concept the way FILES' Table 1 has). That coincidence is
            # not something to keep relying on -- see the dedicated
            # "$name.files.:manifest():last()" bucket-list entry for
            # why this matters far more once FILES gets its own
            # implied-'*' wiring: there, :manifest() genuinely IS an
            # ordinal index into one shared array across every matched
            # file_home, and letting implied-'*' re-route it through
            # pooled/grouped path-matching would silently change its
            # meaning.
            "manifest",
        ):
            return
        function_cls = ReferenceFunctionFactory.get_registered_class(path[-1].name)
        if function_cls is not None and function_cls.SOURCE == "clock":
            return
        implied = path.pop()
        path.append(Star3())
        name_one.functions.insert(0, implied)

    @staticmethod
    def _is_bare_pointer_reference(reference: Reference3, name: str) -> bool:
        """true when name_one's entire content is a single, argument-
        less ":name()" call -- no other path segments, no trailing
        chain, and no name_three. Detects a reference like
        "$acme.files.:manifest()", which needs its own query() branch
        entirely separate from ordinary "which file"/"which version"
        narrowing, since a metadata-file function like :manifest()
        points at one fixed resource regardless of any path/version
        selection. Shared here because both files and csvpaths need the
        identical check for :manifest()."""
        name_one = reference.name_one
        return (
            reference.name_three is None
            and not name_one.functions
            and len(name_one.path) == 1
            and isinstance(name_one.path[0], FunctionCall3)
            and name_one.path[0].name == name
            and name_one.path[0].arg is None
        )

    @staticmethod
    def _pointer_before_manifest(
        reference: Reference3, name: str
    ) -> "FunctionCall3 | None":
        """returns the pointer function call riding alongside a bare
        ":name()" call in name_one -- in either order (both
        "$*.files.:last():manifest()" and "$*.files.:manifest():last()"
        parse to one segment in name_one.path and one in
        name_one.functions, just swapped), or None if this reference is
        not shaped that way. Ordinal indexing into a global ledger (Rule
        1b, manifest_field_functions_proposal.md) -- a pointer here
        selects one entry out of the whole ledger array, same
        position-based selection _apply_pointer() already does for a
        named entity's own manifest, just applied to the ledger instead.
        Shared by files/csvpaths/results since all three ledgers are
        flat arrays in arrival order. Order-insensitive on purpose,
        matching every literal-root query() path, which never cares
        which of pointer/:name() came first in a combined chain --
        confirmed missing here and fixed 2026-08-10."""
        name_one = reference.name_one
        if reference.name_three is not None:
            return None
        if len(name_one.path) != 1 or len(name_one.functions) != 1:
            return None
        calls = (name_one.path[0], name_one.functions[0])
        if not all(isinstance(c, FunctionCall3) for c in calls):
            return None
        pointer_calls = [c for c in calls if c.name in ("first", "last", "index")]
        manifest_calls = [c for c in calls if c.name == name and c.arg is None]
        if len(pointer_calls) != 1 or len(manifest_calls) != 1:
            return None
        return pointer_calls[0]

    @staticmethod
    def _query_well_known_file(home: str, filename: str) -> ReferenceResults3:
        """query() branch for a fixed, home-directory-scoped JSON
        resource (manifest.json, definition.json) -- one result,
        uuid=None (not a registered version), bypassing whatever
        "which file"/"which version" narrowing the concrete finder
        would otherwise do for an ordinary reference. Shared by files
        and csvpaths for both :manifest() and :definition() -- both
        live at exactly the same named-file/named-paths home directory
        in either datatype."""
        path = Nos(home).join(filename)
        return ReferenceResults3(results=[ReferenceResult3(path=path, uuid=None)])

    #
    # the definition chain (E3, 2026-11-02 for FILES; shared with CSVPATHS
    # 2026-11-10). definition.json is one record per named-file or
    # named-paths group, and it is not versioned, so a definition read
    # gives one result per entity, never one per version. A subclass
    # that reads definitions supplies DEFINITION_OWNER and the three
    # hooks below.
    #
    DEFINITION_OWNER: str | None = None

    def _definition_names(self) -> list:
        """every live entity that can have a definition.json, by name"""
        raise NotImplementedError(
            f"{type(self).__name__} does not read definition.json"
        )

    def _definition_home(self, name: str) -> str:
        """the home directory of `name`, where its definition.json is"""
        raise NotImplementedError(
            f"{type(self).__name__} does not read definition.json"
        )

    def _definition_config(self, name: str):
        """the describer's parsed definition.json for `name`"""
        raise NotImplementedError(
            f"{type(self).__name__} does not read definition.json"
        )

    def _definition_path(self, name: str) -> str:
        if name is None or name == "":
            raise ValueError("name cannot be None or empty")
        return Nos(self._definition_home(name)).join("definition.json")

    @staticmethod
    def _is_bare_definition_reference(name_one) -> bool:
        """true when name_one's entire content is a single, argument-
        less ':definition()' call, with no trailing function chain --
        the '*'-traversal counterpart to _is_bare_pointer_reference's
        identical literal-root check (added 2026-08-27)."""
        return (
            not name_one.functions
            and len(name_one.path) == 1
            and isinstance(name_one.path[0], FunctionCall3)
            and name_one.path[0].name == "definition"
            and name_one.path[0].arg is None
        )

    @staticmethod
    def _bare_definition_field_call(name_one) -> "FunctionCall3 | None":
        """returns the field-accessor FunctionCall3 when name_one's
        entire content is a single function whose registered class is
        SOURCE == "definition" (":on_arrival()", ":scripts()", etc.), OR
        whose BARE_SOURCE == "definition" (":template()" -- added
        2026-08-26, see Template3's own docstring: bare means the current
        default, a different resource than a version's own snapshot).
        These values live in the entity's definition.json, not in any
        version's manifest entry. An argument is fine here too (e.g.
        ':source_port("email")'): it picks the key, not a version. None
        for every other shape, including a plain SOURCE == "manifest"
        field accessor (":uuid()"/":time()"/etc.), which varies by
        version."""
        if name_one.functions or len(name_one.path) != 1:
            return None
        segment = name_one.path[0]
        if not isinstance(segment, FunctionCall3):
            return None
        function_cls = ReferenceFunctionFactory.get_registered_class(segment.name)
        if function_cls is not None and (
            function_cls.SOURCE == "definition"
            or function_cls.BARE_SOURCE == "definition"
        ):
            return segment
        return None

    @classmethod
    def _definition_chain(cls, *, name_one) -> "list | None":
        """the definition.json field calls of a ':definition()' chain in
        name_one, chained or nested as its argument, e.g.
        ':definition():on_arrival()' or
        ':definition(:on_arrival(:has_value()))' (E3, 2026-11-02). Like
        ':manifest()', ':definition()' names one file per entity, and
        definition.json has no version, so the chain only reads and
        filters that one record.

        A bare definition field is the same one-field chain:
        ':template(:has_value())' is ':definition(:template(:has_value()))'
        and ':template()' is ':definition():template()' (2026-11-03). A
        filter then resolves to the definition.json (D) and a value is
        read per entity under every root.

        Returns None for any other shape: bare ':definition()', and a
        chain with a path-building function, which keep their own
        branches. Raises for a field that does not read
        definition.json, and for a pointer, range or time window, which
        have no version to select."""
        if name_one is None:
            raise ValueError("name_one cannot be None")
        bare = cls._bare_definition_field_call(name_one)
        if bare is not None:
            return [bare]
        if len(name_one.path) != 1:
            return None
        calls = [name_one.path[0], *name_one.functions]
        if not all(isinstance(c, FunctionCall3) for c in calls):
            return None
        definitions = [c for c in calls if c.name == "definition"]
        if len(definitions) != 1:
            return None
        definition = definitions[0]
        others = [c for c in calls if c is not definition]
        if isinstance(definition.arg, FunctionCall3):
            others.insert(0, definition.arg)
        elif definition.arg is not None:
            return None
        if not others:
            return None
        if any(c.name in ("name", "regex", "choice") for c in others):
            return None
        for call in others:
            function_cls = ReferenceFunctionFactory.get_registered_class(call.name)
            if function_cls is not None and (
                function_cls.SOURCE == "definition"
                or function_cls.BARE_SOURCE == "definition"
            ):
                continue
            if function_cls is not None and function_cls.SOURCE in (
                "manifest",
                "computed",
            ):
                raise ReferenceException3(
                    f"':{call.name}()' does not read a {cls.DEFINITION_OWNER}'s "
                    "definition.json, so it is not supported in a "
                    "':definition()' chain."
                )
            raise ReferenceException3(
                f"':{call.name}()' is not supported in a ':definition()' "
                "chain -- definition.json is not versioned, so there is no "
                "version to select."
            )
        return others

    def _split_definition_fields(self, *, calls: list) -> tuple:
        """(filters, values) of a ':definition()' chain's field calls. A
        field with a predicate argument (':on_arrival(:has_value())') is a
        filter, built; any other field is a value, as written. Its
        argument, if any, picks a key (':source_port("email")'). The same
        test the bare definition fields use."""
        if calls is None:
            raise ValueError("calls cannot be None")
        filters = []
        values = []
        for call in calls:
            if call.arg is not None:
                built = self._build(call)
                if isinstance(built.arg, PredicateFunction3):
                    filters.append(built)
                    continue
            values.append(call)
        return filters, values

    def _matches_definition_field_predicate(self, name: str, field_call) -> bool:
        """true if `name`'s own definition.json has `field_call`'s own
        field, and that value satisfies `field_call.arg`'s own predicate
        (e.g. ':has_value()') -- the generic predicate-argument filtering
        mechanism, added 2026-10-17. `field_call` is already a built
        Function3 with a PredicateFunction3 arg (_split_definition_
        fields()); this reads the value by the field's KEY and tests it.
        Not bespoke to any one field: every SOURCE == "definition" field
        works here."""
        function_cls = ReferenceFunctionFactory.get_registered_class(
            field_call.name
        )
        key_path = function_cls.KEY.get(self.ref.parsed.datatype)
        config = self._definition_config(name)
        entry = config.model_dump(exclude_none=True)
        value = self._extract_field_value(entry, key_path)
        return field_call.arg.matches(value)

    def _query_definition_chain(
        self, *, reference: Reference3, calls: list, name_filter: "str | None"
    ) -> ReferenceResults3:
        """query() for a ':definition()' chain (_definition_chain()): the
        definition.json of each entity that passes every filter, one for
        a literal root, each live one for '*', ':regex()' and ':choice()'.
        Several whole files at once cannot be resolved (compendium 5.8),
        so that case is flagged."""
        if calls is None:
            raise ValueError("calls cannot be None")
        if reference.name_three is not None:
            raise ReferenceException3(
                f"{type(self).__name__} does not support combining a "
                "':definition()' chain with name_three -- definition.json is "
                "not versioned, there is no version to select."
            )
        filters, values = self._split_definition_fields(calls=calls)
        if len(values) > 1:
            self.csvpaths.logger.warning(
                "Reference resolves to the value of the last field-accessor "
                "function in its chain (:%s()) -- :%s() earlier in the same "
                "chain could also have provided a value; see compendium 5.20b.",
                values[-1].name,
                "(), :".join(f.name for f in values[:-1]),
            )
        if isinstance(reference.root_major, str):
            names = [reference.root_major]
        else:
            names = self._matching_names(self._definition_names(), name_filter)
        names = [
            name
            for name in names
            if all(self._matches_definition_field_predicate(name, f) for f in filters)
        ]
        results = [
            ReferenceResult3(path=self._definition_path(name), uuid=None)
            for name in names
        ]
        return ReferenceResults3(
            results=results,
            ambiguous_content_read=not values and len(results) > 1,
        )

    def _query_definition_files(self, *, names: list) -> ReferenceResults3:
        """query() for a bare ':definition()' over several entities ('*',
        ':regex()', ':choice()'): each one's definition.json, one result
        each. Rule 1 (manifest_field_functions_proposal.md): resolving
        more than one whole file at once is illegal, so more than one is
        flagged; query() still returns them all, and resolve_from() raises
        only if a caller resolves more than one."""
        if names is None:
            raise ValueError("names cannot be None")
        results = [
            ReferenceResult3(path=self._definition_path(name), uuid=None)
            for name in names
        ]
        return ReferenceResults3(
            results=results, ambiguous_content_read=len(results) > 1
        )

    def _definition_chain_data(
        self, *, reference: Reference3, calls: list, path: str
    ) -> object:
        """resolve() for a ':definition()' chain: the last value field's
        value from the entity's definition.json, or with no value field
        the definition.json itself (compendium 6.19)."""
        if calls is None:
            raise ValueError("calls cannot be None")
        if path is None or path == "":
            raise ValueError("path cannot be None or empty")
        _, values = self._split_definition_fields(calls=calls)
        if not values:
            return self._read_well_known_file(path)
        if isinstance(reference.root_major, str):
            name = reference.root_major
        else:
            name = next(
                (
                    n
                    for n in self._definition_names()
                    if self._definition_path(n) == path
                ),
                None,
            )
            if name is None:
                raise ReferenceException3(
                    f"{type(self).__name__} found no {self.DEFINITION_OWNER} "
                    f"for {path!r}."
                )
        field_call = values[-1]
        function_cls = ReferenceFunctionFactory.get_registered_class(field_call.name)
        key_path = self._apply_key_arg(
            function_cls.KEY.get(reference.datatype), field_call.arg
        )
        config = self._definition_config(name)
        return self._extract_field_value(config.model_dump(exclude_none=True), key_path)

    @staticmethod
    def _read_well_known_file(path: str):
        """reads a well-known, home-directory-scoped JSON resource
        (manifest.json, definition.json) as raw bytes -- None if it
        does not exist yet. manifest.json is always created once
        anything is registered/loaded, but definition.json is genuinely
        optional -- a named-file/named-paths group that was never
        explicitly configured has no definition.json on disk at all.
        The describer classes elsewhere in the codebase (NamedFile
        Describer/NamedPathsDescriber) already treat that absence as
        normal, not an error (their own get_json() returns {} rather
        than raising) -- same treatment here, rather than fabricating
        an empty-JSON default nobody actually wrote."""
        if not Nos(path).exists():
            return None
        with DataFileReader(path=path, mode="rb") as reader:
            return reader.source.read()

    @staticmethod
    def _log_call_anywhere(reference: Reference3) -> "FunctionCall3 | None":
        """returns the :log() FunctionCall3 if it appears anywhere in
        name_one (regardless of whether the overall shape is legal),
        else None -- added 2026-08-26 (compendium 5.16(b)). Checked
        separately from _bare_log_call() so a caller can give a clear,
        specific error ("must be standalone") for an illegal
        combination, rather than falling through to whatever generic
        "not supported" message the ordinary dispatch would raise for
        an unrecognized shape."""
        name_one = reference.name_one
        segments = [*name_one.path, *name_one.functions]
        for seg in segments:
            if isinstance(seg, FunctionCall3) and seg.name == "log":
                return seg
        return None

    @staticmethod
    def _bare_log_call(reference: Reference3) -> "FunctionCall3 | None":
        """returns the :log() FunctionCall3 only if name_one is EXACTLY
        a bare, standalone :log() call -- nothing else in name_one's
        path or function chain, and no name_two/name_three -- per the
        compendium's own "standalone, not-combinable" requirement
        (5.16(b)). Does NOT check root_major -- :log() is a single,
        datatype-independent global resource (the configured log_file),
        not tied to any named entity, so root_major being '*' is a
        separate, dedicated check the caller makes itself (a literal
        root_major gets its own clear error, not silent misuse). Note
        name_two (the "#worksheet" marker) lives on name_one itself,
        not on Reference3 directly."""
        if reference.name_three is not None:
            return None
        name_one = reference.name_one
        if name_one.name_two is not None:
            return None
        if len(name_one.path) != 1 or name_one.functions:
            return None
        call = name_one.path[0]
        if not isinstance(call, FunctionCall3) or call.name != "log":
            return None
        return call

    def _query_log_call(self, reference: Reference3) -> "ReferenceResults3 | None":
        """query()'s own entry point for :log() -- shared by all three
        finders since the log file is identical regardless of
        datatype. Returns None if :log() is not present at all (an
        ordinary reference, unaffected); raises if it is present but
        the shape is illegal; otherwise returns the one-result
        ReferenceResults3 pointing at the configured log file itself
        (uuid=None, same convention _query_well_known_file() uses for
        a fixed, non-versioned resource)."""
        if self._log_call_anywhere(reference) is None:
            return None
        if self._bare_log_call(reference) is None:
            raise ReferenceException3(
                ":log() must be a standalone, not-combinable function -- "
                "it cannot ride alongside a pointer or any other "
                "function in name_one, and does not support name_two/"
                "name_three."
            )
        if not isinstance(reference.root_major, Star3):
            raise ReferenceException3(
                ":log() requires root_major to be '*' -- it resolves a "
                "single, global log file, not tied to any specific "
                "named entity."
            )
        path = self.csvpaths.config.log_file
        return ReferenceResults3(results=[ReferenceResult3(path=path, uuid=None)])

    @classmethod
    def _read_log_file(cls, path: str, lines: int | None):
        """reads the configured log file as text -- the whole thing if
        `lines` is None, otherwise just its last `lines` lines,
        rejoined with newlines (settled with David, 2026-08-26: a
        single string, not raw bytes or a list of line strings, per
        the compendium's own "gives... a string" resolve-type framing
        for text content). None if the log file does not exist yet
        (nothing has ever been logged).

        For a bounded `lines` request, delegates to _tail_lines() to
        avoid reading the whole file just to throw most of it away --
        added 2026-10-20, David found :log(10) against a large log
        file was reading and decoding the entire file before slicing
        off the last 10 lines. `lines <= 0` falls through to the old
        whole-file behavior unchanged (not part of the documented
        "N most recent lines" usage, so not worth a new code path)."""
        if not Nos(path).exists():
            return None
        if lines is not None and lines > 0:
            return cls._tail_lines(path=path, lines=lines)
        with DataFileReader(path=path) as reader:
            text = reader.source.read()
        if lines is None:
            return text
        return "\n".join(text.splitlines()[-lines:])

    @staticmethod
    def _tail_lines(*, path: str, lines: int) -> str:
        """the last `lines` lines of a local text file, without
        reading the whole file into memory first. Seeks backward from
        the end in fixed-size chunks, accumulating raw bytes, until at
        least `lines` newlines have been seen or the start of the file
        is reached -- then decodes just that tail and trims to exactly
        `lines` lines. Produces the same result as reading the whole
        file and taking text.splitlines()[-lines:], just bounded to
        roughly how much text is actually needed rather than the
        whole file's size.

        decode(errors="replace") rather than strict: a backward seek
        can land mid-character on a multi-byte UTF-8 sequence. That
        can only corrupt the EARLIEST (leading) partial line of the
        decoded tail -- which is always either discarded (the loop
        only stops once it has strictly more than `lines` newlines, so
        there is always at least one extra leading line to absorb it)
        or doesn't exist at all (the loop stopped at the real start of
        the file, a clean boundary)."""
        chunk_size = 65536
        blocks = []
        newline_count = 0
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            position = f.tell()
            while position > 0 and newline_count <= lines:
                read_size = min(chunk_size, position)
                position -= read_size
                f.seek(position)
                block = f.read(read_size)
                newline_count += block.count(b"\n")
                blocks.append(block)
        data = b"".join(reversed(blocks))
        text = data.decode("utf-8", errors="replace")
        return "\n".join(text.splitlines()[-lines:])

    @staticmethod
    def _read_well_known_json(path: str):
        """reads a well-known, JSON-shaped resource (results' errors.json/
        vars.json/meta.json) as a parsed Python structure -- None if it
        does not exist yet, same tolerant treatment as
        _read_well_known_file, just parsed rather than raw bytes (per
        the spec's own "Following a reference" section: resolving a
        reference gives bytes, if binary, or a string or JSON
        structure -- these are the JSON-structure case)."""
        return FilesystemReferenceSource.read_json(path)

    @staticmethod
    def _find_manifest_entry_by_uuid(manifest: list, uuid: str) -> dict | None:
        """returns the manifest array entry whose "uuid" matches, or None
        if absent -- shared by any finder resolving a ":manifest()" call
        that rides alongside a real pointer (the entry the pointer
        already selected, per Reference3.resolve_kind's METADATA_FILE
        classification), rather than the whole raw file."""
        return next((entry for entry in manifest if entry["uuid"] == uuid), None)

    def _compile_path_pattern(self, path: list) -> list:
        """turns a name_one path into a list of str/Star3 to match
        against real path segments (a manifest entry's file_home for
        files, real directory names for results). a literal str or
        Star3 segment passes through unchanged; a :name("...") segment
        is compiled and its own arg run through _resolve_value() (so a
        "{...}"-interpolated name, e.g. :name("orders-{:year()}.csv"),
        unwraps to its final literal string the same way a plain
        literal name always has) -- built specifically because a
        literal name containing characters a bare PATH_SEGMENT cannot
        hold (e.g. a real filename's ".") has no other way to appear.

        A bare SOURCE == "clock" function (e.g. :year()) is ALSO now a
        legal path segment in its own right (added 2026-08-26, see
        Year3's own docstring) -- e.g. "$acme.files.orders/:year()" ->
        matches "acme/orders/2026" today, at whatever the current year
        actually is. Evaluated the same way _resolve_value() evaluates
        one inside "{...}" -- build the Function3, call compute(),
        stringify. Any other function-valued segment is still not
        supported. Shared by files and results -- both have a real,
        literal/star/:name(...)/clock-function path to match; csvpaths
        does not (its whole name_one is version-selecting functions).

        Instance method (not a staticmethod, since 2026-08-26) purely
        because _resolve_value() now needs this finder's own registered
        variables -- callers already invoke this as self._compile_path_
        pattern(...) everywhere, so nothing else changes."""
        pattern = []
        for segment in path:
            if isinstance(segment, FunctionCall3):
                if segment.name == "name":
                    # self._build() already resolves a Variable3/
                    # InterpolatedString3 arg in place (added
                    # 2026-08-27) -- built.arg is already the final,
                    # plain value here, no separate _resolve_value()
                    # call needed anymore.
                    built = self._build(segment)
                    pattern.append(built.arg)
                    continue
                if segment.name == "regex":
                    # a bare ":regex(...)" path segment -- added
                    # 2026-09-23, closing the deferred-work bucket list
                    # gap of the same name (normative_reference_
                    # examples.txt's own worked example, corrected
                    # 2026-09-23 to require '/' separators like every
                    # other path segment: "orders/:regex(\"202[6789]\")/
                    # EMEA/:last()" -- matches a TEMPLATE segment by
                    # pattern, the same job :name(/pattern/) already
                    # does, just spelled without the :name() wrapper.
                    # Confirmed by direct parsing before this fix: the
                    # grammar already accepts ":regex(...)" as an
                    # ordinary '/'-separated path segment (it is a
                    # FunctionCall3 like any other); only this shared
                    # compiler did not yet recognize it as legal here.
                    # RegexSelector3's own .pattern property already
                    # normalizes both ":regex(/pattern/)" and
                    # ":regex(\"pattern\")" to a raw string -- wrapped in
                    # a Regex3 here so _segment_matches() takes its
                    # existing regex-search branch, the same one
                    # :name(/pattern/) already triggers. Applies to both
                    # FILES and RESULTS, which share this method -- David
                    # confirmed both should work the same way.
                    built = self._build(segment)
                    pattern.append(Regex3(pattern=built.pattern))
                    continue
                if segment.name == "choice":
                    # a bare ":choice(...)" path segment -- added
                    # 2026-10-20, closing the first of the 30 "does not
                    # yet support" sites catalogued that day.
                    # ChoiceSelector3's own .pattern property already
                    # compiles its pipe-delimited names down to an
                    # anchored, escaped regex alternation -- wrapped in
                    # a Regex3 here exactly like :regex() just above,
                    # so _segment_matches() takes the identical
                    # existing branch, no new matching logic needed.
                    built = self._build(segment)
                    pattern.append(Regex3(pattern=built.pattern))
                    continue
                function_cls = ReferenceFunctionFactory.get_registered_class(
                    segment.name
                )
                if function_cls is None or function_cls.SOURCE != "clock":
                    raise ReferenceException3(
                        f"Does not yet support :{segment.name}() as a "
                        "name_one path segment -- only :name(\"...\"), "
                        "a clock value function (e.g. :year()), "
                        "literal/'*' segments, and :choice(...)/:regex(...) "
                        "are supported."
                    )
                built = self._build(segment)
                pattern.append(str(built.compute()))
            elif isinstance(segment, (str, Star3)):
                pattern.append(segment)
            else:
                raise ReferenceException3(f"Unsupported name_one path segment: {segment!r}")
        return pattern

    @staticmethod
    def _segment_matches(expected, actual: str) -> bool:
        """true if `actual` (one real path/run-directory segment) matches
        `expected` (one already-compiled pattern element from
        _compile_path_pattern) -- Star3 is a wildcard (matches anything);
        a Regex3 (added 2026-08-27, ":name(/pattern/)" -- see Name3's own
        docstring) searches, not anchored to the start/whole segment,
        the same established semantics :idchain()'s own Regex3 argument
        already uses (David's call there, reused rather than
        reinvented: search() so the pattern does not need to match the
        whole segment, just find something within it); anything else (a
        plain str, from a literal segment or a resolved ":name(\"...\")")
        is exact equality. Shared by FilesReferenceFinder3's own
        _matches/_matches_suffix and ResultsReferenceFinder3's own
        _matches_prefix/_matches_prefix_at_least -- one comparison rule,
        not four copies of it."""
        if isinstance(expected, Star3):
            return True
        if isinstance(expected, Regex3):
            return re.search(expected.pattern, actual) is not None
        return actual == expected

    @staticmethod
    def _is_traversal_root(root_major) -> bool:
        """true when root_major spans potentially more than one entity
        -- either the '*' token, or a :regex()/:choice() selector
        (:regex() added 2026-08-27; :choice() added 2026-10-20, same
        reasoning -- it can match more than one named-file/named-paths/
        named-results group just as easily as :regex() can) -- as
        opposed to a literal, single-entity IDENTIFIER. Used wherever a
        finder needs to decide "could this matched result have come
        from any of several named-files/named-paths groups/named-
        results groups" (e.g. CsvpathsReferenceFinder3._group_manifest_
        entry()), as distinct from the narrower, Star3-ONLY Rule 1a/1b
        global-ledger checks each finder's own query()/_extract_data()
        also makes -- neither :regex() nor :choice() ever reaches
        those, they have no equivalent global-ledger shortcut of their
        own (see each finder's own query())."""
        return isinstance(root_major, Star3) or (
            isinstance(root_major, FunctionCall3)
            and root_major.name in ("regex", "choice")
        )

    @staticmethod
    def _matching_names(names: list, name_filter: "str | None") -> list:
        """`names`, filtered down to those matching `name_filter` (a
        regex pattern string, re.search()'d -- not anchored, same
        convention _segment_matches() already uses for Regex3
        everywhere else), or `names` unchanged when `name_filter` is
        None. Added 2026-08-27 for :regex() at root_major -- shared by
        FilesReferenceFinder3's/CsvpathsReferenceFinder3's own
        _query_star_traversal(), each of which enumerates its own
        datatype's full name list at several points; ResultsReference
        Finder3 threads the same filter through its own single shared
        _discover_run_homes() instead, since it already had one funnel
        point these two finders don't."""
        if name_filter is None:
            return names
        return [n for n in names if re.search(name_filter, n)]

    @staticmethod
    def _is_bare_selector_reference(name_one) -> bool:
        """true when name_one's entire content is a single, argued
        FunctionCall3 whose registered Function3 class declares
        SELECTOR_WHEN_ARGUED -- e.g. ':fingerprint("hash...")' as
        name_one's sole content, selecting the entity whose own
        fingerprint field matches, rather than reading a field off an
        already-selected one. Added 2026-08-28 as the generic,
        declarative replacement for FilesReferenceFinder3's own
        original bespoke, hand-written _is_bare_fingerprint_reference()
        -- same structural shape every _is_bare_X_reference sibling
        there already uses (no chained functions, exactly one path
        segment, that segment a FunctionCall3), just with the function-
        name check replaced by a registry lookup so any future
        SELECTOR_WHEN_ARGUED function is recognized here for free,
        without a new hand-written check per function. The OPPOSITE arg
        requirement from ':all()'/':flatten()'/':groups()'
        (WITH an argument, not without) mirrors
        _is_bare_fingerprint_reference()'s own original reasoning: a
        bare, argument-less call has no value to search a manifest
        for, so it is deliberately not recognized here."""
        if name_one.functions:
            return False
        if len(name_one.path) != 1 or not isinstance(
            name_one.path[0], FunctionCall3
        ):
            return False
        call = name_one.path[0]
        if call.arg is None:
            return False
        function_cls = ReferenceFunctionFactory.get_registered_class(call.name)
        return function_cls is not None and function_cls.SELECTOR_WHEN_ARGUED

    @staticmethod
    def _reject_selector_arg_outside_its_bare_form(f: FunctionCall3) -> None:
        """raises if `f` is a SELECTOR_WHEN_ARGUED function (e.g.
        :fingerprint()/:uuid()) carrying an argument OUTSIDE its bare,
        sole-name_one-content lookup form (_is_bare_selector_reference's
        own shape) -- i.e. riding alongside a matched entity in its
        ordinary field-accessor position instead. There, it reads
        whatever the matched entity's own value IS, it does not filter
        by a given one, so a caller that got this far already knows
        `f` is NOT the bare-selector shape itself. Generalized
        2026-10-18 from FilesReferenceFinder3's own original, hand-
        written ':fingerprint()'-specific check (added 2026-08-13),
        once :uuid() became a second SELECTOR_WHEN_ARGUED function
        needing the identical guard -- same registry-driven
        generalization _is_bare_selector_reference() itself already
        got from its own original bespoke, single-function check.
        Raising here avoids an arg being silently ignored, which a
        widened ARG_TYPES would otherwise allow through unnoticed
        (confirmed live before this generalization existed)."""
        function_cls = ReferenceFunctionFactory.get_registered_class(f.name)
        if (
            function_cls is not None
            and function_cls.SELECTOR_WHEN_ARGUED
            and f.arg is not None
        ):
            raise ReferenceException3(
                f":{f.name}() only takes an argument in its bare, "
                "name_one lookup form -- riding alongside a matched "
                "entity in its ordinary field-accessor position, it "
                "takes none."
            )

    @staticmethod
    def _matches_field_predicate(value, arg) -> bool:
        """generic test for a field-accessor's own predicate/exact-
        match argument -- added 2026-10-18 for ResultsReferenceFinder3's
        own ':error_count()' GATE (e.g. ":error_count(:above(3))"/
        ":error_count(0))", the first field accessor to carry one; moved
        up to this shared base the same day FilesReferenceFinder3 needed
        the identical mechanism for ':type()'s own GATE, rather than
        duplicate it a second time. A PredicateFunction3 arg (":above()"/
        ":below()", both built as dual-role range-bound/predicate
        classes) delegates to its own matches(); a bare leaf value (int/
        str) is an exact-match test instead -- no dedicated predicate
        class needed for ":error_count(0)"/":type(\"csv\")"."""
        if isinstance(arg, PredicateFunction3):
            return arg.matches(value)
        return value == arg

    def _resolve_value(self, value):
        """returns `value` unchanged if it is a plain literal (str, int,
        etc.); resolves it if it is a bare Variable3 (added 2026-08-27,
        alongside _build()/_build_chain() -- returns the RAW registered
        value, untouched, unlike the InterpolatedString3 case below,
        since a bare argument (e.g. :regex(@aregex)) may need to stay a
        real Regex3/int/whatever, not become text); evaluates it if it
        is an InterpolatedString3 -- each literal-str part passes
        through, each FunctionCall3 part is built and its compute()
        called (only SOURCE == "clock" functions are legal inside
        "{...}" for now -- see InterpolatedString3.check_valid(), which
        already restricts parts to ROLE == VALUE; a non-clock VALUE
        function landing here would mean check_valid() itself needs
        widening first, so this raises a clear error rather than
        silently mishandling it), each Variable3 PART is looked up the
        same way and stringified (interpolation always assembles one
        final string, unlike the bare-argument case above). Both
        Variable3 lookups read this finder's own registered
        self._variables (added 2026-08-26, compendium 3.12 -- "a
        reference finder can be given variables"; see set_variable()/
        set_variables()) and raise ReferenceRuntimeException3 (not the
        plain ReferenceException3 this used before 2026-08-27) if unset
        -- a reference using an unregistered @variable is not
        malformed, it is missing a runtime value it needs, the same
        static-vs-runtime distinction _resolve_arg() draws for a
        variable's resolved value having the wrong type. Instance
        method so this lookup has something to read from."""
        if isinstance(value, Variable3):
            if value.name not in self._variables:
                raise ReferenceRuntimeException3(
                    f"@{value.name} has no registered value -- call "
                    "set_variable()/set_variables() on this finder "
                    "before resolving a reference that uses it."
                )
            return self._variables[value.name]
        if not isinstance(value, InterpolatedString3):
            return value
        pieces = []
        for part in value.parts:
            if isinstance(part, str):
                pieces.append(part)
            elif isinstance(part, FunctionCall3):
                function_cls = ReferenceFunctionFactory.get_registered_class(
                    part.name
                )
                if function_cls is None or function_cls.SOURCE != "clock":
                    raise ReferenceException3(
                        f":{part.name}() cannot be evaluated inside "
                        "\"{...}\" interpolation yet -- only clock value "
                        "functions (e.g. :year()) are supported so far."
                    )
                built = self._build(part)
                pieces.append(str(built.compute()))
            elif isinstance(part, Variable3):
                if part.name not in self._variables:
                    raise ReferenceRuntimeException3(
                        f"@{part.name} has no registered value -- call "
                        "set_variable()/set_variables() on this finder "
                        "before resolving a reference that uses it."
                    )
                pieces.append(str(self._variables[part.name]))
            else:
                raise ReferenceException3(
                    f"{part!r} cannot be evaluated inside \"{{...}}\" "
                    "interpolation."
                )
        return "".join(pieces)

    def _build(self, call: FunctionCall3) -> Function3:
        """ReferenceFunctionFactory.build(), plus resolving this
        function's own arg in place -- added 2026-08-27 (David:
        "central eager resolve of args is right, certainly for now, at
        least"). A Variable3/InterpolatedString3 arg becomes its real,
        already-resolved value here, once, so no other code in any
        finder ever needs to know either of those two "deferred"
        argument shapes exist -- it just reads .arg and gets a plain
        value, exactly as it always could before @variable existed.
        Every call site that used to call ReferenceFunctionFactory.
        build()/build_chain() directly now calls this/`_build_chain()`
        instead -- a mechanical swap, not a behavior change for any
        existing (non-variable) reference, since _resolve_arg() is a
        no-op whenever an arg is neither of those two shapes."""
        built = ReferenceFunctionFactory.build(call)
        self._resolve_arg(built)
        return built

    def _build_chain(self, calls: list) -> list:
        """ReferenceFunctionFactory.build_chain(), plus resolving every
        function's own arg in place -- see _build()'s own docstring."""
        built = ReferenceFunctionFactory.build_chain(calls)
        for f in built:
            self._resolve_arg(f)
        return built

    def _resolve_arg(self, built: Function3) -> None:
        """the actual per-function resolution step shared by _build()/
        _build_chain() -- added 2026-08-27. Recurses into a nested
        function's own arg first (ReferenceFunctionFactory.build()'s
        own recursion already compiled it into a Function3 before this
        runs, so e.g. :errors(:idchain(@pattern))'s inner :idchain()
        gets the same treatment as any top-level call). Structural type
        validation of the arg's own SHAPE already happened inside
        build()'s check_valid() call, against Variable3/
        InterpolatedString3 themselves (Function3.check_valid()'s own
        ARG_TYPES widening) -- it could not check the RESOLVED value's
        own type, since resolution had not happened yet, and might
        never happen at all if set_variable() is never called. That
        check happens here instead, now that the real value is known --
        raises ReferenceRuntimeException3, not a plain
        ReferenceException3, since the reference itself was perfectly
        well-formed; only a variable's own runtime value did not
        satisfy it (see that exception class's own docstring)."""
        if isinstance(built.arg, Function3):
            self._resolve_arg(built.arg)
            return
        if not isinstance(built.arg, (Variable3, InterpolatedString3)):
            return
        original = built.arg
        resolved = self._resolve_value(original)
        if built.ARG_TYPES and not isinstance(resolved, built.ARG_TYPES):
            allowed = ", ".join(t.__name__ for t in built.ARG_TYPES)
            raise ReferenceRuntimeException3(
                f":{built.name}() argument {original} resolved to a "
                f"{type(resolved).__name__}, expected one of ({allowed})"
            )
        built.arg = resolved

    @staticmethod
    def _apply_key_arg(key_path: str | None, arg) -> str | None:
        """fills a "{}" placeholder in an arg-parameterized Function3.KEY
        dotted path with the field-accessor call's own arg -- e.g.
        "sources.{}.port".format("email") -> "sources.email.port".
        Added 2026-08-26 for the first field accessors whose manifest/
        definition key genuinely depends on a per-call value, not just
        the datatype (sources.<name>.*/destinations.<name>.*/
        transfers.path_transfers.<name>.on_complete_* -- see
        SourcePort3/DestinationPort3/TransferOnCompleteAll3's own
        docstrings for the worked argument). A no-op for every static,
        placeholder-free KEY (arg is None for those, or the path simply
        has no "{}" to fill) -- call this unconditionally before
        _extract_field_value()/_extract_field_value_with_ledger_
        fallback() rather than only for the functions that need it; it
        costs nothing for the ones that do not."""
        if key_path is None or arg is None:
            return key_path
        return key_path.format(arg)

    @staticmethod
    def _extract_field_value(container: dict | None, key_path: str) -> object:
        """walks a dotted key path (e.g. "on_arrival.named_paths_group")
        through a dict, returning None the moment any segment is missing
        or the container itself is None -- tolerant on purpose, matching
        the same "absence is normal, not an error" treatment already used
        for definition.json's own genuine optionality (see
        _read_well_known_file). Shared by every finder resolving a field-
        accessor function's Function3.KEY against either a manifest
        entry or a definition.json dict -- both are plain dicts by the
        time this is called, so the walk itself does not need to know
        which kind of resource it came from."""
        if container is None or key_path is None:
            return None
        value = container
        for segment in key_path.split("."):
            if not isinstance(value, dict) or segment not in value:
                return None
            value = value[segment]
        return value

    @classmethod
    def _extract_field_value_with_ledger_fallback(
        cls,
        *,
        entry: dict | None,
        key_path: str | None,
        function_cls: type,
        datatype: str,
        ledger_entry_getter,
    ) -> object:
        """like _extract_field_value(), but for SOURCE == "manifest"
        field accessors that also declare a Function3.LEDGER_KEY: if the
        entity's own manifest entry does not have the field, falls back
        to that same entity's own global-ledger entry instead of just
        returning None -- added 2026-08-25, see Function3.LEDGER_KEY's
        own docstring for why (some fields, e.g. a named-file's pointer
        back to its own manifest, only exist in the ledger, never in the
        entity's own manifest). `ledger_entry_getter` is a zero-arg
        callable, called only if actually needed, so a normal field
        lookup that succeeds against the entity's own manifest never
        pays for fetching/searching the ledger at all."""
        value = cls._extract_field_value(entry, key_path)
        if value is not None:
            return value
        ledger_key_path = function_cls.LEDGER_KEY.get(datatype)
        if ledger_key_path is None:
            return None
        ledger_entry = ledger_entry_getter()
        return cls._extract_field_value(ledger_entry, ledger_key_path)

    @staticmethod
    def _find_field_function_call(functions: list) -> "FunctionCall3 | None":
        """returns the first function in `functions` that is a
        registered field-accessor (its class declares a SOURCE), or None
        if none of them are. Shared by files/csvpaths finders to detect
        a field function (e.g. :uuid(), :on_arrival()) riding in the same
        terminal position :manifest() already rides in -- generalizing
        the existing bare-":manifest()"-name check without hardcoding
        each new field function's name at every call site."""
        for f in functions:
            function_cls = ReferenceFunctionFactory.get_registered_class(f.name)
            if function_cls is not None and function_cls.SOURCE is not None:
                return f
        return None

    @staticmethod
    def _find_field_function_calls(functions: list, datatype: str | None = None) -> list:
        """returns EVERY function in `functions` that is a registered
        field-accessor (its class declares a SOURCE), excluding any bare
        TimeWindowFunction3 (e.g. :yesterday()) -- that is its own,
        separately-handled category (see _apply_bare_time_window() and
        each finder's own `bare_time_window(s)` handling), not an
        ordinary field accessor, even though its own SOURCE == "clock"
        would otherwise match the same test _find_field_function_call()
        uses. Added 2026-10-18 (compendium 5.20b) so a caller can: (a)
        GATE candidates by EVERY argued field accessor in a chain,
        independent of position, not just the first one
        _find_field_function_call() finds; and (b) hand the full list to
        _last_field_function_call() to pick the correct resolve target.
        `datatype`, when given, also excludes a function not registered
        for THIS datatype at all (DATATYPES) -- without this, a
        function registered for a completely different datatype (e.g.
        ":webhooks()" riding in a RESULTS reference) would wrongly
        count as a qualifying field accessor too, something the old,
        single-match _find_field_function_call() never exposed (a
        wrong-datatype match simply was not THE one match returned, so
        it still fell through to the ordinary "unsupported extra"
        rejection elsewhere) -- confirmed live the moment this method
        started returning every match instead of just the first."""
        found = []
        for f in functions:
            if isinstance(f, TimeWindowFunction3):
                continue
            function_cls = ReferenceFunctionFactory.get_registered_class(f.name)
            if function_cls is None or function_cls.SOURCE is None:
                continue
            if datatype is not None and datatype not in function_cls.DATATYPES:
                continue
            found.append(f)
        return found

    def _last_field_function_call(self, functions: list) -> "FunctionCall3 | None":
        """returns the LAST qualifying field-accessor in `functions`
        (see _find_field_function_calls()) -- the one whose value
        resolve() actually returns, per compendium 5.20b ("in the case
        there are two possible interpretations of a reference's resolve
        value(s) due to there being multiple functions which could
        provide the value the last value-producing function wins").
        Added 2026-10-18, replacing _find_field_function_call()'s
        first-match behavior at every confirmed resolve-target call
        site (first-match was never a deliberate design choice there --
        it was simply what the single-match helper happened to return,
        confirmed live-wrong once a second field accessor could reach
        the same chain, e.g. CsvpathsReferenceFinder3's own
        ':last():uuid():named_paths_name()'). Logs a warning (never
        raises) whenever 2+ candidates qualify, since that is the
        genuinely ambiguous case compendium 5.20b exists to resolve --
        a single candidate is not ambiguous at all and is silent.

        Each distinct warning is logged once per finder (2026-11-13,
        reviewer on #590): query() and each result's extraction read the
        same chain, so one resolve() over N results logged it 1 + N
        times. A second finder warns again."""
        calls = self._find_field_function_calls(functions, self.ref.parsed.datatype)
        if len(calls) > 1:
            names = tuple(f.name for f in calls)
            if names not in self._warned:
                self._warned.add(names)
                self.csvpaths.logger.warning(
                    "Reference resolves to the value of the last field-"
                    "accessor function in its chain (:%s()) -- :%s() earlier "
                    "in the same chain could also have provided a value; "
                    "see compendium 5.20b.",
                    calls[-1].name,
                    "(), :".join(f.name for f in calls[:-1]),
                )
        return calls[-1] if calls else None

    @staticmethod
    def _find_by_identity(identity: str, identities: list) -> int | None:
        """returns the index of `identity` within `identities` (exact
        string match), or None if absent. shared by any finder whose
        name_three does an identity lookup -- csvpaths'
        named_paths_identities and results' per-statement directory
        names both name individual csvpath statements the same way: an
        explicit id/name comment, or the stringified run index if the
        statement is unnamed -- so a plain list membership check
        handles both without needing a separate "or try as an int"
        fallback."""
        try:
            return identities.index(identity)
        except ValueError:
            return None
