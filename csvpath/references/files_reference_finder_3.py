from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos

from .functions.function_3 import Function3
from .functions.reference_function_factory_3 import ReferenceFunctionFactory
from .reference_3 import FunctionCall3, Reference3, Star3
from .reference_exceptions_3 import ReferenceException3
from .reference_finder_3 import ReferenceFinder3
from .reference_results_3 import ReferenceResult3, ReferenceResults3


class FilesReferenceFinder3(ReferenceFinder3):
    #
    # first pass, deliberately narrow:
    #  - root_major is a literal named-file name, or "*" (every named-
    #    file). "*" has two exceptions carved out before general
    #    traversal (Rule 1a/1b, a bare/ordinal-indexed :manifest() reads
    #    the global arrivals ledger, see _pointer_before_manifest); any
    #    other use of "*" goes through _query_star_traversal(), which
    #    implements the spec's flatten (bare '*'/path narrowing, pooled
    #    and reduced by one pointer) vs. group (bare ':all()', one
    #    result per named-file+path pair) semantics -- deliberately
    #    narrow itself: combining '*' traversal with :manifest()/:path()/
    #    a field-accessor function is not yet supported, see that
    #    method's own docstring.
    #  - name_one is "*", a literal path segment, or :name("...") (for a
    #    literal name containing characters -- e.g. a real filename's
    #    "." -- that cannot appear in a bare PATH_SEGMENT). any other
    #    function-valued segment (e.g. :quarter()) and the "#worksheet"
    #    marker (name_two) are not yet supported.
    #  - name_three, if present, must resolve to exactly one pointer
    #    function (:first()/:last()/:index(n)) -- matching the
    #    STRUCTURE table: name_one picks *which file*, name_three picks
    #    *which version*. A literal name_three body (bypassing a
    #    pointer function entirely) is not yet supported. ":manifest()"
    #    may ride alongside the pointer (e.g. ":last():manifest()" --
    #    the matched version's own manifest entry) or appear alone with
    #    no pointer at all (e.g. ":manifest()" alone -- every matching
    #    version's entry, unreduced) -- it never narrows/selects itself,
    #    see functions/manifest_3.py. name_three is
    #    optional: when absent, name_one alone is a prefix search that
    #    returns zero or more paths to file-home directories (one per
    #    distinct file matched, deduplicated across versions) -- per
    #    "creating references v3.txt"'s "Query Vs. Resolve" section.
    #    These directory-level results carry uuid=None: a directory
    #    isn't a specific registered version, so it has no uuid of its
    #    own in the manifest schema.
    #
    # storage facts this relies on (confirmed against FileManager/
    # FileRegistrar and a real manifest.json, not assumed): a named-
    # file's manifest.json is one flat, append-only JSON array covering
    # every version of every distinct file ever registered under that
    # name. Each entry's "file_home" is the directory shared by every
    # version of the same logical file; arrival order is simply array
    # order (not sorted by the "time" field).
    #

    def query(self) -> ReferenceResults3:
        reference = self.ref.parsed
        root_major = reference.root_major
        if isinstance(root_major, Star3):
            if self._is_bare_pointer_reference(reference, "manifest"):
                # Rule 1a (manifest_field_functions_proposal.md): "*" at
                # root_major combined with a bare :manifest() is the one
                # exception -- it resolves to the Named-File Arrivals
                # Manifest, a single global ledger at the named-files
                # root tracking every arrival across every named-file
                # (see files_listener.py). :definition() has no
                # equivalent global resource, so it stays unsupported
                # here, same as any other function.
                home = self.csvpaths.config.inputs_files_path
                return self._query_well_known_file(home, "manifest.json")
            pointer_call = self._pointer_before_manifest(reference, "manifest")
            if pointer_call is not None:
                # Rule 1b -- a pointer riding before the bare :manifest()
                # (e.g. "$*.files.:last():manifest()") selects one entry
                # out of the global ledger by ordinal position, instead
                # of dumping the whole thing.
                home = self.csvpaths.config.inputs_files_path
                path = Nos(home).join("manifest.json")
                ledger = self.csvpaths.file_manager.files_root_manifest
                selected = self._apply_pointer(pointer_call, ledger)
                if selected is None:
                    return ReferenceResults3(results=[])
                return ReferenceResults3(
                    results=[ReferenceResult3(path=path, uuid=selected["uuid"])]
                )
            return self._query_star_traversal(reference)

        name_one = reference.name_one
        if name_one.name_two is not None:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not yet support the '#worksheet' "
                "marker (name_two)."
            )

        if self._is_bare_pointer_reference(
            reference, "manifest"
        ) or self._is_bare_pointer_reference(reference, "definition"):
            # both ":manifest()" and ":definition()" are a bare, sole-
            # content name_one whose function name IS the JSON file's
            # own name (manifest.json/definition.json) -- see
            # _query_well_known_file() on the ABC.
            home = self.csvpaths.file_manager.named_file_home(root_major)
            filename = f"{name_one.path[0].name}.json"
            return self._query_well_known_file(home, filename)

        if name_one.functions:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not yet support functions attached "
                "directly to name_one -- put the version-selecting function in "
                "name_three instead."
            )
        pattern = self._compile_path_pattern(name_one.path)
        candidates = self._candidates_for_name(root_major, pattern)

        name_three = reference.name_three
        if name_three is None:
            file_homes = []
            for entry in candidates:
                if entry["file_home"] not in file_homes:
                    file_homes.append(entry["file_home"])
            return ReferenceResults3(
                results=[
                    ReferenceResult3(path=file_home, uuid=None)
                    for file_home in file_homes
                ]
            )

        if name_three.body is not None:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not yet support a literal name_three "
                "body -- name_three must resolve to a pointer function "
                "(:first()/:last()/:index(n))."
            )
        built = ReferenceFunctionFactory.build_chain(name_three.functions)
        pointers = [f for f in built if f.ROLE == Function3.POINTER]
        has_manifest = any(f.name == "manifest" for f in built)
        has_field_function = self._find_field_function_call(built) is not None
        has_path = self._find_path_call(built) is not None
        if not pointers and not has_manifest and not has_field_function and not has_path:
            raise ReferenceException3(
                "FilesReferenceFinder3 requires name_three to resolve to "
                "exactly one pointer function (:first()/:last()/:index(n)), "
                "optionally combined with :manifest(), :path(), or a "
                "registered field-accessor function (e.g. :uuid())."
            )

        if pointers:
            # a pointer (with or without :manifest() riding alongside it)
            # reduces to one specific version, same as before.
            selected = self._apply_pointer(pointers[0], candidates)
            selected_candidates = [selected] if selected is not None else []
        else:
            # :manifest() alone, no pointer -- legal only when name_one's
            # own path narrowing already resolves to at most one version.
            # Resolving full manifest content always touches exactly one
            # entity (settled 2026-08-07, see manifest_field_functions_
            # proposal.md's "Entity resolution and pooling" section) --
            # more than one candidate here needs a pointer to pick which
            # one. Field accessors and :path() are deliberately exempt
            # (Rules 2/3 in the same doc section) -- a scalar field value
            # or a path string is cheap to pool, unlike raw manifest
            # content, so :uuid()/:path(...) etc. stay poolable across
            # every matched candidate with no pointer at all.
            if has_manifest and len(candidates) > 1:
                raise ReferenceException3(
                    "FilesReferenceFinder3 requires a pointer (:first()/"
                    ":last()/:index(n)) to pick one version when combining "
                    ":manifest() with path narrowing that matches more "
                    "than one version -- resolving full manifest content "
                    "always touches exactly one entity."
                )
            selected_candidates = candidates

        return ReferenceResults3(
            results=[
                ReferenceResult3(path=c["file"], uuid=c["uuid"])
                for c in selected_candidates
            ]
        )

    def _query_star_traversal(self, reference: Reference3) -> ReferenceResults3:
        """root_major == "*" -- query across every named-file, not just
        one. Two distinct semantics (per "Why a trailing bare '*' is
        illegal but bare ':all()' is fine" in the spec compendium):

        - bare '*'/literal path narrowing (FLATTEN): every named-file's
          matching candidates pool into one combined list, sorted by
          each entry's own "time" so a terminal pointer means true
          chronological order across everything, not enumeration order.
        - bare ':all()' as name_one's entire content (GROUP): every
          matching candidate across every named-file is partitioned by
          its own "file_home" (already unique per named-file+path, since
          file_home embeds the named-file's name as a path prefix), and
          the terminal pointer is applied independently within each
          group -- one result per (named-file, path) pair, each that
          pair's own last/first/nth version in its own array order (no
          time-sort needed within one already-single-manifest group).

        Deliberately narrow for now, matching only the spec's own worked
        examples: combining '*' traversal with :manifest()/:path()/a
        field-accessor function in name_three is not yet supported --
        those all assume exactly one already-known manifest to re-read
        in _extract_data(), which does not hold when a result could have
        come from any of several named-files' manifests.
        """
        name_one = reference.name_one
        if name_one.name_two is not None:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not yet support the '#worksheet' "
                "marker (name_two)."
            )
        is_grouped = self._is_bare_all_reference(name_one)
        if is_grouped:
            candidates = []
            for name in self.csvpaths.file_manager.named_file_names:
                candidates.extend(self._all_candidates_for_name(name))
        else:
            if name_one.functions:
                raise ReferenceException3(
                    "FilesReferenceFinder3 does not yet support functions "
                    "attached directly to name_one for '*' traversal -- put "
                    "the version-selecting function in name_three instead."
                )
            pattern = self._compile_path_pattern(name_one.path)
            candidates = []
            for name in self.csvpaths.file_manager.named_file_names:
                candidates.extend(self._candidates_for_name(name, pattern))

        name_three = reference.name_three
        if name_three is None:
            file_homes = []
            for entry in candidates:
                if entry["file_home"] not in file_homes:
                    file_homes.append(entry["file_home"])
            return ReferenceResults3(
                results=[
                    ReferenceResult3(path=file_home, uuid=None)
                    for file_home in file_homes
                ]
            )

        if name_three.body is not None:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not yet support a literal name_three "
                "body -- name_three must resolve to a pointer function "
                "(:first()/:last()/:index(n))."
            )
        built = ReferenceFunctionFactory.build_chain(name_three.functions)
        pointers = [f for f in built if f.ROLE == Function3.POINTER]
        unsupported = (
            any(f.name == "manifest" for f in built)
            or self._find_field_function_call(built) is not None
            or self._find_path_call(built) is not None
        )
        if unsupported:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not yet support combining '*' "
                "traversal with :manifest(), :path(), or a field-accessor "
                "function -- only a plain pointer (:first()/:last()/"
                ":index(n)) is supported so far."
            )
        if not pointers:
            raise ReferenceException3(
                "FilesReferenceFinder3 requires name_three to resolve to "
                "exactly one pointer function (:first()/:last()/:index(n)) "
                "when traversing every named-file with '*'."
            )
        pointer = pointers[0]

        if is_grouped:
            by_file_home = {}
            for entry in candidates:
                by_file_home.setdefault(entry["file_home"], []).append(entry)
            selected_candidates = []
            for file_home in sorted(by_file_home):
                selected = self._apply_pointer(pointer, by_file_home[file_home])
                if selected is not None:
                    selected_candidates.append(selected)
        else:
            pooled = sorted(candidates, key=lambda e: e["time"])
            selected = self._apply_pointer(pointer, pooled)
            selected_candidates = [selected] if selected is not None else []

        return ReferenceResults3(
            results=[
                ReferenceResult3(path=c["file"], uuid=c["uuid"])
                for c in selected_candidates
            ]
        )

    def _candidates_for_name(self, name: str, pattern: list) -> list:
        """every manifest entry for one named-file whose file_home
        matches `pattern` relative to that name's own home directory --
        the per-name-file work shared by both the literal-root_major
        path and '*' traversal's flatten mode."""
        manifest = self.csvpaths.file_manager.get_manifest(name)
        home = self.csvpaths.file_manager.named_file_home(name).rstrip("/")
        return [entry for entry in manifest if self._matches(entry, home, pattern)]

    def _all_candidates_for_name(self, name: str) -> list:
        """every manifest entry for one named-file, at any path depth --
        ':all()' matches unconditionally, unlike a pattern (which must
        match an exact segment count), so this skips _matches entirely."""
        manifest = self.csvpaths.file_manager.get_manifest(name)
        home = self.csvpaths.file_manager.named_file_home(name).rstrip("/")
        return [
            entry
            for entry in manifest
            if entry["file_home"].rstrip("/").startswith(home)
        ]

    @staticmethod
    def _is_bare_all_reference(name_one) -> bool:
        """true when name_one's entire content is a single, argument-
        less ':all()' call, with no trailing function chain -- name_three
        (the per-group reduction function) is independent and may or may
        not be present, unlike _is_bare_pointer_reference's shape."""
        return (
            not name_one.functions
            and len(name_one.path) == 1
            and isinstance(name_one.path[0], FunctionCall3)
            and name_one.path[0].name == "all"
            and name_one.path[0].arg is None
        )

    def _extract_data(self, result: ReferenceResult3):
        reference = self.ref.parsed
        # :path(...) is checked before resolve_kind's content-oriented
        # dispatch, since resolve_kind cannot tell ":path(:manifest())"
        # apart from bare ":manifest()" -- both contain "manifest" via
        # FunctionCall3.contains_function_named's recursive search, but
        # :path() wants the resource's PATH, not its content.
        if reference.name_three is not None:
            path_call = self._find_path_call(reference.name_three.functions)
            if path_call is not None:
                home = self.csvpaths.file_manager.named_file_home(
                    reference.root_major
                )
                return self._resolve_path_call(path_call, home)
        kind = reference.resolve_kind
        if kind == Reference3.FIRST_PARTY:
            if reference.name_three is None:
                # name_one-terminal (prefix search) result: result.path
                # is a file-home directory, not a version file -- no
                # single unambiguous payload to return, per "creating
                # references v3.txt"'s "Resolve terminating at
                # name_one, with no pointer: no default" rule.
                return None
            with DataFileReader(path=result.path, mode="rb") as reader:
                return reader.source.read()
        if kind == Reference3.METADATA_FILE:
            if self._is_bare_pointer_reference(
                reference, "manifest"
            ) or self._is_bare_pointer_reference(reference, "definition"):
                # result.path is already the manifest.json/definition.json
                # path itself (set by query()'s _query_well_known_file()
                # branch above).
                return self._read_well_known_file(result.path)
            if isinstance(reference.root_major, Star3) and result.uuid is not None:
                # Rule 1b -- a pointer already reduced the global ledger
                # to one entry in query(); re-derive it the same way the
                # per-entity branch below does, just against the ledger
                # instead of a named-file's own manifest.
                ledger = self.csvpaths.file_manager.files_root_manifest
                return self._find_manifest_entry_by_uuid(ledger, result.uuid)
            if reference.name_three is not None and any(
                f.contains_function_named("manifest")
                for f in reference.name_three.functions
            ):
                # :manifest() riding alongside a real path/version match
                # (a pointer, or none at all -- see query()) -- give the
                # matched entry itself, not the whole raw file.
                manifest = self.csvpaths.file_manager.get_manifest(
                    reference.root_major
                )
                return self._find_manifest_entry_by_uuid(manifest, result.uuid)
        if kind == Reference3.METADATA_FIELD and reference.name_three is not None:
            field_call = self._find_field_function_call(
                reference.name_three.functions
            )
            if field_call is not None:
                function_cls = ReferenceFunctionFactory.get_registered_class(
                    field_call.name
                )
                if function_cls.SOURCE == "computed":
                    # never stored -- comes straight from the already-
                    # resolved reference, no manifest/definition read at
                    # all. see function_3.py's SOURCE comment.
                    return self._compute_field(field_call.name, reference)
                if field_call.name == "named_file_name":
                    # a real, stored field at RESULTS/RESULT scope, but at
                    # FILES scope this is just the already-known resolved
                    # name -- reading it back from the manifest would be
                    # redundant, so it is computed here instead, same
                    # reasoning as the "computed" SOURCE branch above.
                    return reference.root_major
                key_path = function_cls.KEY.get(reference.datatype)
                if function_cls.SOURCE == "definition":
                    config = self.csvpaths.file_manager.describer.get_config(
                        reference.root_major
                    )
                    entry = config.model_dump(exclude_none=True)
                else:
                    manifest = self.csvpaths.file_manager.get_manifest(
                        reference.root_major
                    )
                    entry = self._find_manifest_entry_by_uuid(manifest, result.uuid)
                return self._extract_field_value(entry, key_path)
        raise ReferenceException3(
            f"FilesReferenceFinder3 does not yet support resolve_kind={kind!r} "
            "-- only :manifest()/:definition() and registered field-accessor "
            "functions are wired up as metadata-file/field functions so far."
        )

    def _compute_field(self, name: str, reference: "Reference3") -> object:
        """values for SOURCE == "computed" field-accessor functions --
        never read from a manifest/definition, always derived from the
        already-resolved reference. See function_3.py's SOURCE comment
        and named_file_home_3.py."""
        if name == "named_file_home":
            return self.csvpaths.file_manager.named_file_home(reference.root_major)
        raise ReferenceException3(
            f"FilesReferenceFinder3 has no computed-field handling for :{name}()"
        )

    @staticmethod
    def _matches(entry: dict, home: str, pattern: list) -> bool:
        file_home = entry["file_home"].rstrip("/")
        if not file_home.startswith(home):
            return False
        rel = file_home[len(home) :].lstrip("/")
        segments = rel.split("/") if rel else []
        if len(segments) != len(pattern):
            return False
        for actual, expected in zip(segments, pattern):
            if isinstance(expected, Star3):
                continue
            if actual != expected:
                return False
        return True
