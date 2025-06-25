import unittest
import pytest
import shutil
import os
from csvpath import CsvPaths
from csvpath.util.nos import Nos
from csvpath.managers.files.files_listener import FilesListener
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.matching.util.exceptions import MatchException
from csvpath.util.path_util import PathUtility as pathu

DIR = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files"
JSON = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files.json"
FILE = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}test.csv"
WONDERFUL = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}food.csv"
AMAZING = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}lookup_names.csv"


class TestCsvPathsManagersFileManager(unittest.TestCase):

    #
    # base case. add zap, find zap
    #
    def test_files_named_file_exists_1(self) -> None:
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        nf = "zap"
        #
        # clear out anything lingering
        #
        exists = paths.file_manager.has_named_file(nf)
        existed = paths.file_manager.remove_named_file(nf)
        assert not exists or existed
        #
        # should be nothing there now
        #
        assert not paths.file_manager.has_named_file(nf)
        #
        # test
        #
        paths.file_manager.add_named_file(name=nf, path=FILE)
        assert paths.file_manager.has_named_file(nf)
        #
        # clear what we just added
        #
        assert paths.file_manager.remove_named_file(nf)
        assert not paths.file_manager.has_named_file(nf)

    #
    # seen bad case. use of relative path for name. no has, get, or remove should work
    #
    def test_files_named_file_exists_2(self) -> None:
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        nf = "zap/test.csv"
        #
        # clear out anything lingering
        #
        # with pytest.raises(ValueError):
        #
        # this method no longer raises an error. it now just returns False. more intuitive.
        # this seems to be the only test the change broke.
        #
        t = paths.file_manager.has_named_file(nf)
        assert t is False
        with pytest.raises(ValueError):
            paths.file_manager.add_named_file(name=nf, path=FILE)

    def test_files_listener_1(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        reg = FilesListener(paths)
        mdata = FileMetadata(paths.config)
        mdata.named_file_name = None
        mdata.fingerprint = "123"
        mdata.origin_path = "p/d/q"
        mdata.manifest_path = "root/name/manifest.json"
        mdata.name_home = "root/name"
        mdata.file_home = "root/name/filename"
        mdata.file_path = "root/name/filename/version"
        mdata.file_name = "version"
        mdata.mark = "#"
        mdata.type = "files"
        #
        # check mdata to mani transfer
        #
        mani = reg._prep_update(mdata)
        #
        # this will have been reset from the file home to the root of files
        #
        assert mani["manifest_path"] != "root/manifest.json"
        assert mani["manifest_path"] == os.path.join(
            paths.config.get(section="inputs", name="files"), "manifest.json"
        )
        #
        #
        #
        assert mani["uuid"] is not None
        assert mani["time"] is not None
        assert mani["type"] == "files"
        assert mani["file_manifest"] == "root/name/manifest.json"
        assert mani["name_home"] == "root/name"
        assert mani["file_home"] == "root/name/filename"
        assert mani["file_path"] == "root/name/filename/version"
        assert mani["file_name"] == "version"
        assert mani["fingerprint"] == "123"
        assert mani["origin_path"] == "p/d/q"

    def test_files_listener_2(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        grps = paths.config.get(section="listeners", name="groups")
        paths.config.add_to_config("listeners", "groups", "default")
        paths.file_manager.add_named_file(name="testx", path=FILE)
        mani = paths.file_manager.files_root_manifest
        paths.file_manager.add_named_file(name="testy", path=FILE)
        mani2 = paths.file_manager.files_root_manifest
        print(f"mani: {mani} !! {mani2}")
        assert len(mani) + 1 == len(mani2)
        if grps is not None and isinstance(grps, str):
            paths.config.add_to_config("listeners", "groups", grps)

    def test_named_files_home(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        m = paths.file_manager
        d = m.named_files_dir
        d = pathu.norm(d)
        assert d is not None
        assert d.endswith(f"inputs{os.sep}named_files")

    def test_named_file_home(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        m = paths.file_manager
        d = m.named_file_home("aname")
        d = pathu.norm(d)
        assert d is not None
        assert d.endswith(f"inputs{os.sep}named_files{os.sep}aname")

    def test_copy_in(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        m = paths.file_manager
        tf = FILE
        home = m.assure_file_home("mytest", tf)
        d = m._copy_in(tf, home)
        assert d is not None
        ds = pathu.parts(d)
        my = f"{paths.config.inputs_files_path}{os.sep}mytest{os.sep}test.csv{os.sep}test.csv"
        chk = pathu.parts(my)
        assert ds[len(ds) - 3 :] == chk[len(chk) - 3 :]
        Nos(d).remove()

    def test_reg_fingerprint(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        m = paths.file_manager
        home = m.assure_file_home("mytest", FILE)
        d = m._copy_in(FILE, home)
        print(f"test_reg_fingerprint: d1: {d}")
        if d.find("://") == -1:
            d = pathu.norm(d)
        print(f"test_reg_fingerprint: d2: {d}")
        assert Nos(d).exists()
        rpath = m._fingerprint(home)
        assert d != rpath
        assert not Nos(d).exists()
        p = f"{paths.config.inputs_files_path}{os.sep}mytest"
        Nos(p).remove()

    def test_rereg(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        m = paths.file_manager
        reg = m.registrar
        try:
            shutil.rmtree(f"{paths.config.inputs_files_path}{os.sep}testx")
        except Exception:
            pass
        m.add_named_file(name="testx", path=FILE)
        m.add_named_file(name="testx", path=FILE)
        m.add_named_file(name="testx", path=FILE)
        mpath = reg.manifest_path(m.named_file_home("testx"))
        m = reg.get_manifest(mpath)
        #
        # file manager should add only 1x to manifest.json because the
        # fingerprint and filename has not changed.
        #
        assert len(m) == 1

    def test_file_mgr_dir1(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        fm = paths.file_manager
        fm.remove_all_named_files()
        fm.add_named_files_from_dir(DIR)
        assert fm.named_files_count == 4

    def test_file_mgr_json1(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        fm = paths.file_manager
        fm.remove_all_named_files()
        assert fm.named_files_count == 0
        fm.set_named_files_from_json(JSON)
        assert fm.named_files_count == 2

    def test_file_mgr_json2(self):
        paths = CsvPaths()
        # setting this config shouldn't be needed here, right?
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        fm = paths.file_manager
        with pytest.raises((FileNotFoundError, IsADirectoryError)):
            fm.set_named_files_from_json("xyz")

    def test_file_mgr_dict1(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        fm = paths.file_manager
        nf = {
            "wonderful": WONDERFUL,
            "amazing": AMAZING,
        }
        fm.set_named_files(nf)
        assert fm.named_files_count >= 2
        assert fm.has_named_file("wonderful")
        assert fm.has_named_file("amazing")
        fm.remove_named_file("wonderful")
        assert not fm.has_named_file("wonderful")
        fm.remove_named_file("amazing")
        assert not fm.has_named_file("amazing")

    def test_file_mgr_dict2(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        fm = paths.file_manager
        try:
            fm.remove_named_file("wonderful")
            fm.remove_named_file("outstanding")
        except FileNotFoundError:
            pass
        nf = {
            "wonderful": WONDERFUL,
            "amazing": AMAZING,
        }
        fm.set_named_files(nf)
        c = fm.named_files_count
        fm.add_named_file(name="outstanding", path=FILE)
        c2 = fm.named_files_count
        assert c2 == (c + 1)
        afile = fm.get_named_file("wonderful")
        assert afile is not None
        fm.remove_named_file("wonderful")
        assert fm.named_files_count == c
        p = f"{paths.config.inputs_files_path}{os.sep}outstanding"
        Nos(p).remove()
        p = f"{paths.config.inputs_files_path}{os.sep}amazing"
        Nos(p).remove()
