from csvpath.util.file_readers import DataFileReader

from .functions.function_3 import Function3
from .functions.reference_function_factory_3 import ReferenceFunctionFactory
from .reference_3 import Reference3, Star3
from .reference_exceptions_3 import ReferenceException3
from .reference_finder_3 import ReferenceFinder3
from .reference_results_3 import ReferenceResult3, ReferenceResults3


class FilesReferenceFinder3(ReferenceFinder3):
    #
    # first pass, deliberately narrow:
    #  - root_major is a literal named-file name. "*" (every named-file)
    #    is a different traversal problem, not yet built.
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
            raise ReferenceException3(
                "FilesReferenceFinder3 does not yet support '*' as root_major "
                "(querying every named-file) -- use a literal named-file name."
            )

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

        manifest = self.csvpaths.file_manager.get_manifest(root_major)
        home = self.csvpaths.file_manager.named_file_home(root_major).rstrip("/")
        candidates = [
            entry for entry in manifest if self._matches(entry, home, pattern)
        ]

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
            # :manifest() alone, no pointer -- every version matching
            # name_one's own path narrowing, unreduced. This is how
            # "$acme.files.orders.:manifest()" (David's own example) is
            # actually reached: the manifest entries of every
            # registration under "orders", not just one.
            selected_candidates = candidates

        return ReferenceResults3(
            results=[
                ReferenceResult3(path=c["file"], uuid=c["uuid"])
                for c in selected_candidates
            ]
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
