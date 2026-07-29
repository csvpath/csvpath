import pytest

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


class TestResolveWithoutDataExtraction:
    # "$acme.results.a.:errors()" -- a plain well-known-file function,
    # no value-locator nested in it, so resolves_to_data is False.
    def test_resolve_leaves_data_none(self):
        f = _DummyFinder(csvpaths=CSVPATHS, ref=_ref("$acme.results.a.:errors()"))
        results = f.resolve()
        assert results.files == ["p1", "p2"]
        assert all(r.data is None for r in results.results)

    def test_resolve_from_list_narrows_without_extracting(self):
        f = _DummyFinder(csvpaths=CSVPATHS, ref=_ref("$acme.results.a.:errors()"))
        results = f.resolve_from(["p1"])
        assert results.files == ["p1"]
        assert results.results[0].data is None
        assert f.query_call_count == 1


class TestResolveWithDataExtraction:
    # ":errors(:idchain(...))" -- a value-locator nested in the
    # well-known-file function's arg, so resolves_to_data is True.
    REF = '$acme.results.a.:errors(:idchain("add[0]string[2]"))'

    def test_resolve_extracts_data_for_every_result(self):
        f = _DummyFinder(csvpaths=CSVPATHS, ref=_ref(self.REF))
        results = f.resolve()
        assert results.data_for_uuid("u1") == "data-for-p1"
        assert results.data_for_uuid("u2") == "data-for-p2"

    def test_resolve_from_narrows_then_only_extracts_the_selection(self):
        f = _DummyFinder(csvpaths=CSVPATHS, ref=_ref(self.REF))
        results = f.resolve_from(["u2"])
        assert results.files == ["p2"]
        assert results.results[0].data == "data-for-p2"
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
