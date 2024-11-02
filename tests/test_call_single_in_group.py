import unittest
from csvpath import CsvPaths


class TestFunctionsSingleInGroup(unittest.TestCase):
    def test_function_single_in_group(self):
        paths = CsvPaths()
        paths.file_manager.add_named_file(
            name="food", path="tests/test_resources/named_files/food.csv"
        )
        paths.paths_manager.add_named_paths_from_dir(
            directory="tests/test_resources/named_paths"
        )
        paths.fast_forward_paths(pathsname="many#many_two", filename="food")
        vars = paths.results_manager.get_variables("many#many_two")
        print(f"vars: {vars}")
        assert "two" in vars
        assert "one" not in vars
