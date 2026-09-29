import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

from csvpath.managers.metadata import Metadata
from csvpath.util.config import Config
from csvpath.managers.integrations.ol.v2.util.protocol_utility import (
    ProtocolUtility as prut,
)
from csvpath.managers.integrations.ol.v2.util.name_utility import NameUtility as naut


class TestCsvPathsExamplesOpenLineageProtocolUtility(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock(spec=Config)
        self.mock_mdata = MagicMock(spec=Metadata)
        self.mock_mdata.project_context = None
        self.mock_mdata.project = None

    #
    # name tests
    #
    def test_csvpaths_examples_openlineage_namespaces_naut(self) -> None:
        file = "/users/bats/data/inputs/mydata/raw"
        root = "data/inputs"
        assert naut.trim_namespace_if(namespace=root, path=file) == "mydata/raw"

    #
    # protocol tests
    #
    def test_csvpaths_examples_openlineage_namespaces_update_protocol_if_raises_on_none_root(
        self,
    ):
        with self.assertRaises(ValueError) as ctx:
            prut.update_protocol_if(
                config=self.mock_config, mdata=self.mock_mdata, root=None
            )
        self.assertIn("URI cannot be None", str(ctx.exception))

    def test_csvpaths_examples_openlineage_namespaces_update_protocol_if_raises_on_empty_root(
        self,
    ):
        with self.assertRaises(ValueError) as ctx:
            prut.update_protocol_if(
                config=self.mock_config, mdata=self.mock_mdata, root="   "
            )
        self.assertIn("URI cannot be empty", str(ctx.exception))

    def test_csvpaths_examples_openlineage_namespaces_update_protocol_if_raises_on_none_config(
        self,
    ):
        with self.assertRaises(ValueError) as ctx:
            prut.update_protocol_if(
                config=None, mdata=self.mock_mdata, root="some/path"
            )
        self.assertIn("Config cannot be None", str(ctx.exception))

    def test_csvpaths_examples_openlineage_namespaces_update_protocol_if_raises_on_none_metadata(
        self,
    ):
        with self.assertRaises(ValueError) as ctx:
            prut.update_protocol_if(
                config=self.mock_config, mdata=None, root="some/path"
            )
        self.assertIn("Metadata cannot be None", str(ctx.exception))

    # -------------------------------------------------------------------------
    # Strategy: 'strip'
    # -------------------------------------------------------------------------

    def test_csvpaths_examples_openlineage_namespaces_strategy_strip_removes_protocol(
        self,
    ):
        self.mock_config.get.return_value = "strip"
        result = prut.update_protocol_if(
            config=self.mock_config,
            mdata=self.mock_mdata,
            root="s3://bucket/path/file.csv",
        )
        self.assertEqual(result, "bucket/path/file.csv")

    def test_csvpaths_examples_openlineage_namespaces_strategy_strip_no_protocol_returns_unchanged(
        self,
    ):
        self.mock_config.get.return_value = "strip"
        result = prut.update_protocol_if(
            config=self.mock_config,
            mdata=self.mock_mdata,
            root="relative/path/file.csv",
        )
        self.assertEqual(result, "relative/path/file.csv")

    # -------------------------------------------------------------------------
    # Strategy: 'name'
    # -------------------------------------------------------------------------

    def test_csvpaths_examples_openlineage_namespaces_strategy_name_returns_last_path_segment(
        self,
    ):
        self.mock_config.get.return_value = "name"
        result = prut.update_protocol_if(
            config=self.mock_config,
            mdata=self.mock_mdata,
            root="/var/data/inputs/orders",
        )
        self.assertEqual(result, "csvpath://orders")

    def test_csvpaths_examples_openlineage_namespaces_strategy_name_root_slash_fallback(
        self,
    ):
        self.mock_config.get.return_value = "name"
        result = prut.update_protocol_if(
            config=self.mock_config, mdata=self.mock_mdata, root="/"
        )
        self.assertEqual(result, "csvpath:///")

    # -------------------------------------------------------------------------
    # Strategy: 'project'
    # -------------------------------------------------------------------------

    def test_csvpaths_examples_openlineage_namespaces_strategy_project_with_context_and_project_name(
        self,
    ):
        self.mock_config.get.return_value = "project"
        self.mock_mdata.project_context = "my_org"
        self.mock_mdata.project = "claims_app"

        result = prut.update_protocol_if(
            config=self.mock_config, mdata=self.mock_mdata, root="s3://bucket/data"
        )
        # Note: tests current code logic for _project_if
        self.assertTrue(result.startswith("csvpath://"))

    def test_csvpaths_examples_openlineage_namespaces_strategy_project_without_metadata_falls_back_to_root(
        self,
    ):
        self.mock_config.get.return_value = "project"
        self.mock_mdata.project_context = None
        self.mock_mdata.project = None

        result = prut.update_protocol_if(
            config=self.mock_config,
            mdata=self.mock_mdata,
            root="https://my.storage.com/files",
        )
        self.assertEqual(result, "csvpath://my.storage.com/files")

    def test_csvpaths_examples_openlineage_namespaces_strategy_project_without_metadata_falls_back_to_root_2(
        self,
    ):
        self.mock_config.get.return_value = "project"
        self.mock_mdata.project_context = "testing"
        self.mock_mdata.project = "unit"

        result = prut.update_protocol_if(
            config=self.mock_config,
            mdata=self.mock_mdata,
            root="https://my.storage.com/files",
        )
        self.assertEqual(result, "csvpath://testing/unit/files")

    # -------------------------------------------------------------------------
    # Strategy: 'default' / ""
    # -------------------------------------------------------------------------

    @patch("csvpath.managers.integrations.ol.v2.util.protocol_utility.Nos")
    def test_csvpaths_examples_openlineage_namespaces_strategy_default_local_absolute_path_returns_uri(
        self, mock_nos_class
    ):
        self.mock_config.get.return_value = "default"
        mock_nos = mock_nos_class.return_value
        mock_nos.is_local = True
        mock_nos.is_azure = False

        test_path = "/Users/me/data/file.csv"
        expected_uri = Path(test_path).as_uri()

        result = prut.update_protocol_if(
            config=self.mock_config, mdata=self.mock_mdata, root=test_path
        )
        self.assertEqual(result, expected_uri)

    @patch("csvpath.managers.integrations.ol.v2.util.protocol_utility.Nos")
    def test_csvpaths_examples_openlineage_namespaces_strategy_default_local_already_file_uri(
        self, mock_nos_class
    ):
        self.mock_config.get.return_value = ""
        mock_nos = mock_nos_class.return_value
        mock_nos.is_local = True

        root_uri = "file:///var/log/app.log"
        result = prut.update_protocol_if(
            config=self.mock_config, mdata=self.mock_mdata, root=root_uri
        )
        self.assertEqual(result, root_uri)

    @patch("csvpath.managers.integrations.ol.v2.util.protocol_utility.azut")
    @patch("csvpath.managers.integrations.ol.v2.util.protocol_utility.Nos")
    def test_csvpaths_examples_openlineage_namespaces_strategy_default_azure_path(
        self, mock_nos_class, mock_azut
    ):
        self.mock_config.get.return_value = "default"
        mock_nos = mock_nos_class.return_value
        mock_nos.is_local = False
        mock_nos.is_azure = True
        mock_azut.my_protocol.return_value = "azfs://"

        result = prut.update_protocol_if(
            config=self.mock_config,
            mdata=self.mock_mdata,
            root="az://container/blob.json",
        )
        self.assertEqual(result, "azfs://container/blob.json")

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def test_csvpaths_examples_openlineage_namespaces_strip_protocol_if_with_protocol(
        self,
    ):
        self.assertEqual(prut._strip_protocol_if("s3://bucket/key"), "bucket/key")
        self.assertEqual(prut._strip_protocol_if("file:///path/to"), "/path/to")

    def test_csvpaths_examples_openlineage_namespaces_strip_protocol_if_without_protocol(
        self,
    ):
        self.assertEqual(prut._strip_protocol_if("relative/path"), "relative/path")


if __name__ == "__main__":
    unittest.main()
