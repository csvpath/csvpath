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
    def test_sftpplus_parse_config(self):
        config1 = None
        with open(
            "tests/test_resources/sftpplus_server_1.ini", "r", encoding="utf-8"
        ) as file:
            config1 = file.read()
        config2 = None
        with open(
            "tests/test_resources/sftpplus_server_2.ini", "r", encoding="utf-8"
        ) as file:
            config2 = file.read()

        existing_uuid = "7d7c2aeb-31c6-4baf-8357-6ffd80c04b21"
        yes_uuid = "7d7c2aeb-31c6-4baf-8357-6ffd80cxxxxx"
        no_uuid = "aaaaaaeb-31c6-4baf-8357-6ffd80c04b21"
        msg = {"uuid": no_uuid}
        tuuid = SftpPlusTransferCreator._find_existing_transfer_in_config_string(
            msg, config1
        )
        print(f"tuuid: {type(tuuid)}")
        assert tuuid is None
        msg = {"uuid": yes_uuid}
        tuuid = SftpPlusTransferCreator._find_existing_transfer_in_config_string(
            msg, config2
        )
        assert tuuid is not None
        assert tuuid == existing_uuid

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
        # time.sleep(1)
        # self._check_arrival(["dirname/data.csv", "dirname/foo.json"])

    def _clear(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect("localhost", 10022, "test_user", os.getenv("SFTP_PASSWORD"))
            sftp = client.open_sftp()
            for entry in sftp.listdir_attr("./csvpath_messages"):
                print(f"\nfound a file or dir: {entry.filename}")
                if not stat.S_ISDIR(entry.st_mode):
                    sftp.remove(f"./csvpath_messages/{entry.filename}")
            for entry in sftp.listdir_attr("./csvpath_messages/handled"):
                print(f"\nfound a file or dir: {entry.filename}")
                if not stat.S_ISDIR(entry.st_mode):
                    sftp.remove(f"./csvpath_messages/handled/{entry.filename}")
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
