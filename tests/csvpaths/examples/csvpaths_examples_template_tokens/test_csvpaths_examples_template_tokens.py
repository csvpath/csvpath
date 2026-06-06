import unittest
import os
from datetime import datetime, timezone
from tests.csvpaths.builder import Builder

PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}food.csv"


class TestCsvPathsTemplateTokens(unittest.TestCase):
    def test_csvpaths_template_tokens_1(self):
        paths = Builder().build()
        paths.file_manager.remove_named_file("food")
        ref = paths.file_manager.add_named_file(
            name="food", path=PATH, template=":month/:year/:filename"
        )
        assert ref
        filepath = paths.file_manager.get_named_file("food")
        print(f"filepath: {filepath}")
        dt = datetime.now(timezone.utc)
        assert filepath.find(f"{dt.month}/{dt.year}/food.csv") > -1

    def test_csvpaths_template_tokens_2(self):
        paths = Builder().build()
        paths.file_manager.remove_named_file("food")
        ref = paths.file_manager.add_named_file(
            name="food", path=PATH, template=":month_name/:hour_24/:filename"
        )
        assert ref
        filepath = paths.file_manager.get_named_file("food")
        print(f"filepath: {filepath}")
        dt = datetime.now(timezone.utc)
        chk = f"{dt.strftime('%B')}/{dt.strftime('%H')}/food.csv"
        print(f"chk: {chk}")
        assert filepath.find(chk) > -1

    def test_csvpaths_template_tokens_3(self):
        paths = Builder().build()
        paths.file_manager.remove_named_file("food")
        ref = paths.file_manager.add_named_file(
            name="food", path=PATH, template=":month_name/:hour_24/:filename"
        )
        assert ref
        filepath = paths.file_manager.get_named_file("food")
        print(f"filepath: {filepath}")
        dt = datetime.now(timezone.utc)
        chk = f"{dt.strftime('%B')}/{dt.strftime('%H')}/food.csv"
        print(f"chk: {chk}")
        assert filepath.find(chk) > -1

        paths.paths_manager.remove_named_paths("food")
        group = {
            "food": [
                """~id:first~$[*][
                    print("identity: $.csvpath.identity in $.csvpath.named_paths_name ")
                    print("$.csvpath.day_of_week, $.csvpath.day of $.csvpath.month ($.csvpath.month_of_year), $.csvpath.year")
                ]""",
            ]
        }
        paths.paths_manager.set_named_paths(group)

        ref = paths.collect_paths(
            filename="food", pathsname="food", template=":2/:day/:month/:run_dir"
        )
        results = paths.results_manager.get_named_results(ref)
        assert results is not None
        assert len(results) == 1
        result = results[0]
        assert result.run_dir
        chk = f"test_resources/{dt.day}/{dt.month}/"
        print(f"chk: {chk}, run_dir: {result.run_dir}")
        assert result.run_dir.find(chk) > -1
