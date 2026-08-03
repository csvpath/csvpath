import pytest

from csvpath.references.reference_3 import FunctionCall3, NameOne3, NameThree3, Reference3
from csvpath.references.reference_finder_3 import ReferenceFinder3
from csvpath.references.reference_parser_3 import ReferenceParser3
from csvpath.references.reference_results_3 import ReferenceResult3, ReferenceResults3

CSVPATHS = object()


class _DummyFinder(ReferenceFinder3):
    """minimal concrete finder for exercising the shared resolve()/
    resolve_from() logic on the ABC -- query() and _extract_data() are
    the only datatype-specific hooks, so a fixed fake result set and a
    deterministic extraction are enough."""

    def __init__(self, *, csvpaths, ref) -> None:
        super().__init__(csvpaths=csvpaths, ref=ref)
        self.query_call_count = 0

    def query(self) -> ReferenceResults3:
        self.query_call_count += 1
        return ReferenceResults3(
            results=[
                ReferenceResult3(path="p1", uuid="u1"),
                ReferenceResult3(path="p2", uuid="u2"),
            ]
        )

    def _extract_data(self, result: ReferenceResult3):
        return f"data-for-{result.path}"


def _ref(reference: str) -> ReferenceParser3:
    return ReferenceParser3(string=reference, csvpaths=CSVPATHS)


class TestConstruction:
    def test_rejects_none_csvpaths(self):
        with pytest.raises(ValueError):
            _DummyFinder(csvpaths=None, ref=_ref("$acme.results.a"))

    def test_rejects_none_ref(self):
        with pytest.raises(ValueError):
            _DummyFinder(csvpaths=CSVPATHS, ref=None)

    def test_cannot_instantiate_the_abc_directly(self):
        with pytest.raises(TypeError):
            ReferenceFinder3(csvpaths=CSVPATHS, ref=_ref("$acme.results.a"))

    def test_holds_ref_and_csvpaths(self):
        ref = _ref("$acme.results.a")
        f = _DummyFinder(csvpaths=CSVPATHS, ref=ref)
        assert f.ref is ref
        assert f.csvpaths is CSVPATHS


class TestApplyPointer:
    # shared by every finder that reads a flat manifest array (files,
    # csvpaths) -- moved onto the ABC once there were two real
    # consumers, not just one.
    def test_first(self):
        assert ReferenceFinder3._apply_pointer(
            type("P", (), {"name": "first"})(), ["a", "b", "c"]
        ) == "a"

    def test_last(self):
        assert ReferenceFinder3._apply_pointer(
            type("P", (), {"name": "last"})(), ["a", "b", "c"]
        ) == "c"

    def test_index(self):
        assert ReferenceFinder3._apply_pointer(
            type("P", (), {"name": "index", "arg": 1})(), ["a", "b", "c"]
        ) == "b"

    def test_index_out_of_range_returns_none(self):
        assert ReferenceFinder3._apply_pointer(
            type("P", (), {"name": "index", "arg": 99})(), ["a", "b", "c"]
        ) is None

    def test_empty_candidates_returns_none(self):
        assert ReferenceFinder3._apply_pointer(
            type("P", (), {"name": "first"})(), []
        ) is None

    def test_unsupported_pointer_name_raises(self):
        from csvpath.references.reference_exceptions_3 import ReferenceException3

        with pytest.raises(ReferenceException3):
            ReferenceFinder3._apply_pointer(
                type("P", (), {"name": "bogus"})(), ["a"]
            )


class TestIsBarePointerReference:
    # shared by every finder that needs to detect a ":manifest()"-style,
    # sole-content name_one shape (files, csvpaths) -- see :manifest()'s
    # own query() branch in each finder, which must bypass ordinary
    # "which file"/"which version" narrowing entirely for this shape.
    @staticmethod
    def _ref(name_one, name_three=None) -> Reference3:
        return Reference3(
            root_major="acme",
            datatype=Reference3.FILES,
            name_one=name_one,
            name_three=name_three,
        )

    def test_true_for_bare_sole_function(self):
        r = self._ref(NameOne3(path=[FunctionCall3(name="manifest")]))
        assert ReferenceFinder3._is_bare_pointer_reference(r, "manifest")

    def test_false_for_different_function_name(self):
        r = self._ref(NameOne3(path=[FunctionCall3(name="all")]))
        assert not ReferenceFinder3._is_bare_pointer_reference(r, "manifest")

    def test_false_when_function_has_an_arg(self):
        r = self._ref(NameOne3(path=[FunctionCall3(name="manifest", arg="x")]))
        assert not ReferenceFinder3._is_bare_pointer_reference(r, "manifest")

    def test_false_with_extra_path_segment(self):
        r = self._ref(NameOne3(path=["a", FunctionCall3(name="manifest")]))
        assert not ReferenceFinder3._is_bare_pointer_reference(r, "manifest")

    def test_false_with_trailing_functions(self):
        r = self._ref(
            NameOne3(
                path=[FunctionCall3(name="manifest")],
                functions=[FunctionCall3(name="first")],
            )
        )
        assert not ReferenceFinder3._is_bare_pointer_reference(r, "manifest")

    def test_false_when_name_three_present(self):
        r = self._ref(
            NameOne3(path=[FunctionCall3(name="manifest")]),
            name_three=NameThree3(body="v1"),
        )
        assert not ReferenceFinder3._is_bare_pointer_reference(r, "manifest")

    def test_false_for_literal_path_segment(self):
        r = self._ref(NameOne3(path=["manifest"]))
        assert not ReferenceFinder3._is_bare_pointer_reference(r, "manifest")


class TestQueryWellKnownFile:
    # shared query() branch for a fixed, home-directory-scoped JSON
    # resource (manifest.json, definition.json) -- both files and
    # csvpaths route :manifest()/:definition() through this.
    def test_returns_one_result_with_no_uuid(self):
        results = ReferenceFinder3._query_well_known_file("some/home", "manifest.json")
        assert results.files == ["some/home/manifest.json"]
        assert results.results[0].uuid is None


class TestReadWellKnownFile:
    def test_reads_raw_bytes_when_the_file_exists(self, tmp_path):
        content = b'{"a": 1}'
        path = tmp_path / "definition.json"
        path.write_bytes(content)
        assert ReferenceFinder3._read_well_known_file(str(path)) == content

    def test_returns_none_when_the_file_does_not_exist(self, tmp_path):
        missing = tmp_path / "definition.json"
        assert ReferenceFinder3._read_well_known_file(str(missing)) is None


class TestFindByIdentity:
    # shared by every finder whose name_three does an identity lookup
    # (csvpaths' named_paths_identities, results' per-statement
    # directory names).
    def test_matches_named_identity(self):
        assert ReferenceFinder3._find_by_identity("b", ["a", "b", "c"]) == 1

    def test_matches_stringified_index_identity(self):
        assert ReferenceFinder3._find_by_identity("0", ["0", "named"]) == 0

    def test_no_match_returns_none(self):
        assert ReferenceFinder3._find_by_identity("nope", ["a", "b"]) is None


class TestResolve:
    # resolve_from() always calls _extract_data() for every result now
    # -- the old resolves_to_data gate is gone from the ABC (it moved
    # into what each concrete finder's own _extract_data() does with
    # Reference3.resolve_kind, not whether it gets called at all).
    REF = "$acme.results.a"

    def test_resolve_extracts_data_for_every_result(self):
        f = _DummyFinder(csvpaths=CSVPATHS, ref=_ref(self.REF))
        results = f.resolve()
        assert results.data_for_uuid("u1") == "data-for-p1"
        assert results.data_for_uuid("u2") == "data-for-p2"

    def test_resolve_from_list_narrows_then_only_extracts_the_selection(self):
        f = _DummyFinder(csvpaths=CSVPATHS, ref=_ref(self.REF))
        results = f.resolve_from(["p1"])
        assert results.files == ["p1"]
        assert results.results[0].data == "data-for-p1"
        assert f.query_call_count == 1

    def test_resolve_from_a_results3_does_not_requery(self):
        f = _DummyFinder(csvpaths=CSVPATHS, ref=_ref(self.REF))
        preselected = ReferenceResults3(
            results=[ReferenceResult3(path="only-this-one", uuid="uX")]
        )
        results = f.resolve_from(preselected)
        assert results.files == ["only-this-one"]
        assert results.results[0].data == "data-for-only-this-one"
        assert f.query_call_count == 0
