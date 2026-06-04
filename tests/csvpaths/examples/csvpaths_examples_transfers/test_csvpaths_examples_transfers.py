import unittest
import os

from csvpath.util.nos import Nos

from tests.csvpaths.builder import Builder

CSV = os.path.join(
    "tests",
    "csvpaths",
    "examples",
    "csvpaths_examples_transfers",
    "csvs",
    "March-2024.csv",
)
PATH = os.path.join(
    "tests", "csvpaths", "examples", "csvpaths_examples_transfers", "definition.json"
)


class TestCsvPathsExamplesTransfers(unittest.TestCase):
    def test_new_transfers_1(self):
        paths = Builder().build()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.config.set(section="sftp", name="username", value="python")
        paths.config.set(section="sftp", name="password", value="hangzhou")
        #
        # clear and add files
        #
        if paths.file_manager.has_named_file("transfer"):
            paths.file_manager.remove_named_file("transfer")
        assert not paths.file_manager.has_named_file("transfer")
        paths.file_manager.add_named_file(name="transfer", path=CSV)
        assert paths.file_manager.has_named_file("transfer")

        #
        # clear and add paths
        #
        if paths.paths_manager.has_named_paths("validations"):
            paths.paths_manager.remove_named_paths("validations")
        assert not paths.paths_manager.has_named_paths("validations")
        paths.paths_manager.add_named_paths_from_json(PATH)
        #
        # run paths vs files
        #
        paths.collect_paths(filename="transfer", pathsname="validations")
        #
        # check that transfer happened
        #
        transfers = paths.config.get(section="results", name="transfers")
        print(f"testxy: transfers: {transfers}")
        nos = Nos(transfers)
        assert Nos(f"{transfers}{nos.sep}output{nos.sep}is{nos.sep}valid.txt").exists()
        assert Nos(f"{transfers}{nos.sep}vars{nos.sep}vars.json").exists()
        assert Nos(f"{transfers}{nos.sep}data.csv").exists()
        assert Nos(f"{transfers}{nos.sep}source.csv").exists()
        assert Nos(f"{transfers}{nos.sep}done.txt").exists()
        #
        # check one sftp happened
        #
        server = paths.config.get(section="sftp", name="server")
        port = paths.config.get(section="sftp", name="port")
        tpath = f"sftp://{server}:{port}/print_reports.txt"
        assert Nos(tpath).exists()
