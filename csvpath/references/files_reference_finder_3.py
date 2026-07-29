from .functions.function_3 import Function3
from .functions.reference_function_factory_3 import ReferenceFunctionFactory
from .reference_3 import FunctionCall3, Star3
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
    #  - name_three must resolve to exactly one pointer function
    #    (:first()/:last()/:index(n)). This matches the STRUCTURE table:
    #    name_one picks *which file*, name_three picks *which version*.
    #    A literal name_three body (bypassing a pointer function
    #    entirely) is not yet supported either.
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
        if name_one.functions:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not yet support functions attached "
                "directly to name_one -- put the version-selecting function in "
                "name_three instead."
            )
        pattern = self._compile_path_pattern(name_one.path)

        name_three = reference.name_three
        if name_three.body is not None:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not yet support a literal name_three "
                "body -- name_three must resolve to a pointer function "
                "(:first()/:last()/:index(n))."
            )
        built = ReferenceFunctionFactory.build_chain(name_three.functions)
        pointers = [f for f in built if f.ROLE == Function3.POINTER]
        if len(pointers) != 1:
            raise ReferenceException3(
                "FilesReferenceFinder3 requires name_three to resolve to "
                "exactly one pointer function (:first()/:last()/:index(n))."
            )
        pointer = pointers[0]

        manifest = self.csvpaths.file_manager.get_manifest(root_major)
        home = self.csvpaths.file_manager.named_file_home(root_major).rstrip("/")
        candidates = [
            entry for entry in manifest if self._matches(entry, home, pattern)
        ]

        selected = self._apply_pointer(pointer, candidates)
        results = []
        if selected is not None:
            results.append(
                ReferenceResult3(path=selected["file"], uuid=selected["uuid"])
            )
        return ReferenceResults3(results=results)

    def _extract_data(self, result: ReferenceResult3):
        raise ReferenceException3(
            "FilesReferenceFinder3 has no content to extract from -- "
            "resolves_to_data should always be False for the files datatype "
            "with the functions currently registered."
        )

    @staticmethod
    def _compile_path_pattern(path: list) -> list:
        """turns name_one.path into a list of str/Star3 to match against
        real file_home segments. a literal str or Star3 segment passes
        through unchanged; a :name("...") segment is compiled and
        unwrapped to its literal string, so matching downstream doesn't
        need to know the difference. any other function-valued segment
        is explicitly not yet supported."""
        pattern = []
        for segment in path:
            if isinstance(segment, FunctionCall3):
                if segment.name != "name":
                    raise ReferenceException3(
                        f"FilesReferenceFinder3 does not yet support :{segment.name}() "
                        "as a name_one path segment -- only :name(\"...\") and "
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

    @staticmethod
    def _apply_pointer(pointer, candidates: list) -> dict | None:
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
