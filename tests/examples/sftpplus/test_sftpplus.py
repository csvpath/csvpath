import unittest
import os
import time
import paramiko
import stat
from csvpath import CsvPaths
from csvpath.managers.integrations.sftpplus.transfer_creator import (
    SftpPlusTransferCreator,
)


class TestSftpPlus(unittest.TestCase):
    def test_sftpplus_load_paths(self):
        if not self._check_for_server():
            return
        self._clear()
        paths = CsvPaths()
        paths.config.add_to_config("listeners", "groups", "sftpplus", save_load=False)
        paths.config.add_to_config(
            "listeners",
            "sftpplus.paths",
            "from csvpath.managers.integrations.sftpplus.sftpplus_listener import SftpPlusListener",
            save_load=False,
        )
        paths.paths_manager.add_named_paths_from_dir(
            name="sftpplus", directory="tests/examples/sftpplus/csvpaths"
        )
        #
        # no way to determine automatically if this succeeds yet
        #

    def test_sftpplus_drop_file(self):
        if not self._check_for_server():
            return
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect("localhost", 10022, "tinpenny", "tinpenny")
        sftp = client.open_sftp()
        sftp.put("tests/examples/sftpplus/csvs/March-2024.csv", "orders/March-2024.csv")
        #
        # no way to determine automatically if this succeeds yet
        #

    def test_sftpplus_basic(self):
        if not self._check_for_server():
            return
        self._clear()
        paths = CsvPaths()
        paths.config.add_to_config("listeners", "groups", "sftpplus", save_load=False)
        paths.config.add_to_config(
            "listeners",
            "sftpplus.paths",
            "from csvpath.managers.integrations.sftpplus.sftpplus_listener import SftpPlusListener",
            save_load=False,
        )
        paths.file_manager.add_named_file(
            name="sftpplus-orders", path="tests/examples/sftpplus/csvs/March-2024.csv"
        )
        paths.paths_manager.add_named_paths_from_dir(
            name="sftpplus", directory="tests/examples/sftpplus/csvpaths"
        )
        paths.collect_paths(filename="sftpplus-orders", pathsname="sftpplus")
        #
        # how to check arrival?
        #
        # time.sleep(3)
        # self._check_arrival(["dirname/data.csv", "dirname/foo.json"])

    def _clear(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect("localhost", 10022, "mailbox", "mailbox")
            sftp = client.open_sftp()
            for entry in sftp.listdir_attr("./"):
                print(f"\nfound a file or dir: {entry.filename}")
                if not stat.S_ISDIR(entry.st_mode):
                    sftp.remove(f"./{entry.filename}")
            for entry in sftp.listdir_attr("./csvpath_messages/handled"):
                print(f"\nfound a file or dir: {entry.filename}")
                if not stat.S_ISDIR(entry.st_mode):
                    sftp.remove(f"./handled/{entry.filename}")
            sftp.close()
        except Exception:
            ...
        finally:
            client.close()

    def _check_arrival(self, paths):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect("localhost", 10022, "mailbox", "mailbox")
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
            client.connect("localhost", 10022, "mailbox", "mailbox")
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
