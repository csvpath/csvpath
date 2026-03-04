import unittest
import tempfile
import os
import shutil
import pyarrow.parquet as pq

from csvpath import CsvPaths
from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader

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


class TestCsvPathsExamplesTransferSftp(unittest.TestCase):
    def test_transfer_parquet_1(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.config.set(section="sftp", name="server", value="192.168.1.152")
        paths.config.set(section="sftp", name="port", value="2022")
        paths.config.set(section="sftp", name="username", value="python")
        paths.config.set(section="sftp", name="password", value="hangzhou")
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
        # copy parquet file to temp local and check contents
        #
        path = Nos(paths.run_metadata.run_home).join("output")
        pname = Nos(path).join("stores.parquet")
        """
        with DataFileReader(path=pname, mode="rb") as src, tempfile.NamedTemporaryFile(
            mode="wb"
        ) as dst:
            shutil.copyfileobj(src.source, dst)
            dst.flush()
            p = pq.ParquetFile(dst.name)
            table = p.read(columns=["id", "day"])
            assert table
            chunked_array = table.column("day")
            assert len(chunked_array) == 3
            assert chunked_array[2].as_py().day == 21
        """
        temp_path = None
        with DataFileReader(path=pname, mode="rb") as src, tempfile.NamedTemporaryFile(
            mode="wb", delete=False
        ) as dst:
            shutil.copyfileobj(src.source, dst)
            dst.flush()
            temp_path = dst.name
        try:
            p = pq.ParquetFile(temp_path)
            table = p.read(columns=["id", "day"])
            assert table
            chunked_array = table.column("day")
            assert len(chunked_array) == 3
            assert chunked_array[2].as_py().day == 21
        finally:
            os.unlink(temp_path)

        #
        # check that transfer happened
        #
        tpath = "sftp://stores.parquet"
        assert Nos(tpath).exists()
