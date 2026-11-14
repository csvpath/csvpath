import logging
import unittest
from types import SimpleNamespace
from csvpath.managers.integrations.ol.v2.facets.data_provenance import DataProvenance


def _file_mdata(uuid: str) -> SimpleNamespace:
    """stands in for a file registration's metadata (not a ResultMetadata)"""
    return SimpleNamespace(
        named_file_uuid_string=uuid,
        named_file_fingerprint="fp",
        named_file_path="inputs/named_files/orders/orders.csv",
        named_file_name="orders",
    )


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
            [{"uuid": "u1", "origin_path": "/data/orders.csv", "time": "t1"}]
        )
        dp = DataProvenance.build(listener=listener, mdata=_file_mdata("u1"))
        assert dp.uuid == "u1"
        assert dp.origin_path == "/data/orders.csv"
        assert dp.registered_at == "t1"
        assert dp.fingerprint == "fp"

    def test_uuid_not_in_root_manifest_warns_and_builds(self):
        #
        # this called config.logger(), but logger is a property, so it raised
        # TypeError: 'Logger' object is not callable, not a warning
        #
        listener = _listener([{"uuid": "other"}])
        with self.assertLogs(listener.config.logger, level="WARNING") as logs:
            dp = DataProvenance.build(listener=listener, mdata=_file_mdata("u1"))
        assert any("Could not match UUID u1 in root manifest" in m for m in logs.output)
        assert dp.uuid == "u1"
        assert dp.origin_path is None
        assert dp.registered_at is None
