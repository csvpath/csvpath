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
        print(f"test_run_home_template_1: run_dir: {run_dir}")
        parts = pathu.parts(run_dir)
        assert len(parts) == 3

    def test_run_home_template_2(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.paths_manager.add_named_paths_from_file(name="food", file_path=PATHS)
        paths.file_manager.remove_named_file("food")
        paths.file_manager.add_named_file(name="food", path=PATH2)
        maker = RunHomeMaker(paths)
        run_dir = maker.get_run_dir(paths_name="food", file_name="food")
        # run_dir = maker.run_time_str("food")
        print(f"test_run_home_template_2: run_dir: {run_dir}")
        parts = pathu.parts(run_dir)
        dir_path = maker.results_dir_path(
            pathsname="food",
            filename="food",
            run_dir=run_dir,
            template=":1/:run_dir/:2",
        )
        print(f"test_run_home_template_2: dir_path: {dir_path}")
        assert dir_path == f"archive/food/test_resources/{parts[2]}/named_files"

    def test_run_home_template_3(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.paths_manager.add_named_paths_from_file(name="food", file_path=PATHS)
        paths.file_manager.remove_named_file("food")
        paths.file_manager.add_named_file(name="food", path=TREE1)
        paths.file_manager.add_named_file(name="food", path=TREE2)
        paths.file_manager.add_named_file(name="food", path=TREE3)
        maker = RunHomeMaker(paths)
        run_dir = maker.get_run_dir(paths_name="food", file_name="food")
        # run_dir = maker.run_time_str("food")
        print(f"test_run_home_template_3run_dir: {run_dir}")
        parts = pathu.parts(run_dir)
        dir_path = maker.results_dir_path(
            pathsname="food",
            filename="$food.files.:1",
            run_dir=run_dir,
            template=":0/:run_dir/:3",
        )
        print(f"test_run_home_template_3: dir_path: {dir_path}")
        assert dir_path == f"archive/food/tests/{parts[2]}/sub1"
