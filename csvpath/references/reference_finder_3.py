import json
from abc import ABC, abstractmethod
from datetime import datetime

from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos

from .functions.reference_function_factory_3 import ReferenceFunctionFactory
from .reference_3 import FunctionCall3, Reference3, Star3
from .reference_exceptions_3 import ReferenceException3
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
    def __init__(self, *, csvpaths, ref: ReferenceParser3) -> None:
        if csvpaths is None:
            raise ValueError("Csvpaths cannot be None")
        if ref is None:
            raise ValueError("Reference cannot be None")
        self._csvpaths = csvpaths
        self._ref = ref

    @property
    def ref(self) -> ReferenceParser3:
        return self._ref

    @property
    def csvpaths(self):
        return self._csvpaths

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
        """
        if isinstance(selection, ReferenceResults3):
            results = selection
        else:
            results = self.query().select(selection)
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

    @staticmethod
    def _compile_path_pattern(path: list) -> list:
        """turns a name_one path into a list of str/Star3 to match
        against real path segments (a manifest entry's file_home for
        files, real directory names for results). a literal str or
        Star3 segment passes through unchanged; a :name("...") segment
        is compiled and unwrapped to its literal string, so matching
        downstream doesn't need to know the difference -- built
        specifically because a literal name containing characters a
        bare PATH_SEGMENT cannot hold (e.g. a real filename's ".") has
        no other way to appear. any other function-valued segment is
        explicitly not yet supported. shared by files and results --
        both have a real, literal/star/:name(...) path to match; csvpaths
        does not (its whole name_one is version-selecting functions)."""
        pattern = []
        for segment in path:
            if isinstance(segment, FunctionCall3):
                if segment.name != "name":
                    raise ReferenceException3(
                        f"Does not yet support :{segment.name}() as a "
                        "name_one path segment -- only :name(\"...\") and "
                        "literal/'*' segments are supported."
                    )
                built = ReferenceFunctionFactory.build(segment)
                pattern.append(built.arg)
            elif isinstance(segment, (str, Star3)):
                pattern.append(segment)
            else:
                raise ReferenceException3(f"Unsupported name_one path segment: {segment!r}")
        return pattern

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
    def _find_path_call(functions: list) -> "FunctionCall3 | None":
        """returns the first ":path(...)" call in `functions`, or None
        if absent. Checked by literal name rather than a registry
        lookup, since ":path()" is a single fixed name, not a growing
        list of field-accessor names -- matching how ":manifest()"
        itself is already detected by name elsewhere in these finders."""
        for f in functions:
            if f.name == "path":
                return f
        return None

    @staticmethod
    def _resolve_path_call(path_call, home: str) -> str:
        """given a raw ":path(inner)" FunctionCall3 and the already-
        computed home directory for the enclosing entity, returns the
        filesystem path to whatever well-known file `inner` names.
        :manifest()/:definition() are the only ones available at the
        FILES/CSVPATHS datatypes this covers so far -- see wrappers/
        path_3.py. Shared by files/csvpaths: home is computed
        differently per datatype (named_file_home vs named_paths_home),
        but the join is identical once you have it."""
        inner = path_call.arg
        inner_name = inner.name if inner is not None else None
        if inner_name not in ("manifest", "definition"):
            raise ReferenceException3(
                f":path() does not yet support wrapping :{inner_name}() -- "
                "only :manifest()/:definition() are supported so far."
            )
        filename = f"{inner_name}.json"
        return ReferenceFinder3._query_well_known_file(home, filename).results[
            0
        ].path

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
