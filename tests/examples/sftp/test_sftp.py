import unittest
import os
import time
import paramiko
import stat
from csvpath import CsvPaths
from csvpath.util.var_utility import VarUtility


class TestSftp(unittest.TestCase):
    def test_sftp_send(self):
        if not self._check_for_server():
            return
        self._clear()
        paths = CsvPaths()
        paths.config.add_to_config("listeners", "groups", "sftp", save_load=False)
        paths.config.add_to_config(
            "listeners",
            "sftp.results",
            "from csvpath.managers.integrations.sftp.sftp_sender import SftpSender",
            save_load=False,
        )
        paths.file_manager.add_named_files_from_dir("tests/examples/sftp/csvs")
        paths.paths_manager.add_named_paths_from_json("tests/examples/sftp/group.json")
        paths.collect_paths(filename="March-2024", pathsname="sftptest")
        #
        # how to check arrival?
        #
        time.sleep(1)
        self._check_arrival(["dirname/data.csv", "dirname/foo.json"])

    def _clear(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect("localhost", 10022, "test_user", os.getenv("SFTP_PASSWORD"))
            sftp = client.open_sftp()
            for entry in sftp.listdir_attr("./dirname"):
                print(f"\nfound a file or dir: {entry.filename}")
                if not stat.S_ISDIR(entry.st_mode):  # Changed to use stat module
                    sftp.remove(f"./dirname/{entry.filename}")
            sftp.close()
        except Exception:
            ...
        finally:
            client.close()

    def _check_arrival(self, paths):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect("localhost", 10022, "test_user", os.getenv("SFTP_PASSWORD"))
            sftp = client.open_sftp()
            for path in paths:
                print(f"checking localhost:10022 in test_user for {path}")
                sftp.stat(path)
            sftp.close()
        finally:
            client.close()

    def _check_for_server(self):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect("localhost", 10022, "test_user", os.getenv("SFTP_PASSWORD"))
        except Exception as e:
            print(e)
            print(
                "WARNING: cannot run sftp test: required: localhost:10022 with test_user account and an SFTP_PASSWORD env var"
            )
            return False
        finally:
            try:
                client.close()
            except Exception:
                ...
        return True

    def test_sftp_var_values(self):
        paths = CsvPaths()
        paths.file_manager.add_named_files_from_dir("tests/examples/sftp/csvs")
        paths.paths_manager.add_named_paths_from_json("tests/examples/sftp/group.json")
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
