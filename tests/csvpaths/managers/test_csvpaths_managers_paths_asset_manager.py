import unittest
from uuid import uuid4

from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader
from tests.csvpaths.builder import Builder


class TestCsvPathsAssetManager(unittest.TestCase):
    def test_get_assets_dir_path_1(self):
        name = f"{uuid4()}"
        apath = "$[*][yes()]"
        paths = Builder().build()
        pmgr = paths.paths_manager
        amgr = paths.paths_manager.asset_manager
        pmgr.add_named_paths(name=name, paths=[apath])
        #
        # test
        #
        assets = amgr.assets_dir_path(name)
        assert assets
        home = pmgr.named_paths_home(name)
        Nos(home).join("assets") == assets
        #
        # cleanup
        #
        pmgr.remove_named_paths(name)

    def test_get_assets_dir_path_2(self):
        #
        # note: v1/v2 references apparently expect to start with letters, not numbers.
        # this could be a problem, but has existed forever. v3 will likely remove this
        # requirement.
        #
        name = f"a{uuid4()}"
        ref = f"${name}.csvpaths.:1"
        apath = "$[*][yes()]"
        paths = Builder().build()
        pmgr = paths.paths_manager
        amgr = paths.paths_manager.asset_manager
        pmgr.add_named_paths(name=name, paths=[apath])
        #
        # test
        #
        assets = amgr.assets_dir_path(ref)
        assert assets
        home = pmgr.named_paths_home(name)
        Nos(home).join("assets") == assets
        #
        # cleanup
        #
        pmgr.remove_named_paths(name)

    def test_store_asset_1(self):
        name = f"{uuid4()}"
        apath = "$[*][yes()]"
        paths = Builder().build()
        paths.paths_manager.add_named_paths(name=name, paths=[apath])
        home = paths.paths_manager.named_paths_home(name)
        mgr = paths.paths_manager.asset_manager
        #
        # test
        #
        assets = mgr.assets_dir_path(name)
        assert assets
        a = Nos(home).join("assets")
        a == assets

        c = '{"a":"b"}'
        mgr.store_asset_file(name=name, filename="asset1.json", contents=c)
        asset = Nos(a).join("asset1.json")
        nos = Nos(asset)
        assert nos.exists()

        with DataFileReader(nos.path) as reader:
            assert c == reader.read()
        #
        # list
        #
        lst = mgr.list_asset_files(name)
        assert lst is not None
        assert len(lst) == 1
        assert lst[0] == "asset1.json"
        #
        # delete
        #
        mgr.delete_asset_file(name, "asset1.json")
        assert not nos.exists()

        #
        # cleanup
        #
        paths.paths_manager.remove_named_paths(name)

        assert not Nos(a).dir_exists()
