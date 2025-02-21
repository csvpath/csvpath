import unittest
import os
import time
import paramiko
import stat
from csvpath import CsvPaths
from csvpath.util.var_utility import VarUtility


class TestSftpVarValues(unittest.TestCase):
    def test_sftp_var_values(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_files_from_dir(
            f"tests{os.sep}examples{os.sep}sftp{os.sep}csvs"
        )
        paths.paths_manager.add_named_paths_from_json(
            f"tests{os.sep}examples{os.sep}sftp{os.sep}group.json"
        )
        paths.collect_paths(filename="March-2024", pathsname="sftptest")
        r = paths.results_manager.get_specific_named_result("sftptest", "upc-sku")
        assert r
        m = r.csvpath.metadata
        v = r.csvpath.variables
        lst = VarUtility.get_value_pairs(m, v, "sftp-files")
        assert lst
        assert len(lst) == 3
        assert lst[0] == ("data.csv", "data.csv")
        assert lst[1] == ("errors.json", "foo.json")
        assert lst[2] == ("meta.json", "dirname")
        #
        # get a string
        # get a var|var-name (tested above)
        # get an ENV_VAR
        #
        os.environ["SFTP_USER"] = "auser"
        m["sftp-user"] = "SFTP_USER"
        v = VarUtility.get_str(m, v, "sftp-user")
        assert v == "auser"

        v = VarUtility.get_int(m, v, "sftp-port")
        assert v == 10022

        v = VarUtility.get_bool(m, v, "sftp-original")
        v is False

        r.csvpath.metadata["sftp-original"] = True
        v = VarUtility.get_bool(m, v, "sftp-original")
        v is True

        assert VarUtility.is_true(1)
        assert VarUtility.is_true("yes")
        assert VarUtility.is_true("true")
        assert not VarUtility.is_true(0)
        assert not VarUtility.is_true("no")
        assert not VarUtility.is_true("false")
        assert not VarUtility.is_true(None)
