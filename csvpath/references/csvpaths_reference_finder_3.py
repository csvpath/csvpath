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
    #  - name_one IS the version selector for csvpaths (STRUCTURE table:
    #    "name_one is always one or more versions of a named-paths
    #    group's group.csvpaths file"). Its combined function chain
    #    (the sole path-segment function plus any trailing chain) may
    #    contain at most one pointer function (:first()/:last()/
    #    :index(n)): if present, it reduces to that one version; if
    #    absent (e.g. a bare :all()), every version in the manifest is
    #    returned, unreduced -- this is how "list of versions in the
    #    form: (path-to-group.csvpaths, uuid)" (STRUCTURE table) is
    #    actually reached. ":manifest()" may ride alongside the version
    #    pointer in this same combined chain (e.g. ":last():manifest()")
    #    -- it never narrows/selects itself (see functions/manifest_3.py),
    #    it just changes what _extract_data() resolves to: the matched
    #    version's own manifest entry, instead of its statement text.
    #    Literal/"*"/path-building content, and the
    #    "#worksheet" marker (name_two, files-only), are not meaningful
    #    for csvpaths and are rejected. :uuid() is not yet a registered
    #    function, so it is "not yet supported" for now like any other
    #    unbuilt function.
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

        if self._is_bare_pointer_reference(
            reference, "manifest"
        ) or self._is_bare_pointer_reference(reference, "definition"):
            # both ":manifest()" and ":definition()" are a bare, sole-
            # content name_one whose function name IS the JSON file's
            # own name (manifest.json/definition.json) -- see
            # _query_well_known_file() on the ABC.
            home = self.csvpaths.paths_manager.named_paths_home(root_major)
            filename = f"{name_one.path[0].name}.json"
            return self._query_well_known_file(home, filename)

        manifest = self.csvpaths.paths_manager.get_manifest_for_name(root_major)
        selected_versions = self._resolve_versions(name_one, manifest)

        if len(selected_versions) > 1:
            combined = [
                seg
                for seg in (name_one.path[0], *name_one.functions)
                if isinstance(seg, FunctionCall3)
            ]
            has_manifest = any(
                seg.contains_function_named("manifest") for seg in combined
            )
            if has_manifest:
                # Resolving full manifest content always touches exactly
                # one entity (settled 2026-08-07, see manifest_field_
                # functions_proposal.md's "Entity resolution and pooling"
                # section) -- more than one version here needs a pointer
                # to pick which one.
                raise ReferenceException3(
                    "CsvpathsReferenceFinder3 requires a pointer (:first()/"
                    ":last()/:index(n)) to pick one version when combining "
                    ":manifest() with no pointer matches more than one "
                    "version -- resolving full manifest content always "
                    "touches exactly one entity."
                )

        name_three = reference.name_three
        if name_three is not None:
            if name_three.functions:
                raise ReferenceException3(
                    "CsvpathsReferenceFinder3 does not yet support functions "
                    "on name_three -- no metadata-access functions are "
                    "registered for csvpaths yet."
                )
            if name_three.body is None or isinstance(name_three.body, Star3):
                raise ReferenceException3(
                    "CsvpathsReferenceFinder3 requires name_three to be a "
                    "literal statement identity or index."
                )

        results = []
        for selected in selected_versions:
            if name_three is not None:
                identities = selected.get("named_paths_identities") or []
                if self._find_by_identity(name_three.body, identities) is None:
                    continue
            results.append(
                ReferenceResult3(
                    path=selected["group_file_path"], uuid=selected["uuid"]
                )
            )
        return ReferenceResults3(results=results)

    def _extract_data(self, result: ReferenceResult3):
        reference = self.ref.parsed
        kind = reference.resolve_kind
        if kind == Reference3.METADATA_FILE:
            if self._is_bare_pointer_reference(
                reference, "manifest"
            ) or self._is_bare_pointer_reference(reference, "definition"):
                # result.path is already the manifest.json/definition.json
                # path itself (set by query()'s _query_well_known_file()
                # branch above).
                return self._read_well_known_file(result.path)
            name_one = reference.name_one
            has_manifest = any(
                seg.contains_function_named("manifest")
                for seg in (name_one.path[0], *name_one.functions)
                if isinstance(seg, FunctionCall3)
            )
            if has_manifest:
                # :manifest() riding alongside the real version-selecting
                # pointer already in name_one's own combined chain (e.g.
                # ":last():manifest()") -- give the matched version's own
                # manifest entry, not the whole raw file.
                manifest = self.csvpaths.paths_manager.get_manifest_for_name(
                    reference.root_major
                )
                return self._find_manifest_entry_by_uuid(manifest, result.uuid)
        if kind != Reference3.FIRST_PARTY:
            raise ReferenceException3(
                f"CsvpathsReferenceFinder3 does not yet support "
                f"resolve_kind={kind!r} -- only :manifest()/:definition() "
                "are wired up as metadata-file functions so far."
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
        selected = self._find_manifest_entry_by_uuid(manifest, result.uuid)
        if selected is None:
            return None
        identities = selected.get("named_paths_identities") or []
        index = self._find_by_identity(name_three.body, identities)
        if index is None:
            return None
        statements = selected.get("named_paths") or []
        return statements[index]

    def _resolve_versions(self, name_one, manifest: list) -> list:
        """name_one's sole job for csvpaths is selecting which
        version(s) to work with, so its path_prefix must reduce to
        exactly one function-segment (no literal/"*" path-building, no
        worksheet marker) -- combined with its own trailing function
        chain, if any. At most one pointer function is allowed among
        the combined chain (build_chain() enforces this): if present,
        it reduces `manifest` to that one version; if absent (e.g. a
        bare :all()), every version in `manifest` is returned,
        unreduced."""
        if len(name_one.path) != 1 or not isinstance(name_one.path[0], FunctionCall3):
            raise ReferenceException3(
                "CsvpathsReferenceFinder3 requires name_one to be a version-"
                "selecting function chain (e.g. :last(), :all()) -- "
                "literal/'*' path-building is not meaningful for csvpaths."
            )
        calls = [name_one.path[0], *name_one.functions]
        built = ReferenceFunctionFactory.build_chain(calls)
        pointers = [f for f in built if f.ROLE == Function3.POINTER]
        if not pointers:
            return manifest
        selected = self._apply_pointer(pointers[0], manifest)
        return [selected] if selected is not None else []
