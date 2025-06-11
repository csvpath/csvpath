import unittest
import os
from csvpath import CsvPaths
from csvpath.util.run_home_maker import RunHomeMaker
from csvpath.util.path_util import PathUtility as pathu

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"
PATH2 = f"tests{os.sep}test_resources{os.sep}named_files{os.sep}test.csv"

TREE1 = f"tests{os.sep}test_resources{os.sep}trees{os.sep}test-1.csv"
TREE2 = f"tests{os.sep}test_resources{os.sep}trees{os.sep}sub1{os.sep}test-2.csv"
TREE3 = f"tests{os.sep}test_resources{os.sep}trees{os.sep}test-3.csv"


PATHS = f"tests{os.sep}test_resources{os.sep}named_paths{os.sep}food.csvpaths"


class TestRunHome(unittest.TestCase):
    def test_run_home_template_1(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.paths_manager.add_named_paths_from_file(name="food", file_path=PATHS)
        paths.file_manager.add_named_file(name="food", path=PATH)
        maker = RunHomeMaker(paths)
        run_dir = maker.get_run_dir(paths_name="food", file_name="food")
        assert run_dir is not None
        assert run_dir.startswith(paths.config.archive_path)
        parts = pathu.parts(run_dir)
        assert len(parts) == 3
