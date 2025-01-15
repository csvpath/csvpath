import unittest
import pytest
import shutil
import os
from csvpath import CsvPaths
from csvpath.util.nos import Nos
from csvpath.matching.util.exceptions import MatchException

DIR = "tests/test_resources/named_files"
JSON = "tests/test_resources/named_files.json"


class TestFilesManager(unittest.TestCase):
    def test_named_files_home(self):
        paths = CsvPaths()
        m = paths.file_manager
        d = m.named_files_dir
        assert d is not None
        assert d.endswith("inputs/named_files")

    def test_named_file_home(self):
        paths = CsvPaths()
        m = paths.file_manager
        d = m.named_file_home("aname")
        assert d is not None
        assert d.endswith("inputs/named_files/aname")

    def test_copy_in(self):
        paths = CsvPaths()
        m = paths.file_manager
        tf = "tests/test_resources/test.csv"
        home = m.assure_file_home("mytest", tf)
        d = m._copy_in(tf, home)
        assert d is not None
        assert d.endswith("inputs/named_files/mytest/test.csv/test.csv")
        # p = "inputs/named_files/mytest"
        p = f"{paths.config.inputs_files_path}/mytest"
        # if paths.config.inputs_files_path.find("://") > -1:
        # p = f"{paths.config.inputs_files_path}/{p}"
        Nos(p).remove()

    def test_reg_fingerprint(self):
        paths = CsvPaths()
        m = paths.file_manager
        tf = "tests/test_resources/test.csv"
        home = m.assure_file_home("mytest", tf)
        d = m._copy_in(tf, home)
        assert Nos(d).exists()
        rpath = m._fingerprint(home)
        assert d != rpath
        assert not Nos(d).exists()
        p = f"{paths.config.inputs_files_path}/mytest"
        # if paths.config.inputs_files_path.find("://") > -1:
        #    p = f"{paths.config.inputs_files_path}/{p}"
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
        m = paths.file_manager
        reg = m.registrar
        try:
            shutil.rmtree("inputs/named_files/testx")
        except Exception:
            pass
        m.add_named_file(name="testx", path="tests/test_resources/test.csv")
        m.add_named_file(name="testx", path="tests/test_resources/test.csv")
        m.add_named_file(name="testx", path="tests/test_resources/test.csv")
        mpath = reg.manifest_path(m.named_file_home("testx"))
        m = reg.get_manifest(mpath)
        #
        # file manager should add only 1x to manifest.json because the
        # fingerprint and filename has not changed.
        #
        assert len(m) == 1

    def test_file_mgr_dir1(self):
        paths = CsvPaths()
        fm = paths.file_manager
        fm.remove_all_named_files()
        fm.add_named_files_from_dir(DIR)
        assert fm.named_files_count == 6

    def test_file_mgr_json1(self):
        paths = CsvPaths()
        fm = paths.file_manager
        fm.remove_all_named_files()
        assert fm.named_files_count == 0
        fm.set_named_files_from_json(JSON)
        assert fm.named_files_count == 2

    def test_file_mgr_json2(self):
        paths = CsvPaths()
        paths.config.csvpaths_errors_policy = ["raise"]
        fm = paths.file_manager
        with pytest.raises(MatchException):
            fm.set_named_files_from_json("xyz")

    def test_file_mgr_dict1(self):
        paths = CsvPaths()
        fm = paths.file_manager
        nf = {
            "wonderful": "tests/test_resources/food.csv",
            "amazing": "tests/test_resources/lookup_names.csv",
        }
        fm.set_named_files(nf)
        assert fm.named_files_count >= 2
        assert fm.name_exists("wonderful")
        assert fm.name_exists("amazing")

        # Nos(f"{paths.config.inputs_files_path}/inputs/named_files/wonderful").remove()
        p = f"{paths.config.inputs_files_path}/wonderful"
        # if paths.config.inputs_files_path.find("://") > -1:
        #    p = f"{paths.config.inputs_files_path}/{p}"
        Nos(p).remove()
        # Nos(f"{paths.config.inputs_files_path}/inputs/named_files/amazing").remove()
        p = f"{paths.config.inputs_files_path}/amazing"
        # if paths.config.inputs_files_path.find("://") > -1:
        #    p = f"{paths.config.inputs_files_path}/{p}"
        Nos(p).remove()

    def test_file_mgr_dict2(self):
        paths = CsvPaths()
        fm = paths.file_manager
        try:
            fm.remove_named_file("wonderful")
            fm.remove_named_file("outstanding")
        except FileNotFoundError:
            pass
        nf = {
            "wonderful": "tests/test_resources/food.csv",
            "amazing": "tests/test_resources/lookup_names.csv",
        }
        fm.set_named_files(nf)
        c = fm.named_files_count
        fm.add_named_file(name="outstanding", path="tests/test_resources/test.csv")
        c2 = fm.named_files_count
        assert c2 == (c + 1)
        afile = fm.get_named_file("wonderful")
        assert afile is not None
        fm.remove_named_file("wonderful")
        assert fm.named_files_count == c

        # Nos(f"{paths.config.inputs_files_path}/inputs/named_files/outstanding").remove()
        p = f"{paths.config.inputs_files_path}/outstanding"
        # if paths.config.inputs_files_path.find("://") > -1:
        #    p = f"{paths.config.inputs_files_path}/{p}"
        Nos(p).remove()

        # Nos(f"{paths.config.inputs_files_path}/inputs/named_files/amazing").remove()
        p = f"{paths.config.inputs_files_path}/amazing"
        # if paths.config.inputs_files_path.find("://") > -1:
        #    p = f"{paths.config.inputs_files_path}/{p}"
        Nos(p).remove()
