import unittest
import os
import time
import paramiko
import stat
from csvpath import CsvPaths
from csvpath.util.var_utility import VarUtility

USER = "tinpenny"
PASSWORD = "tinpenny"


class TestSftpMode(unittest.TestCase):
    def test_load_named_file_from_sftp(self):
        if not self._check_for_server():
            return
        #
        # tests if the sftp backend let's us use sftp:// to do add_named_file.
        # this may not be the best place for this test, but it's good enough.
        #
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")

        print(f"paths.config from: {paths.config._configpath}")
        print(
            f"paths.config: env: {os.environ.get(paths.config.CSVPATH_CONFIG_FILE_ENV)}"
        )

        #
        # requires user tinpenny with an orders.csv at their root
        #
        server = paths.config.get(section="sftp", name="server")
        port = paths.config.get(section="sftp", name="port")
        paths.file_manager.add_named_file(
            name="orders", path=f"sftp://{server}:{port}/orders.csv"
        )
        path = '$[*][ print("0: $.headers.0, 2: $.headers.2")]'
        d = {"process": [f"{path}"]}
        paths.paths_manager.set_named_paths(d)
        paths.collect_paths(filename="orders", pathsname="process")
        results = paths.results_manager.get_named_results("process")
        assert len(results) == 1
        assert paths.results_manager.is_valid("process")

    def test_sftp_send(self):
        if not self._check_for_server():
            return
        self._clear()
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.config.add_to_config("listeners", "groups", "sftp")
        paths.config.add_to_config(
            "listeners",
            "sftp.results",
            "from csvpath.managers.integrations.sftp.sftp_sender import SftpSender",
        )
        paths.file_manager.add_named_files_from_dir(
            f"tests{os.sep}examples{os.sep}sftp{os.sep}csvs"
        )
        paths.paths_manager.add_named_paths_from_json(
            f"tests{os.sep}examples{os.sep}sftp{os.sep}group.json"
        )
        paths.collect_paths(filename="March-2024", pathsname="sftptest")
        #
        # how to check arrival?
        #
        time.sleep(1)
        self._check_arrival([f"dirname{os.sep}data.csv", f"dirname{os.sep}foo.json"])

    def _clear(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect("localhost", 10022, USER, PASSWORD)
            sftp = client.open_sftp()
            for entry in sftp.listdir_attr(f".{os.sep}dirname"):
                print(f"\nfound a file or dir: {entry.filename}")
                if not stat.S_ISDIR(entry.st_mode):  # Changed to use stat module
                    sftp.remove(f".{os.sep}dirname{os.sep}{entry.filename}")
            sftp.close()
        except Exception:
            ...
        finally:
            client.close()

    def _check_arrival(self, paths):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect("localhost", 10022, USER, PASSWORD)
            sftp = client.open_sftp()
            for path in paths:
                print(f"checking localhost:10022 in {USER} for {path}")
                sftp.stat(path)
            sftp.close()
        finally:
            client.close()

    def _check_for_server(self):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect("localhost", 10022, USER, PASSWORD)
        except Exception as e:
            print(e)
            print("WARNING: cannot run sftp test")
            print(
                f"required: localhost:10022 with the {USER} account and an {PASSWORD} env var"
            )
            return False
        finally:
            try:
                client.close()
            except Exception:
                ...
        print("SFTP mode: _check_for_server: server is ready to test")
        return True
