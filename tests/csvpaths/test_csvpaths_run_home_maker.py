import unittest
import os
from csvpath import CsvPaths
from csvpath.util.run_home_maker import RunHomeMaker
from csvpath.util.path_util import PathUtility as pathu
from csvpath.util.nos import Nos
from tests.csvpaths.builder import Builder

PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}test.csv"
PATHS = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}food.csvpaths"
PATH2 = (
    f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}test.csv"
)


class TestCsvPathsRunHome(unittest.TestCase):
    def test_run_home_template_1(self):
        paths = Builder().build()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.paths_manager.add_named_paths_from_file(name="food", file_path=PATHS)
        paths.file_manager.add_named_file(name="food", path=PATH)
        maker = RunHomeMaker(paths)
        run_dir = maker.get_run_dir(paths_name="food", file_name="food")
        assert run_dir is not None
        assert run_dir.startswith(paths.config.archive_path)
        parts = pathu.parts(run_dir)
        expected = (
            3
            if Nos(paths.config.get(section="results", name="archive")).backend
            == "local"
            else 5
        )
        assert len(parts) == expected
