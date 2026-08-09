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
