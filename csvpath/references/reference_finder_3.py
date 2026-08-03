from abc import ABC, abstractmethod

from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos

from .reference_3 import FunctionCall3, Reference3
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
