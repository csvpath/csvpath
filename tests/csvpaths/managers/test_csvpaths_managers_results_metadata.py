import unittest
from uuid import UUID, uuid4

from csvpath.managers.results.results_metadata import ResultsMetadata


class TestCsvPathsManagersResultsMetadata(unittest.TestCase):
    def test_run_uuid_setter_mirrors_into_uuid(self) -> None:
        m = ResultsMetadata(None)
        u = uuid4()
        m.run_uuid = u
        assert m.run_uuid == u
        assert m.uuid == u

    def test_run_uuid_string_setter_mirrors_into_uuid_string(self) -> None:
        m = ResultsMetadata(None)
        s = str(uuid4())
        m.run_uuid_string = s
        assert m.run_uuid_string == s
        assert m.uuid_string == s

    def test_from_manifest_run_uuid_overrides_manifests_own_uuid(self) -> None:
        # uuid is vestigial at run scope -- from_manifest reads the
        # manifest's own "uuid" field first (base Metadata behavior),
        # then run_uuid_string mirrors over it so the two never diverge.
        m = ResultsMetadata(None)
        run_uuid = str(uuid4())
        manifest = {
            "run_home": "some/run/home",
            "uuid": str(uuid4()),
            "run_uuid": run_uuid,
            "named_paths_uuid": str(uuid4()),
            "named_file_uuid": str(uuid4()),
        }
        m.from_manifest(manifest)
        assert m.run_uuid_string == run_uuid
        assert m.uuid_string == run_uuid

    def test_named_paths_fingerprint_defaults_to_none(self) -> None:
        m = ResultsMetadata(None)
        assert m.named_paths_fingerprint is None

    def test_from_manifest_reads_named_paths_fingerprint(self) -> None:
        m = ResultsMetadata(None)
        manifest = {
            "run_home": "some/run/home",
            "uuid": str(uuid4()),
            "run_uuid": str(uuid4()),
            "named_paths_uuid": str(uuid4()),
            "named_file_uuid": str(uuid4()),
            "named_paths_fingerprint": "abc123",
        }
        m.from_manifest(manifest)
        assert m.named_paths_fingerprint == "abc123"

    def test_from_manifest_reads_named_file_size(self) -> None:
        # register_complete() rebuilds the metadata from the run manifest and
        # writes it back; an empty key ("") dropped the size on every run
        # (RC triage A20, David 2026-11-15)
        m = ResultsMetadata(None)
        m.from_manifest(
            {
                "run_home": "some/run/home",
                "uuid": str(uuid4()),
                "run_uuid": str(uuid4()),
                "named_paths_uuid": str(uuid4()),
                "named_file_uuid": str(uuid4()),
                "named_file_size": 224,
            }
        )
        assert m.named_file_size == 224

    def test_from_manifest_reads_named_file_last_change(self) -> None:
        # same empty-key bug as named_file_size: the value was dropped on
        # every rebuild (results_metadata.py:140, David 2026-11-16)
        m = ResultsMetadata(None)
        m.from_manifest(
            {
                "run_home": "some/run/home",
                "uuid": str(uuid4()),
                "run_uuid": str(uuid4()),
                "named_paths_uuid": str(uuid4()),
                "named_file_uuid": str(uuid4()),
                "named_file_last_change": "2026-01-01T00:00:00+00:00",
            }
        )
        assert m.named_file_last_change == "2026-01-01T00:00:00+00:00"
