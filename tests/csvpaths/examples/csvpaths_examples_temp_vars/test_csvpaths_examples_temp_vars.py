import unittest
import os
from tests.csvpaths.builder import Builder

PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}food.csv"


class TestCsvPathsTempVars(unittest.TestCase):
    def test_csvpaths_temp_vars_1(self):

        paths = Builder().build()
        paths.file_manager.remove_named_file("food")
        paths.file_manager.add_named_file(name="food", path=PATH)

        paths.paths_manager.remove_named_paths("food")
        group = {
            "food": [
                """~id:second~$[*][
                    @line.tmp = line_number()
                    yes() -> @a = "a"
                    yes() -> @b = "b"
                ]""",
                """~id:first~$[*][
                    @line = line_number()
                    yes() -> @a = "a"
                    yes() -> @b.tmp = "b"
                ]""",
            ]
        }
        paths.paths_manager.set_named_paths(group)

        paths.collect_paths(filename="food", pathsname="food")
        results = paths.results_manager.get_named_results("food")
        assert len(results) == 2
        result = results[0]
        variables = result.csvpath.variables
        assert "line" not in variables
        assert variables["a"] == "a"
        assert variables["b"] == "b"

        result = results[1]
        variables = result.csvpath.variables
        assert variables["a"] == "a"
        assert "b" not in variables
        assert "line" in variables
