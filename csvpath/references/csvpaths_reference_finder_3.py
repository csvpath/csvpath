from .functions.function_3 import Function3
from .functions.reference_function_factory_3 import ReferenceFunctionFactory
from .reference_3 import FunctionCall3, Reference3, Star3
from .reference_exceptions_3 import ReferenceException3
from .reference_finder_3 import ReferenceFinder3
from .reference_results_3 import ReferenceResult3, ReferenceResults3


class CsvpathsReferenceFinder3(ReferenceFinder3):
    #
    # first pass, deliberately narrow, mirroring FilesReferenceFinder3's
    # scoping approach -- but note the roles of name_one/name_three are
    # REVERSED from files here:
    #  - root_major is a literal named-paths group name. "*" (every
    #    group) is a different traversal problem, not yet built.
    #  - name_one IS the version pointer for csvpaths (STRUCTURE table:
    #    "name_one is always one or more versions of a named-paths
    #    group's group.csvpaths file"). It must resolve, via
    #    build_chain(), to exactly one pointer function
    #    (:first()/:last()/:index(n)). Literal/"*"/path-building
    #    content, and the "#worksheet" marker (name_two, files-only),
    #    are not meaningful for csvpaths and are rejected. :uuid() is
    #    not yet a registered function, so it is "not yet supported"
    #    for now like any other unbuilt function.
    #  - name_three, if present, is an identity lookup into that
    #    version's named_paths_identities list -- matched by identity
    #    string, or by the stringified index an unnamed statement is
    #    given at load time (both already live in
    #    named_paths_identities, so a single exact-match lookup covers
    #    both cases). A function chain on name_three is not yet
    #    supported -- no metadata-access functions exist yet for
    #    csvpaths (see "creating references v3.txt"'s † footnote on
    #    this).
    #
    # storage facts this relies on (confirmed against PathsManager/
    # PathsRegistrar and the real per-group manifest schema, not
    # assumed): a named-paths group's manifest.json is one flat,
    # append-only JSON array, one entry per loaded/reloaded version of
    # the WHOLE group -- there is only one group.csvpath file, always
    # the same path, regardless of version. Each entry's "named_paths"
    # is a list of that version's individual csvpath statement source
    # strings, and "named_paths_identities" is a parallel list of each
    # statement's name/id (or its stringified load-time index, if
    # unnamed). Arrival order is simply array order.
    #

    def query(self) -> ReferenceResults3:
        reference = self.ref.parsed
        root_major = reference.root_major
        if isinstance(root_major, Star3):
            raise ReferenceException3(
                "CsvpathsReferenceFinder3 does not yet support '*' as "
                "root_major (querying every named-paths group) -- use a "
                "literal group name."
            )

        name_one = reference.name_one
        if name_one.name_two is not None:
            raise ReferenceException3(
                "CsvpathsReferenceFinder3 does not support the '#worksheet' "
                "marker (name_two) -- it is files-only."
            )
        pointer = self._resolve_version_pointer(name_one)

        manifest = self.csvpaths.paths_manager.get_manifest_for_name(root_major)
        selected = self._apply_pointer(pointer, manifest)
        if selected is None:
            return ReferenceResults3(results=[])

        result = ReferenceResult3(
            path=selected["group_file_path"], uuid=selected["uuid"]
        )

        name_three = reference.name_three
        if name_three is None:
            return ReferenceResults3(results=[result])

        if name_three.functions:
            raise ReferenceException3(
                "CsvpathsReferenceFinder3 does not yet support functions on "
                "name_three -- no metadata-access functions are registered "
                "for csvpaths yet."
            )
        if name_three.body is None or isinstance(name_three.body, Star3):
            raise ReferenceException3(
                "CsvpathsReferenceFinder3 requires name_three to be a "
                "literal statement identity or index."
            )
        identities = selected.get("named_paths_identities") or []
        if self._find_by_identity(name_three.body, identities) is None:
            return ReferenceResults3(results=[])
        return ReferenceResults3(results=[result])

    def _extract_data(self, result: ReferenceResult3):
        reference = self.ref.parsed
        kind = reference.resolve_kind
        if kind != Reference3.FIRST_PARTY:
            raise ReferenceException3(
                f"CsvpathsReferenceFinder3 does not yet support "
                f"resolve_kind={kind!r} -- no metadata-access functions are "
                "registered for csvpaths yet."
            )
        name_three = reference.name_three
        if name_three is None:
            # a whole group version has no single unambiguous payload --
            # the same "no default" rule as a directory-level, name_one-
            # terminal result in FilesReferenceFinder3.
            return None

        manifest = self.csvpaths.paths_manager.get_manifest_for_name(
            reference.root_major
        )
        selected = next(
            (entry for entry in manifest if entry["uuid"] == result.uuid), None
        )
        if selected is None:
            return None
        identities = selected.get("named_paths_identities") or []
        index = self._find_by_identity(name_three.body, identities)
        if index is None:
            return None
        statements = selected.get("named_paths") or []
        return statements[index]

    @staticmethod
    def _resolve_version_pointer(name_one) -> Function3:
        """name_one's sole job for csvpaths is being the version
        pointer, so its path_prefix must reduce to exactly one
        function-segment (no literal/"*" path-building, no worksheet
        marker) -- combined with its own trailing function chain, if
        any, and required to resolve to exactly one pointer function
        overall (e.g. :before(:yesterday()):after(...):index(3))."""
        if len(name_one.path) != 1 or not isinstance(name_one.path[0], FunctionCall3):
            raise ReferenceException3(
                "CsvpathsReferenceFinder3 requires name_one to be a version-"
                "selecting function chain (e.g. :last(), :index(3)) -- "
                "literal/'*' path-building is not meaningful for csvpaths."
            )
        calls = [name_one.path[0], *name_one.functions]
        built = ReferenceFunctionFactory.build_chain(calls)
        pointers = [f for f in built if f.ROLE == Function3.POINTER]
        if len(pointers) != 1:
            raise ReferenceException3(
                "CsvpathsReferenceFinder3 requires name_one to resolve to "
                "exactly one pointer function (:first()/:last()/:index(n))."
            )
        return pointers[0]
