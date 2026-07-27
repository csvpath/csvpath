import pytest

from csvpath.references.reference_results_3 import ReferenceResult3, ReferenceResults3


class TestReferenceResult3:
    @pytest.mark.parametrize("bad_path", [None, ""])
    def test_rejects_none_or_empty_path(self, bad_path):
        with pytest.raises(ValueError):
            ReferenceResult3(path=bad_path, uuid="u1")

    @pytest.mark.parametrize("bad_uuid", [None, ""])
    def test_rejects_none_or_empty_uuid(self, bad_uuid):
        with pytest.raises(ValueError):
            ReferenceResult3(path="p1", uuid=bad_uuid)

    def test_data_defaults_to_none(self):
        r = ReferenceResult3(path="p1", uuid="u1")
        assert r.data is None

    def test_data_is_settable(self):
        r = ReferenceResult3(path="p1", uuid="u1")
        r.data = {"a": 1}
        assert r.data == {"a": 1}

    def test_equality(self):
        a = ReferenceResult3(path="p1", uuid="u1")
        b = ReferenceResult3(path="p1", uuid="u1")
        c = ReferenceResult3(path="p2", uuid="u1")
        assert a == b
        assert a != c


class TestReferenceResults3:
    def _results(self):
        return ReferenceResults3(
            results=[
                ReferenceResult3(path="p1", uuid="u1"),
                ReferenceResult3(path="p2", uuid="u2"),
            ]
        )

    def test_defaults_to_empty(self):
        r = ReferenceResults3()
        assert r.results == []
        assert len(r) == 0

    def test_files_and_uuids(self):
        r = self._results()
        assert r.files == ["p1", "p2"]
        assert r.uuids == ["u1", "u2"]

    def test_file_for_uuid(self):
        r = self._results()
        assert r.file_for_uuid("u2") == "p2"
        assert r.file_for_uuid("nope") is None

    def test_uuid_for_file(self):
        r = self._results()
        assert r.uuid_for_file("p1") == "u1"
        assert r.uuid_for_file("nope") is None

    def test_data_for_uuid(self):
        results = [
            ReferenceResult3(path="p1", uuid="u1", data="d1"),
            ReferenceResult3(path="p2", uuid="u2"),
        ]
        r = ReferenceResults3(results=results)
        assert r.data_for_uuid("u1") == "d1"
        assert r.data_for_uuid("u2") is None
        assert r.data_for_uuid("nope") is None

    def test_select_by_path_or_uuid(self):
        r = self._results()
        selected = r.select(["p1", "u2"])
        assert selected.files == ["p1", "p2"]
        assert len(selected) == 2

    def test_select_returns_empty_for_no_matches(self):
        r = self._results()
        selected = r.select(["nope"])
        assert len(selected) == 0

    def test_len_and_iter(self):
        r = self._results()
        assert len(r) == 2
        assert [x.path for x in r] == ["p1", "p2"]

    def test_equality(self):
        assert self._results() == self._results()
