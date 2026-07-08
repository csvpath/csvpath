import unittest
import os

from csvpath.util.nos import Nos
from csvpath.managers.server_config import ServerConfig

from tests.csvpaths.builder import Builder

CSV = os.path.join(
    "tests",
    "csvpaths",
    "examples",
    "csvpaths_examples_transfer_sftp",
    "csvs",
    "March-2024.csv",
)
PATH = os.path.join(
    "tests",
    "csvpaths",
    "examples",
    "csvpaths_examples_transfer_sftp",
    "csvpaths",
    "transfer.csvpath",
)


class TestCsvPathsExamplesTransferNonlocalSftp(unittest.TestCase):
    def test_transfer_non_local_1(self):
        paths = Builder().build()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.config.set(
            section="inputs",
            name="paths",
            value=f"{('mac' if os.sep == '/' else 'windows')}/inputs/named_paths",
        )
        paths.config.set(
            section="inputs",
            name="files",
            value=f"{('mac' if os.sep == '/' else 'windows')}/inputs/named_files",
        )
        paths.config.set(section="sftp", name="username", value="")
        paths.config.set(section="sftp", name="password", value="")
        #
        # clear and add files
        #
        if paths.file_manager.has_named_file("transfer"):
            paths.file_manager.remove_named_file("transfer")
        assert not paths.file_manager.has_named_file("transfer")
        paths.file_manager.add_named_file(name="transfer", path=CSV)
        #
        # clear and add paths
        #
        if paths.paths_manager.has_named_paths("transfer"):
            paths.paths_manager.remove_named_paths("transfer")
        assert not paths.paths_manager.has_named_paths("transfer")
        paths.paths_manager.add_named_paths(name="transfer", from_file=PATH)
        #
        # setup server configs
        #
        config = paths.paths_manager.describer.get_config("transfer")
        config.destinations = {
            "test": ServerConfig(
                address=os.getenv("SFTP_SERVER"),
                port=os.getenv("SFTP_PORT"),
                username=os.getenv("SFTP_USER"),
                password=os.getenv("SFTP_PASSWORD"),
            )
        }
        paths.paths_manager.describer.store_config("transfer", config)
        tpath = (
            f"sftp://{os.getenv('SFTP_SERVER')}:{os.getenv('SFTP_PORT')}/stores.parquet"
        )
        #
        # clear output
        #
        servers = config.destinations
        nos = Nos(tpath)
        nos.server_config = servers
        if nos.exists():
            nos.remove()
        assert not nos.exists()

        #
        # run paths vs files
        #
        paths.collect_paths(filename="transfer", pathsname="transfer")
        #
        # create local check path and check that parquet file exists
        #
        ppath = Nos(paths.run_metadata.run_home).join("output")
        ppath = Nos(ppath).join("stores.parquet")
        assert Nos(ppath).exists()
        #
        # check that transfer happened
        #
        nos = Nos(tpath)
        config = paths.paths_manager.describer.get_config("transfer")
        servers = config.destinations
        nos.server_config = servers
        assert nos.exists()
