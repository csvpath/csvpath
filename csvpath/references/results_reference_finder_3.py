import json

from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos

from .functions.function_3 import Function3
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
#          template, or the caller does not care about path narrowing --
#          the named-results home directory itself is the "prefix".
#      (b) literal/"*"/:name("...") path segments (same semantics as files
#          -- see ReferenceFinder3._compile_path_pattern) PLUS its own
#          trailing function chain.
#    Either way, the combined chain (whichever function(s) are not path-
#    building) may contain at most one pointer function (:first()/:last()/
#    :index(n)): if present, it reduces each matched prefix to that
#    prefix's one specific run; if absent, every run under each matched
#    prefix comes back, unreduced. This is how "Name_one used alone == path
#    to run dir" (STRUCTURE table) is reached, matching how
#    CsvpathsReferenceFinder3 already handles "zero or one pointer" for its
#    own combined chain. The "#worksheet" marker (name_two, files-only) is
#    not meaningful here and is rejected.
#    KNOWN LIMITATION: this finder does not know how many literal path
#    segments a given named-results group's template actually has before
#    reaching the run-directory level (that lives in the group's own
#    template string, e.g. via PathsManager.get_template_for_paths()) --
#    it simply treats whatever directories the given pattern matches as
#    "the runs". Under-specifying the path (fewer segments than the real
#    template) silently treats an intermediate directory's own children as
#    if they were runs, rather than raising. Not validated in this pass.
#  - name_three, if present, is an identity lookup into the selected run's
#    own instance-directory listing (one subdirectory per csvpath statement,
#    named by that statement's identity -- same convention as csvpaths'
#    named_paths_identities) -- matched by identity string, or by :all() for
#    every instance in the run. Well-known instance-level file functions
#    (:data()/:vars()/:meta()/:unmatched()/:errors()) are not yet
#    registered, so resolving a matched instance always gives None for now
#    (no default) -- query() still finds every matched path+uuid correctly,
#    resolve() just has nothing further to extract yet.
#
# storage facts this relies on (confirmed against ResultsManager/
# ResultsRegistrar/ResultRegistrar/ResultSerializer, not assumed): there is
# no per-named-results-group manifest array the way files/csvpaths have --
# query() has to walk real directories. Run directories are named
# "%Y-%m-%d_%H-%M-%S[_N]" (RunHomeMaker), lexicographically sortable =
# chronological (confirmed by direct experiment -- see project memory).
# Each run directory has its own manifest.json (a single dict, not an
# array -- "run_uuid" identifies the run itself). Each run directory
# contains one subdirectory per csvpath statement, named by that
# statement's own identity (ResultSerializer.get_instance_dir), each with
# its own manifest.json (a single dict; "uuid" identifies that instance).
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
        if self._is_bare_function_only(name_one):
            # mirrors csvpaths: no literal path at all, e.g.
            # "$acme.results.:all()"/"$acme.results.:last()" -- the named-
            # results home directory itself is the "prefix".
            prefixes = [home]
            calls = [name_one.path[0], *name_one.functions]
        else:
            pattern = self._compile_path_pattern(name_one.path)
            prefixes = self._matching_prefix_dirs(home, pattern)
            calls = list(name_one.functions)

        pointer = self._pointer_from_calls(calls)
        identity, match_all = self._name_three_selector(reference.name_three)

        results = []
        for prefix in prefixes:
            run_names = sorted(Nos(prefix).listdir(dirs_only=True))
            if pointer is not None:
                selected = self._apply_pointer(pointer, run_names)
                selected_runs = [selected] if selected is not None else []
            else:
                selected_runs = run_names

            for run_name in selected_runs:
                run_dir = Nos(prefix).join(run_name)
                results.extend(
                    self._results_for_run(run_dir, identity, match_all)
                )
        return ReferenceResults3(results=results)

    def _extract_data(self, result: ReferenceResult3):
        reference = self.ref.parsed
        kind = reference.resolve_kind
        if kind != Reference3.FIRST_PARTY:
            raise ReferenceException3(
                f"ResultsReferenceFinder3 does not yet support "
                f"resolve_kind={kind!r} -- no metadata-file/metadata-field "
                "functions are registered for results yet."
            )
        # neither a whole run directory nor an instance directory matched
        # by identity/:all() has a single unambiguous payload without a
        # well-known-file function -- none registered yet, so "no
        # default" applies uniformly here, per "creating references
        # v3.txt"'s resolve table.
        return None

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

    @staticmethod
    def _name_three_selector(name_three) -> tuple[str | None, bool]:
        """returns (identity, match_all) for name_three -- identity is a
        literal statement-identity string to look up, match_all is True
        for a bare :all() (every instance in the run, unfiltered). Any
        other function (well-known instance-level files -- :data()/
        :vars()/:meta()/:unmatched()/:errors()) is not yet registered
        and raises via build_chain() itself ("Unknown reference
        function"); any registered function other than :all() (there is
        no other one that makes sense here) is explicitly rejected too."""
        if name_three is None:
            return None, False
        if name_three.functions:
            built = ReferenceFunctionFactory.build_chain(name_three.functions)
            if not (len(built) == 1 and built[0].name == "all"):
                raise ReferenceException3(
                    "ResultsReferenceFinder3 only supports :all() as a "
                    "name_three function for now -- well-known instance "
                    "files (:data()/:vars()/:meta()/:unmatched()/"
                    ":errors()) are not yet registered for results."
                )
            return None, True
        if isinstance(name_three.body, Star3):
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not support a bare '*' as "
                "name_three's body -- use :all() instead."
            )
        return name_three.body, False

    @staticmethod
    def _matching_prefix_dirs(home: str, pattern: list) -> list[str]:
        """walks real directories under `home`, matching each literal/
        Star3 pattern segment against one level of subdirectories --
        the results-side equivalent of FilesReferenceFinder3's manifest-
        array matching, needed because there is no per-named-results-
        group manifest array to scan (confirmed by direct experiment --
        see project memory) -- only real directories on disk."""
        current = [home]
        for segment in pattern:
            next_level = []
            for base in current:
                for name in sorted(Nos(base).listdir(dirs_only=True)):
                    if isinstance(segment, Star3) or name == segment:
                        next_level.append(Nos(base).join(name))
            current = next_level
        return current

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

    @staticmethod
    def _read_json_field(path: str, field: str):
        """reads one field from a small JSON file (a run's or an
        instance's own manifest.json), tolerating absence -- None if the
        file does not exist rather than raising or fabricating a
        default. Deliberately does not reuse ResultFileReader.json_file()
        here -- that helper writes a fresh empty JSON file when one is
        missing, a write side effect a read-only reference query must
        never trigger."""
        if not Nos(path).exists():
            return None
        with DataFileReader(path) as reader:
            data = json.load(reader.source)
        return data.get(field)
