import unittest
import tempfile
import os
import shutil
import pyarrow.parquet as pq
from csvpath import CsvPaths
from csvpath.managers.paths.paths_manager import PathsManager
from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos

PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}parquet.csvpaths"
PATH2 = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}parquet2.csvpaths"


class TestCsvPathsExamplesPathsParquet(unittest.TestCase):
    def test_csvpaths_parquet_1(self) -> None:
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        #
        # setup paths
        #
        paths.paths_manager.add_named_paths_from_file(
            name="annual_units", file_path=PATH
        )
        paths.file_manager.add_named_file(
            name="autos",
            path=os.path.join(
                "tests",
                "csvpaths",
                "test_resources",
                "Automobiles_Annual_Imports_and_Exports_Port_Authority_of_NY.csv",
            ),
        )
        ref = paths.collect_paths(filename="autos", pathsname="annual_units")
        results = paths.results_manager.get_named_results(ref)
        assert results
        assert len(results) == 1
        result = results[0]
        rundir = result.run_dir
        path = Nos(rundir).join("autos")
        path = Nos(path).join("autos.parquet")
        path = Nos(path)
        assert path.exists()

        #
        # parquet doesn't like our backend urls so copy to a local temp
        #
        path = Nos(paths.run_metadata.run_home)
        path = path.join("autos")
        pname = Nos(path).join("autos.parquet")
        temp_path = None
        with DataFileReader(path=pname, mode="rb") as src, tempfile.NamedTemporaryFile(
            mode="wb", delete=False
        ) as dst:
            shutil.copyfileobj(src.source, dst)
            dst.flush()
            temp_path = dst.name
        try:
            p = pq.ParquetFile(temp_path)
            table = p.read(columns=["year", "type", "volume"])
            assert table
            chunked_array = table.column("volume")
            assert len(chunked_array) == 2
            assert int(chunked_array[1]) == 302441
        finally:
            os.unlink(temp_path)

    def test_csvpaths_parquet_2(self) -> None:
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        #
        # setup paths
        #
        paths.paths_manager.add_named_paths_from_file(
            name="annual_units", file_path=PATH2
        )
        paths.file_manager.add_named_file(
            name="autos",
            path=os.path.join(
                "tests",
                "csvpaths",
                "test_resources",
                "Automobiles_Annual_Imports_and_Exports_Port_Authority_of_NY.csv",
            ),
        )
        ref = paths.collect_paths(filename="autos", pathsname="annual_units")
        results = paths.results_manager.get_named_results(ref)
        assert results
        assert len(results) == 1
        result = results[0]
        rundir = result.run_dir
        path = Nos(rundir).join("autos")
        path = Nos(path).join("autos.parquet")
        path = Nos(path)
        assert path.exists()

        rundir = result.run_dir
        path = Nos(rundir).join("autos")
        path = Nos(path).join("years.parquet")
        path = Nos(path)
        assert path.exists()

        #
        # parquet doesn't like our backend urls so copy to a local temp
        #
        path = Nos(paths.run_metadata.run_home)
        path = path.join("autos")
        pname = Nos(path).join("autos.parquet")
        """
        with DataFileReader(path=pname, mode="rb") as src, tempfile.NamedTemporaryFile(
            mode="wb"
        ) as dst:
            shutil.copyfileobj(src.source, dst)
            dst.flush()
            p = pq.ParquetFile(dst.name)
            table = p.read(columns=["year", "type", "volume"])
            assert table
            chunked_array = table.column("volume")
            assert len(chunked_array) == 32
            assert int(chunked_array[1]) == 302441
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
            table = p.read(columns=["year", "type", "volume"])
            assert table
            chunked_array = table.column("volume")
            assert len(chunked_array) == 32
            assert int(chunked_array[1]) == 302441
        finally:
            os.unlink(temp_path)

        #
        # parquet doesn't like our backend urls so copy to a local temp
        #
        path = Nos(paths.run_metadata.run_home)
        path = path.join("autos")
        pname = Nos(path).join("years.parquet")
        temp_path = None
        with DataFileReader(path=pname, mode="rb") as src, tempfile.NamedTemporaryFile(
            mode="wb", delete=False
        ) as dst:
            shutil.copyfileobj(src.source, dst)
            dst.flush()
            temp_path = dst.name
        try:
            p = pq.ParquetFile(temp_path)
            table = p.read(columns=["year"])
            assert table
            chunked_array = table.column("year")
            assert len(chunked_array) == 6
            assert int(chunked_array[2]) == 2009
        finally:
            os.unlink(temp_path)
