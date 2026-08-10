import json
from abc import ABC, abstractmethod

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
        """returns the pointer function call riding immediately before a
        bare ":name()" call in name_one (e.g. "$*.files.:last():manifest()"
        parses as name_one.path == [:last()], name_one.functions ==
        [:manifest()]), or None if this reference is not shaped that
        way. Ordinal indexing into a global ledger (Rule 1b,
        manifest_field_functions_proposal.md) -- a pointer here selects
        one entry out of the whole ledger array, same position-based
        selection _apply_pointer() already does for a named entitys own
        manifest, just applied to the ledger instead. Shared by files/
        csvpaths/results since all three ledgers are flat arrays in
        arrival order."""
        name_one = reference.name_one
        if reference.name_three is not None:
            return None
        if len(name_one.path) != 1 or len(name_one.functions) != 1:
            return None
        pointer_call = name_one.path[0]
        manifest_call = name_one.functions[0]
        if not isinstance(pointer_call, FunctionCall3) or pointer_call.name not in (
            "first",
            "last",
            "index",
        ):
            return None
        if (
            not isinstance(manifest_call, FunctionCall3)
            or manifest_call.name != name
            or manifest_call.arg is not None
        ):
            return None
        return pointer_call

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
