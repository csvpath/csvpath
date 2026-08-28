import json
import re
from abc import ABC, abstractmethod
from datetime import datetime

from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos

from .functions.function_3 import Function3
from .functions.reference_function_factory_3 import ReferenceFunctionFactory
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
    def _range_bound(function) -> "int | str":
        """the plain int/str value a built ':from()'/':to()' function's
        arg represents -- handles bare leaf values (int for index-mode,
        str for date-mode, added 2026-08-13) and nested wrapper
        functions (":index(n)"/":date(...)"), which
        ReferenceFunctionFactory.build() already recursively compiled
        into a real Index3/Date3 instance (not a plain int/str) by the
        time this function exists -- see From3/To3's own comments for
        why every shape must be accepted."""
        arg = function.arg
        if isinstance(arg, (int, str)):
            return arg
        return arg.arg

    @classmethod
    def _apply_range(cls, items: list, from_call, to_call) -> list:
        """slices `items` (already in the scope's own natural order)
        using ':from()'/':to()' -- added 2026-08-13, RESULTS' index-mode
        range selector, David's own framing: "our version of BETWEEN in
        SQL or range() in Python." ':to()' is INCLUSIVE of its own
        position (matches SQL BETWEEN and :index(n) itself pointing AT a
        position -- ':from(2):to(5)' is positions 2 through 5, both
        ends included). Either bound may be absent (an open range on
        that side); negative bounds count from the end, same convention
        :index(n) already has -- Python slicing already does the right
        thing there natively, no special-casing needed except when
        :to()'s own bound is exactly -1 (the last item): "+1" for
        inclusivity would otherwise wrap -1 to 0, which means "nothing"
        in a slice, not "to the end" -- that one case needs an explicit
        fix, everything else falls out of ordinary slice semantics."""
        start = cls._range_bound(from_call) if from_call is not None else None
        if to_call is None:
            return items[start:]
        end = cls._range_bound(to_call)
        if end == -1:
            return items[start:]
        return items[start : end + 1]

    @staticmethod
    def _validate_date_format(value: str) -> None:
        """raises unless `value` is a real calendar date in "YYYY-MM-DD"
        form -- shared 2026-08-13 (previously RESULTS-only) alongside
        FILES/CSVPATHS getting their own date-mode ':from()'/':to()'.
        Function3.check_valid()'s own generic ARG_TYPES check only
        confirms an arg is A str, not that its CONTENT is a valid date --
        a malformed date bound would otherwise be silently compared as
        an ordinary string (no crash, just a meaningless answer), which
        is worse than a clear, immediate rejection."""
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ReferenceException3(
                "date-mode ':from()'/':to()' requires a real calendar "
                f"date in 'YYYY-MM-DD' form, got {value!r}."
            ) from None

    @staticmethod
    def _apply_manifest_date_range(
        entries: list, from_date: str | None, to_date: str | None, key: str = "time"
    ) -> list:
        """filters `entries` (manifest-entry dicts) to those whose own
        `entries[i][key]` (an ISO datetime string, e.g. FILES/CSVPATHS'
        own "time" field -- registration/load time, see functions/
        fields/time_3.py's own SUMMARY) falls within [from_date, to_date],
        both INCLUSIVE -- date-mode ':from()'/':to()' for FILES/CSVPATHS,
        added 2026-08-13. Unlike index-mode (_apply_range, a POSITIONAL
        slice), this is a FILTER, not a slice -- comparing positions
        would be meaningless for a date bound. Compares only the first
        10 characters (the "YYYY-MM-DD" date portion) of the stored
        timestamp -- ISO date strings sort/compare lexicographically in
        true chronological order, so plain string comparison is correct,
        not just convenient (same convention ResultsReferenceFinder3's
        own _run_dir_date/_apply_date_range already use for run
        directories -- here the date comes straight from a stored field
        instead of being parsed from a path, since FILES/CSVPATHS
        manifest entries already carry it directly)."""
        result = []
        for entry in entries:
            d = str(entry.get(key, ""))[:10]
            if from_date is not None and d < from_date:
                continue
            if to_date is not None and d > to_date:
                continue
            result.append(entry)
        return result

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
        (nothing has ever been logged)."""
        if not Nos(path).exists():
            return None
        with DataFileReader(path=path) as reader:
            text = reader.source.read()
        if lines is None:
            return text
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
        if not Nos(path).exists():
            return None
        with DataFileReader(path) as reader:
            return json.load(reader.source)

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
                function_cls = ReferenceFunctionFactory.get_registered_class(
                    segment.name
                )
                if function_cls is None or function_cls.SOURCE != "clock":
                    raise ReferenceException3(
                        f"Does not yet support :{segment.name}() as a "
                        "name_one path segment -- only :name(\"...\"), a "
                        "clock value function (e.g. :year()), and "
                        "literal/'*' segments are supported."
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
    def _pointer_present(calls: list) -> bool:
        """true if any function in `calls` is a real, top-level version-
        selecting pointer (:first()/:last()/:index()) -- used to decide,
        for a Function3.BARE_SOURCE-declaring field accessor (currently
        only :template()), whether a specific version was actually
        selected (read that version's own manifest snapshot, the
        ordinary SOURCE) or not (read the entity's current
        definition.json default instead, BARE_SOURCE). Added 2026-08-26.
        Uses the same literal-name check already established in
        _pointer_before_manifest() above, rather than a registry lookup
        -- deliberately narrow/cheap, matching that precedent."""
        return any(
            isinstance(f, FunctionCall3) and f.name in ("first", "last", "index")
            for f in calls
        )

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
