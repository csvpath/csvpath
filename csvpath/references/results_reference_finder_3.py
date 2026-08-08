import json

from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos

from .functions.function_3 import Function3
from .functions.filters.idchain_3 import Idchain3
from .functions.reference_function_factory_3 import ReferenceFunctionFactory
from .reference_3 import FunctionCall3, Reference3, Star3
from .reference_exceptions_3 import ReferenceException3
from .reference_finder_3 import ReferenceFinder3
from .reference_results_3 import ReferenceResult3, ReferenceResults3

#
# first pass, deliberately narrow, mirroring Files/CsvpathsReferenceFinder3's
# scoping approach -- but results is its own shape, the STRUCTURE table's
# "deepest hierarchy": name_one is a path-like prefix search AS WELL AS the
# version (run) selector, both together (unlike files, which splits "which
# file"/name_one from "which version"/name_three; unlike csvpaths, which has
# no real path at all). name_three identifies one csvpath statement's own
# result directory within the selected run(s).
#
#  - root_major is a literal named-results name (the same name as the named-
#    paths group that was run). "*" (every named-results group) is a
#    different traversal problem, not yet built.
#  - name_one has TWO legal shapes, matching the spec's own examples
#    ("$acme.results.:all()"/"$acme.results.:last()" alongside
#    "$acme.results.customers/2025:first()"):
#      (a) bare/function-only, no literal path at all (mirrors csvpaths --
#          the sole path "segment" is itself a version-selecting function,
#          e.g. :all()/:first()/:last()/:index(n)). Used when there is no
#          template, or the caller does not care about path narrowing at
#          all -- every run discovered for the group is a candidate.
#      (b) literal/"*"/:name("...") path segments (same semantics as files
#          -- see ReferenceFinder3._compile_path_pattern) PLUS its own
#          trailing function chain -- narrows to runs whose own prefix
#          (see _discover_run_homes/_matches_prefix below) matches.
#    Either way, every matching run is pooled into ONE flat list first
#    (mirroring how a bare "*" already flattens across every match for
#    files, rather than reducing per matched prefix separately), and the
#    combined chain's at most one pointer function (:first()/:last()/
#    :index(n)) reduces that WHOLE pool to one run; absent, every pooled
#    run comes back unreduced -- for query()'s own purposes (just listing
#    paths/uuids). This is how "Name_one used alone == path to run dir"
#    (STRUCTURE table) is reached. The "#worksheet" marker (name_two,
#    files-only) is not meaningful here and is rejected. Resolving full
#    content (:manifest(), or an instance-level accessor -- see below) is
#    a stricter case: if no pointer narrows the pool and more than one run
#    matched, query() raises rather than pooling several runs' content --
#    settled 2026-08-07, see manifest_field_functions_proposal.md's
#    "Entity resolution and pooling" section. Listing (query() alone) is
#    unaffected either way.
#  - name_three, if present, is an identity lookup into the selected run's
#    own instance-directory listing (one subdirectory per csvpath statement,
#    named by that statement's identity -- same convention as csvpaths'
#    named_paths_identities) -- matched by identity string, or by :all() for
#    every instance in the run. A well-known instance-level file function
#    (:errors()/:vars()/:meta()/:data()/:unmatched(), or the arbitrary-named
#    :file("...")) may ride alongside the identity/:all() selector in the
#    same chain (e.g. "$acme.results.customers/2025:first().invoices:data()")
#    -- these functions never narrow/select anything themselves (ROLE is
#    VALUE, matching :manifest()/:definition()'s own corrected role), they
#    just say what to resolve to once an instance is already identified.
#    Resolving a matched instance with NO accessor present still gives None
#    (no default) -- only the identity/:all() selection was made, nothing
#    further was asked for. An accessor riding alongside :all() specifically
#    (rather than one specific identity) is illegal, for the same single-
#    entity reason as the run-level case above: :all() means every instance
#    in the run, each with its own separate well-known file on disk, so
#    reading their content all at once is exactly the "more than one entity"
#    case the rule forbids.
#
# storage facts this relies on (confirmed against ResultsManager/
# ResultsRegistrar/ResultRegistrar/ResultSerializer, and a real archive-root
# manifest.json entry David pasted, not assumed): there is no per-named-
# results-group manifest array the way files/csvpaths have -- but there IS
# a single, archive-wide manifest.json (one entry per csvpath-statement
# execution, across every named-paths group -- the same one the earlier
# run-ordering experiment found unreliable as an ORDERING source, owing to
# cross-group interleaving and stale entries for deleted runs). Each entry
# already carries "run_home", the exact, already-resolved absolute path a
# specific run's directory landed at, recorded at the moment that run
# happened -- discovery, not ordering: this sidesteps ever needing to
# know/guess a group's own template depth (which lives in the group's own
# template string, e.g. PathsManager.get_template_for_paths(), and can
# change over time or be overridden per-run -- neither matters here, since
# run_home already reflects whatever template was actually in effect for
# that specific run). Confirmed against v1/v2's own working equivalent
# (csvpath/util/references/results_tools/resolve_possibles.py), which uses
# this exact same manifest+run_home+existence-check approach rather than
# directory-walking. Stale entries are handled by an existence check
# (Nos(run_home).exists()), same as v2 does. Run directories are named
# "%Y-%m-%d_%H-%M-%S[_N]" (RunHomeMaker), lexicographically sortable =
# chronological (confirmed separately by direct experiment). Each run
# directory has its own manifest.json (a single dict; "run_uuid" identifies
# the run itself). Each run directory contains one subdirectory per csvpath
# statement, named by that statement's own identity
# (ResultSerializer.get_instance_dir), each with its own manifest.json (a
# single dict; "uuid" identifies that instance).
#


class ResultsReferenceFinder3(ReferenceFinder3):
    def query(self) -> ReferenceResults3:
        reference = self.ref.parsed
        root_major = reference.root_major
        if isinstance(root_major, Star3):
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not yet support '*' as "
                "root_major (querying every named-results group) -- use a "
                "literal group name."
            )

        name_one = reference.name_one
        if name_one.name_two is not None:
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not support the '#worksheet' "
                "marker (name_two) -- it is files-only."
            )

        home = self.csvpaths.results_manager.get_named_results_home(root_major)
        run_homes = self._discover_run_homes(root_major)

        if self._is_bare_function_only(name_one):
            # mirrors csvpaths: no literal path at all, e.g.
            # "$acme.results.:all()"/"$acme.results.:last()" -- every run
            # discovered for the group is a candidate, no prefix narrowing.
            candidates = run_homes
        else:
            pattern = self._compile_path_pattern(name_one.path)
            candidates = [
                rh for rh in run_homes if self._matches_prefix(rh, home, pattern)
            ]
        candidates = sorted(candidates)

        calls = self._combined_name_one_calls(name_one)
        pointer = self._pointer_from_calls(calls)
        identity, match_all, accessor = self._name_three_selector(reference.name_three)
        has_manifest = any(
            seg.contains_function_named("manifest")
            for seg in calls
            if isinstance(seg, FunctionCall3)
        )
        wants_full_content = has_manifest or accessor is not None

        if pointer is not None:
            selected = self._apply_pointer(pointer, candidates)
            selected_runs = [selected] if selected is not None else []
        else:
            selected_runs = candidates
            if len(selected_runs) > 1 and wants_full_content:
                # Resolving full manifest/well-known-file content always
                # touches exactly one entity (settled 2026-08-07, see
                # manifest_field_functions_proposal.md's "Entity
                # resolution and pooling" section) -- more than one run
                # here needs a pointer to pick which one, whether the
                # content lives at the run level (:manifest()) or the
                # instance level (an accessor riding on name_three).
                raise ReferenceException3(
                    "ResultsReferenceFinder3 requires a pointer (:first()/"
                    ":last()/:index(n)) to pick one run when reading full "
                    "content and more than one run matches -- resolving "
                    "full content always touches exactly one entity."
                )

        if match_all and accessor is not None:
            # :all() pools every instance in the run -- each instance has
            # its own separate well-known file on disk, so this is the
            # same "more than one entity" case as above, just one level
            # down. A specific identity is still fine: that is already
            # exactly one instance.
            raise ReferenceException3(
                "ResultsReferenceFinder3 requires a specific statement "
                "identity, not :all(), to read full well-known-file "
                "content -- resolving full content always touches "
                "exactly one entity."
            )

        results = []
        for run_dir in selected_runs:
            results.extend(self._results_for_run(run_dir, identity, match_all))
        return ReferenceResults3(results=results)

    _JSON_ACCESSOR_FILES = {
        "errors": "errors.json",
        "vars": "vars.json",
        "meta": "meta.json",
    }
    _BYTES_ACCESSOR_FILES = {
        "data": "data.csv",
        "unmatched": "unmatched.csv",
    }

    def _extract_data(self, result: ReferenceResult3):
        reference = self.ref.parsed
        name_one_calls = self._combined_name_one_calls(reference.name_one)
        has_manifest = any(
            seg.contains_function_named("manifest")
            for seg in name_one_calls
            if isinstance(seg, FunctionCall3)
        )
        if has_manifest:
            # :manifest() rides beside the run-selecting pointer in
            # name_one (e.g. "$acme.results.customers/2025:first()
            # :manifest()") -- the STRUCTURE table's own "Resolve
            # terminating at name_one, with file pointer: results:
            # contents of manifest.json" row.
            #
            # Files/csvpaths share ONE manifest.json array across every
            # version of a named-file/named-paths group, so resolving
            # several matched versions' :manifest() means filtering that
            # one shared array down to several entries (see
            # _find_manifest_entry_by_uuid). Results is different: each
            # matched run has its OWN separate manifest.json file on
            # disk -- reading more than one would mean opening more than
            # one file, which query()'s own guard above already forbids
            # (a pointer is required whenever more than one run would
            # otherwise match). So by the time we get here, result.path
            # is always exactly one run's directory, and we just read
            # its own manifest.json directly (below), the same as any
            # other per-result payload via the ordinary resolve() loop.
            if reference.name_three is not None:
                raise ReferenceException3(
                    "ResultsReferenceFinder3 does not support combining "
                    ":manifest() on name_one with name_three -- resolve "
                    "the run's own manifest on its own, without a "
                    "further instance selector."
                )
            return self._read_well_known_json(
                Nos(result.path).join("manifest.json")
            )

        kind = reference.resolve_kind
        if kind in (Reference3.METADATA_FILE, Reference3.METADATA_FIELD):
            # both land here: :errors() alone classifies as METADATA_FILE,
            # :errors(:idchain(...)) classifies as METADATA_FIELD (a
            # nested pointer-like arg -- see Reference3.resolve_kind) --
            # _read_accessor already handles the idchain-filtering
            # internally based on accessor.arg, so both kinds resolve
            # identically from here.
            _, _, accessor = self._name_three_selector(reference.name_three)
            if accessor is not None:
                return self._read_accessor(result.path, accessor)
        if kind != Reference3.FIRST_PARTY:
            raise ReferenceException3(
                f"ResultsReferenceFinder3 does not yet support "
                f"resolve_kind={kind!r} -- only :errors()/:vars()/:meta()/"
                ":data()/:unmatched()/:file() are wired up as metadata-"
                "file functions so far."
            )
        # a run directory (no name_three) or an instance directory matched
        # by identity/:all() with no accessor riding alongside has no
        # single unambiguous payload -- "no default", per "creating
        # references v3.txt"'s resolve table.
        return None

    @classmethod
    def _read_accessor(cls, instance_dir: str, accessor):
        """resolves a well-known instance-level file accessor (errors/
        vars/meta -> parsed JSON; data/unmatched -> raw bytes, both
        genuinely optional, None if never written; file("...") -> raw
        bytes of the user-named file, also optional). :errors() may
        carry a nested :idchain(...) argument, filtering the parsed
        list down to entries whose own "source" field (Error.to_json()
        -- Matchable.my_chain, recorded once at error time, not walked
        live) matches -- zero matches is a legitimate empty list, not
        None or an error; the file itself was found and read fine."""
        if accessor.name in cls._JSON_ACCESSOR_FILES:
            path = Nos(instance_dir).join(cls._JSON_ACCESSOR_FILES[accessor.name])
            data = cls._read_well_known_json(path)
            if (
                data is not None
                and accessor.name == "errors"
                and isinstance(accessor.arg, Idchain3)
            ):
                data = [e for e in data if accessor.arg.matches(e.get("source"))]
            return data
        if accessor.name in cls._BYTES_ACCESSOR_FILES:
            path = Nos(instance_dir).join(cls._BYTES_ACCESSOR_FILES[accessor.name])
            return cls._read_well_known_file(path)
        path = Nos(instance_dir).join(accessor.arg)
        return cls._read_well_known_file(path)

    def _discover_run_homes(self, root_major: str) -> list[str]:
        """every distinct, still-existing run_home for this group, read
        from the archive-root manifest.json -- see this module's own
        docstring for why this replaces directory-walking entirely (no
        need to know/guess the group's template depth). Many entries can
        share the same run_home (one entry per csvpath-statement
        execution, several statements per run), so dedupe; a stale entry
        (the run since deleted) is dropped via an existence check."""
        archive = self.csvpaths.config.get(section="results", name="archive")
        manifest_path = Nos(archive).join("manifest.json")
        if not Nos(manifest_path).exists():
            return []
        with DataFileReader(manifest_path) as reader:
            entries = json.load(reader.source)
        homes = []
        for entry in entries:
            if entry.get("named_paths_name") != root_major:
                continue
            run_home = entry.get("run_home")
            if run_home and run_home not in homes:
                homes.append(run_home)
        return [h for h in homes if Nos(h).exists()]

    def _results_for_run(
        self, run_dir: str, identity: str | None, match_all: bool
    ) -> list[ReferenceResult3]:
        if identity is None and not match_all:
            uuid = self._read_json_field(
                Nos(run_dir).join("manifest.json"), "run_uuid"
            )
            return [ReferenceResult3(path=run_dir, uuid=uuid)]

        instances = self._list_instance_identities(run_dir)
        if match_all:
            matched = instances
        else:
            index = self._find_by_identity(identity, instances)
            matched = [instances[index]] if index is not None else []

        found = []
        for inst in matched:
            inst_dir = Nos(run_dir).join(inst)
            uuid = self._read_json_field(
                Nos(inst_dir).join("manifest.json"), "uuid"
            )
            found.append(ReferenceResult3(path=inst_dir, uuid=uuid))
        return found

    @classmethod
    def _combined_name_one_calls(cls, name_one) -> list:
        """name_one's own effective function chain, used for both
        pointer-detection (query()) and ":manifest()"-detection
        (_extract_data()) -- the bare/function-only shape's path[0] is
        itself part of the chain (mirrors csvpaths); the literal-path
        shape's path segments are never functions (except :name(...),
        which is path-building, not chain content), so only its
        trailing .functions counts there."""
        if cls._is_bare_function_only(name_one):
            return [name_one.path[0], *name_one.functions]
        return list(name_one.functions)

    @staticmethod
    def _is_bare_function_only(name_one) -> bool:
        """true for a name_one with no literal path at all -- its sole
        path "segment" is itself a version-selecting function (e.g.
        :all()/:first()/:last()/:index(n)), mirroring csvpaths' own
        "path[0] is a FunctionCall3" shape. :name("...") is excluded --
        that is path-*building* (a literal name), not a version
        selector, so it stays in the ordinary literal-path shape even
        as the sole segment."""
        return (
            len(name_one.path) == 1
            and isinstance(name_one.path[0], FunctionCall3)
            and name_one.path[0].name != "name"
        )

    @staticmethod
    def _pointer_from_calls(calls: list):
        """at most one pointer function (:first()/:last()/:index(n))
        among the combined chain selects which run -- build_chain()
        already enforces the "at most one" rule; absent means every run
        comes back unreduced."""
        if not calls:
            return None
        built = ReferenceFunctionFactory.build_chain(calls)
        pointers = [f for f in built if f.ROLE == Function3.POINTER]
        return pointers[0] if pointers else None

    _ACCESSOR_NAMES = ("errors", "vars", "meta", "data", "unmatched", "file")

    @staticmethod
    def _name_three_selector(name_three) -> tuple[str | None, bool, object]:
        """returns (identity, match_all, accessor) for name_three --
        identity is a literal statement-identity string to look up (None
        if match_all, or if no identity/:all() selector is present at
        all); match_all is True for :all() (every instance in the run);
        accessor is the built well-known-file Function3 riding alongside
        the identity/:all() selector, or None if none was requested
        (resolving then gives None -- "no default"). An unrecognized
        function raises via build_chain() itself ("Unknown reference
        function") if it is not registered at all, or is rejected here
        directly if it is registered but not meaningful as a name_three
        function (e.g. :manifest())."""
        if name_three is None:
            return None, False, None

        match_all = False
        accessor = None
        if name_three.functions:
            built = ReferenceFunctionFactory.build_chain(name_three.functions)
            for f in built:
                if f.name == "all":
                    match_all = True
                elif f.name in ResultsReferenceFinder3._ACCESSOR_NAMES:
                    accessor = f
                else:
                    raise ReferenceException3(
                        f"ResultsReferenceFinder3 does not yet support "
                        f":{f.name}() as a name_three function."
                    )

        body = name_three.body
        if isinstance(body, Star3):
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not support a bare '*' as "
                "name_three's body -- use :all() instead."
            )
        if body is not None and match_all:
            raise ReferenceException3(
                "ResultsReferenceFinder3 cannot combine a literal "
                "identity with :all() -- they select instances two "
                "different, contradictory ways."
            )
        if body is None and not match_all:
            raise ReferenceException3(
                "ResultsReferenceFinder3 requires name_three to be a "
                "literal statement identity or :all() to select which "
                "instance(s) a well-known-file function applies to."
            )
        return body, match_all, accessor

    @staticmethod
    def _matches_prefix(run_home: str, home: str, pattern: list) -> bool:
        """true if run_home's own prefix -- everything between `home`
        and the run directory's own name (the last path segment) --
        matches `pattern` position-by-position (Star3 as wildcard).
        Similar in spirit to FilesReferenceFinder3._matches, but the run
        directory's own name is excluded from the comparison first,
        since (unlike a file's file_home) run_home already includes
        that final, version-identifying segment itself."""
        home = home.rstrip("/")
        if not run_home.startswith(home):
            return False
        rel = run_home[len(home) :].lstrip("/")
        segments = rel.split("/") if rel else []
        prefix_segments = segments[:-1]
        if len(prefix_segments) != len(pattern):
            return False
        for actual, expected in zip(prefix_segments, pattern):
            if isinstance(expected, Star3):
                continue
            if actual != expected:
                return False
        return True

    @staticmethod
    def _list_instance_identities(run_dir: str) -> list[str]:
        """every csvpath statement's own result subdirectory within a
        run, named by that statement's identity -- "_extra_data" is the
        one non-instance directory a run dir can contain (manifest.json
        is a file, already excluded by dirs_only)."""
        return [
            name
            for name in Nos(run_dir).listdir(dirs_only=True)
            if name != "_extra_data"
        ]

    @classmethod
    def _read_json_field(cls, path: str, field: str):
        """reads one field from a small JSON file (a run's or an
        instance's own manifest.json), tolerating absence -- None if the
        file does not exist rather than raising or fabricating a
        default. Built on the shared _read_well_known_json rather than
        reusing ResultFileReader.json_file() -- that helper writes a
        fresh empty JSON file when one is missing, a write side effect a
        read-only reference query must never trigger."""
        data = cls._read_well_known_json(path)
        return data.get(field) if data else None
