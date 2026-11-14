import logging
import unittest
from types import SimpleNamespace
from csvpath import CsvPath
from csvpath.managers.integrations.ol.v2.facets.data_provenance import DataProvenance
from csvpath.managers.results.results_metadata import ResultsMetadata

U1 = "6f1c2a4e-0b7d-4a51-9a3e-2d8c5b7e9f01"
U2 = "0d9e8f7a-6b5c-4d3e-8f2a-1b0c9d8e7f62"


def _results_mdata(uuid: str) -> ResultsMetadata:
    """a named-paths group run's metadata: the OL v2 results event builds
    this facet from it. not a ResultMetadata, so it takes the named-file
    branch"""
    mdata = ResultsMetadata(CsvPath().config)
    mdata.named_file_uuid_string = uuid
    mdata.named_file_fingerprint = "fp"
    mdata.named_file_path = "inputs/named_files/orders/orders.csv"
    mdata.named_file_name = "orders"
    return mdata


def _listener(manifest: list[dict]) -> SimpleNamespace:
    #
    # like Config, the config's logger is an attribute (a property on Config),
    # not a method. a plain logger here lets assertLogs see the warning; each
    # Config.logger access reconfigures its handlers and level.
    #
    file_manager = SimpleNamespace(get_manifest=lambda name: manifest)
    config = SimpleNamespace(logger=logging.getLogger("test_ol_data_provenance_facet"))
    return SimpleNamespace(
        csvpaths=SimpleNamespace(file_manager=file_manager),
        config=config,
    )


class TestOlDataProvenanceFacet(unittest.TestCase):
    def test_uuid_found_in_root_manifest(self):
        listener = _listener(
            [{"uuid": U1, "origin_path": "/data/orders.csv", "time": "t1"}]
        )
        dp = DataProvenance.build(listener=listener, mdata=_results_mdata(U1))
        assert dp.uuid == U1
        assert dp.origin_path == "/data/orders.csv"
        assert dp.registered_at == "t1"
        assert dp.fingerprint == "fp"

    def test_uuid_not_in_root_manifest_warns_and_builds(self):
        #
        # this called config.logger(), but logger is a property, so it raised
        # TypeError: 'Logger' object is not callable, not a warning
        #
        listener = _listener([{"uuid": U2}])
        with self.assertLogs(listener.config.logger, level="WARNING") as logs:
            dp = DataProvenance.build(listener=listener, mdata=_results_mdata(U1))
        assert any(f"Could not match UUID {U1} in root manifest" in m for m in logs.output)
        assert dp.uuid == U1
        assert dp.origin_path is None
        assert dp.registered_at is None
