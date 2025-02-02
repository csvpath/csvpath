import unittest
import pytest
import shutil
import os
from csvpath import CsvPaths
from csvpath.util.nos import Nos
from csvpath.matching.util.exceptions import MatchException

DIR = f"tests{os.sep}test_resources{os.sep}named_files"
JSON = f"tests{os.sep}test_resources{os.sep}named_files.json"


class TestFilesManager(unittest.TestCase):
    def test_named_files_home(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise")
        m = paths.file_manager
        d = m.named_files_dir
        assert d is not None
        assert d.endswith(f"inputs{os.sep}named_files")

    def test_named_file_home(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise")
        m = paths.file_manager
        d = m.named_file_home("aname")
        assert d is not None
        assert d.endswith(f"inputs{os.sep}named_files{os.sep}aname")

    def test_copy_in(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise")
        m = paths.file_manager
        tf = f"tests{os.sep}test_resources{os.sep}test.csv"
        home = m.assure_file_home("mytest", tf)
        d = m._copy_in(tf, home)
        assert d is not None
        assert d.endswith(
            f"inputs{os.sep}named_files{os.sep}mytest{os.sep}test.csv{os.sep}test.csv"
        )
        p = f"{paths.config.inputs_files_path}{os.sep}mytest"
        Nos(p).remove()

    def test_reg_fingerprint(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise")
        m = paths.file_manager
        tf = f"tests{os.sep}test_resources{os.sep}test.csv"
        home = m.assure_file_home("mytest", tf)
        d = m._copy_in(tf, home)
        assert Nos(d).exists()
        rpath = m._fingerprint(home)
        assert d != rpath
        assert not Nos(d).exists()
        p = f"{paths.config.inputs_files_path}{os.sep}mytest"
        Nos(p).remove()

    """
    # this test would need to be converted to use FileMetadata. not
    # sure if it adds enough value or not.
    def test_manifest_path(self):
        paths = CsvPaths()
        m = paths.file_manager
        m.add_named_file(name="aname", path="tests/test_resources/test.csv")
        reg = m.registrar
        d = m.named_file_home("aname")
        assert d is not None
        assert d == "inputs/named_files/aname"
        mpath = reg.manifest_path(d)
        assert mpath == os.path.join(d, "manifest.json")
        reg.update_manifest(
            manifestpath=mpath,
            regpath="regpath",
            sourcepath="origpath",
            fingerprint="fingerprint",
        )
        m = reg.get_manifest(mpath)
        assert "file" in m[len(m) - 1]
        assert m[len(m) - 1]["file"] == "regpath"
        assert "from" in m[len(m) - 1]
        assert m[len(m) - 1]["from"] == "origpath"
        assert "time" in m[len(m) - 1]
        r = reg.registered_file(d)
        assert r == "regpath"
        shutil.rmtree("inputs/named_files/aname")
    """

    def test_rereg(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise")
        m = paths.file_manager
        reg = m.registrar
        try:
            shutil.rmtree(f"inputs{os.sep}named_files{os.sep}testx")
        except Exception:
            pass
        m.add_named_file(
            name="testx", path=f"tests{os.sep}test_resources{os.sep}test.csv"
        )
        m.add_named_file(
            name="testx", path=f"tests{os.sep}test_resources{os.sep}test.csv"
        )
        m.add_named_file(
            name="testx", path=f"tests{os.sep}test_resources{os.sep}test.csv"
        )
        mpath = reg.manifest_path(m.named_file_home("testx"))
        m = reg.get_manifest(mpath)
        #
        # file manager should add only 1x to manifest.json because the
        # fingerprint and filename has not changed.
        #
        assert len(m) == 1

    def test_file_mgr_dir1(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise")
        fm = paths.file_manager
        fm.remove_all_named_files()
        fm.add_named_files_from_dir(DIR)
        assert fm.named_files_count == 6

    def test_file_mgr_json1(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise")
        fm = paths.file_manager
        fm.remove_all_named_files()
        assert fm.named_files_count == 0
        fm.set_named_files_from_json(JSON)
        assert fm.named_files_count == 2

    def test_file_mgr_json2(self):
        paths = CsvPaths()
        # setting this config shouldn't be needed here, right?
        paths.config.add_to_config("errors", "csvpath", "raise")
        fm = paths.file_manager
        with pytest.raises(FileNotFoundError):
            fm.set_named_files_from_json("xyz")

    def test_file_mgr_dict1(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise")
        fm = paths.file_manager
        nf = {
            "wonderful": f"tests{os.sep}test_resources{os.sep}food.csv",
            "amazing": f"tests{os.sep}test_resources{os.sep}lookup_names.csv",
        }
        fm.set_named_files(nf)
        assert fm.named_files_count >= 2
        assert fm.name_exists("wonderful")
        assert fm.name_exists("amazing")
        p = f"{paths.config.inputs_files_path}{os.sep}wonderful"
        Nos(p).remove()
        p = f"{paths.config.inputs_files_path}{os.sep}amazing"
        Nos(p).remove()

    def test_file_mgr_dict2(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise")
        fm = paths.file_manager
        try:
            fm.remove_named_file("wonderful")
            fm.remove_named_file("outstanding")
        except FileNotFoundError:
            pass
        nf = {
            "wonderful": f"tests{os.sep}test_resources{os.sep}food.csv",
            "amazing": f"tests{os.sep}test_resources{os.sep}lookup_names.csv",
        }
        fm.set_named_files(nf)
        c = fm.named_files_count
        fm.add_named_file(
            name="outstanding", path=f"tests{os.sep}test_resources{os.sep}test.csv"
        )
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
