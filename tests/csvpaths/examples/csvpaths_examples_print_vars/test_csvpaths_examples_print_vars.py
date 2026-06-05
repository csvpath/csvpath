import unittest
import os
from tests.csvpaths.builder import Builder
from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader

PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}food.csv"


class TestCsvPathsPrintVars(unittest.TestCase):
    def test_csvpaths_print_vars_1(self):
        paths = Builder().build()
        paths.file_manager.remove_named_file("food")
        paths.file_manager.add_named_file(name="food", path=PATH)

        paths.paths_manager.remove_named_paths("food")
        group = {
            "food": [
                """~id:second~$[*][
                    print("$.csvpath.identity")
                    print("$.csvpath.run_dir_name")
                    print("$.csvpath.run_dir")
                    print("$.csvpath.run_reference")
                ]""",
                """~id:first~$[*][
                    print("identity: $.csvpath.identity in $.csvpath.named_paths_name ")
                    print("$.csvpath.day_of_week, $.csvpath.day of $.csvpath.month_of_year")
                ]""",
            ]
        }
        paths.paths_manager.set_named_paths(group)

        paths.collect_paths(filename="food", pathsname="food")
        paths.results_manager.get_named_results("food")

        second = Nos(paths.last_run_dir).join("second")
        printouts = Nos(second).join("printouts.txt")
        text = None
        with DataFileReader(printouts) as file:
            text = file.read()
        assert text
        assert "run_dir" not in text
        assert "run_ref" not in text
        assert "identity" not in text

        first = Nos(paths.last_run_dir).join("first")
        printouts = Nos(first).join("printouts.txt")
        text = None
        with DataFileReader(printouts) as file:
            text = file.read()
        assert text
        assert "day_of_week" not in text
        assert "month_of_year" not in text
