import pytest

from csvpath.references.reference_results_3 import ReferenceResult3, ReferenceResults3


class TestReferenceResult3:
    @pytest.mark.parametrize("bad_path", [None, ""])
    def test_rejects_none_or_empty_path(self, bad_path):
        with pytest.raises(ValueError):
            ReferenceResult3(path=bad_path, uuid="u1")

    def test_rejects_empty_uuid(self):
        with pytest.raises(ValueError):
            ReferenceResult3(path="p1", uuid="")

    def test_allows_none_uuid(self):
        # a directory-level, name_three-absent result has no single
        # version/registration to identify -- None, not empty string,
        # is the correct "no uuid" value.
        r = ReferenceResult3(path="p1", uuid=None)
        assert r.uuid is None

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

    def test_identity_defaults_to_none(self):
        r = ReferenceResult3(path="p1", uuid="u1")
        assert r.identity is None

    def test_identity_is_settable_at_construction(self):
        # added 2026-08-13 for CSVPATHS' statement-level range selector
        # -- path/uuid alone are identical across every statement in a
        # range (CSVPATHS has no per-statement uuid), so identity is
        # what lets _extract_data() tell them apart.
        r = ReferenceResult3(path="p1", uuid="u1", identity="my_validations")
        assert r.identity == "my_validations"

    def test_rejects_empty_identity(self):
        with pytest.raises(ValueError):
            ReferenceResult3(path="p1", uuid="u1", identity="")

    def test_equality_considers_identity(self):
        a = ReferenceResult3(path="p1", uuid="u1", identity="a")
        b = ReferenceResult3(path="p1", uuid="u1", identity="a")
        c = ReferenceResult3(path="p1", uuid="u1", identity="b")
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

    def test_select_by_identity(self):
        # added 2026-08-13 -- needed when path/uuid are identical across
        # results (CSVPATHS' statement-level range), identity is the
        # only thing that can distinguish them for resolve_from().
        results = [
            ReferenceResult3(path="p1", uuid="u1", identity="a"),
            ReferenceResult3(path="p1", uuid="u1", identity="b"),
        ]
        r = ReferenceResults3(results=results)
        selected = r.select(["a"])
        assert len(selected) == 1
        assert selected.results[0].identity == "a"

    def test_len_and_iter(self):
        r = self._results()
        assert len(r) == 2
        assert [x.path for x in r] == ["p1", "p2"]

    def test_equality(self):
        assert self._results() == self._results()

    def test_deduplicated_with_no_duplicates_is_unchanged(self):
        r = self._results()
        assert r.deduplicated().files == ["p1", "p2"]

    def test_deduplicated_collapses_exact_duplicates(self):
        results = [
            ReferenceResult3(path="p1", uuid="u1"),
            ReferenceResult3(path="p2", uuid="u2"),
            ReferenceResult3(path="p1", uuid="u1"),
        ]
        r = ReferenceResults3(results=results)
        deduped = r.deduplicated()
        assert deduped.files == ["p1", "p2"]
        assert len(deduped) == 2

    def test_deduplicated_preserves_first_occurrence_order(self):
        results = [
            ReferenceResult3(path="p3", uuid="u3"),
            ReferenceResult3(path="p1", uuid="u1"),
            ReferenceResult3(path="p3", uuid="u3"),
            ReferenceResult3(path="p2", uuid="u2"),
        ]
        r = ReferenceResults3(results=results)
        assert r.deduplicated().files == ["p3", "p1", "p2"]

    def test_deduplicated_uses_full_equality_not_just_path(self):
        # same path+uuid but different data, or different identity, are
        # NOT duplicates -- see ReferenceResult3.__eq__ and its own
        # identity docstring for why.
        results = [
            ReferenceResult3(path="p1", uuid="u1", data="a"),
            ReferenceResult3(path="p1", uuid="u1", data="b"),
            ReferenceResult3(path="p1", uuid="u1", identity="x"),
            ReferenceResult3(path="p1", uuid="u1", identity="y"),
        ]
        r = ReferenceResults3(results=results)
        assert len(r.deduplicated()) == 4

    def test_deduplicated_on_empty_results_is_empty(self):
        assert ReferenceResults3().deduplicated().results == []

    def test_deduplicated_returns_a_new_instance_not_the_original(self):
        r = self._results()
        deduped = r.deduplicated()
        assert deduped is not r
        deduped.remove(deduped.results[0])
        assert len(r) == 2


class TestRemove:
    def _results(self, n=3):
        return ReferenceResults3(
            results=[ReferenceResult3(path=f"p{i}", uuid=f"u{i}") for i in range(n)]
        )

    def test_remove_drops_the_entry(self):
        r = self._results()
        target = r.results[1]
        r.remove(target)
        assert r.files == ["p0", "p2"]
        assert len(r) == 2

    def test_remove_missing_result_raises(self):
        r = self._results()
        stranger = ReferenceResult3(path="nope", uuid="nope")
        with pytest.raises(ValueError):
            r.remove(stranger)

    def test_iterate_and_remove_in_the_same_loop_skips_nothing(self):
        # the exact workflow this method exists for: walk the results,
        # remove the ones you do not want, keep the rest. if __iter__
        # returned the live list instead of a snapshot, removing p1
        # while iterating would shift p2 into p1's old slot and the
        # loop would skip over it.
        r = self._results()
        seen = []
        for result in r:
            seen.append(result.path)
            if result.path == "p1":
                r.remove(result)
        assert seen == ["p0", "p1", "p2"]
        assert r.files == ["p0", "p2"]

    def test_trimmed_results_can_be_handed_to_resolve_from(self):
        # the end-to-end shape David described: iterate, remove some,
        # then pass the trimmed object straight to a finder.
        from csvpath.references.reference_finder_3 import ReferenceFinder3
        from csvpath.references.reference_parser_3 import ReferenceParser3

        class _DummyFinder(ReferenceFinder3):
            def query(self):
                raise AssertionError("resolve_from(a ReferenceResults3) must not requery")

            def _extract_data(self, result):
                return f"data-for-{result.path}"

        ref = ReferenceParser3(string="$acme.results.a.:errors()", csvpaths=object())
        results = self._results()
        for result in results:
            if result.path == "p1":
                results.remove(result)

        finder = _DummyFinder(csvpaths=object(), ref=ref)
        resolved = finder.resolve_from(results)
        assert resolved.files == ["p0", "p2"]
