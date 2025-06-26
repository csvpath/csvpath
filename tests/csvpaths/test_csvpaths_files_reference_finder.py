import unittest
import os
import datetime
from datetime import timedelta, timezone
from csvpath import CsvPaths
from csvpath.util.references.reference_parser import ReferenceParser

from csvpath.util.references.files_reference_finder_2 import (
    FilesReferenceFinder2 as FilesReferenceFinder,
)
from csvpath.util.references.tools.date_completer import DateCompleter
from csvpath.util.path_util import PathUtility as pathu
from csvpath.util.date_util import DateUtility as daut
from csvpath.util.references.ref_utils import ReferenceUtility as refu
from tests.csvpaths.builder import Builder

FOOD = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}food.csv"
FOOD_PATHS = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}food.csvpaths"
FILES = {
    "food": FOOD,
    "test": f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}test.csv",
}
NAMED_PATHS_DIR = (
    f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}"
)


class TestFilesCsvPathsReferenceFinder(unittest.TestCase):
    def setup(self):
        paths = Builder().build()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.paths_manager.add_named_paths(name="food", from_file=FOOD_PATHS)
        #
        #
        # replaceme! commented out for testing to speed up s3. remove the line above.
        #
        # paths.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        paths.file_manager.set_named_files(FILES)
        paths.fast_forward_paths(filename="food", pathsname="food")
        return paths

    def test_b_files_ref_finder_mani_path_to_ref(self) -> None:
        refstr = refu.results_manifest_path_to_reference(
            archive_name="archive",
            manipath=f"archive{os.sep}many{os.sep}test_resources{os.sep}2025-03-27_01-16-05{os.sep}named_files{os.sep}many_two{os.sep}manifest.json",
            is_instance=True,
        )
        ref = ReferenceParser(refstr)
        assert ref.root_major == "many"
        assert ref.name_one == f"test_resources{os.sep}2025-03-27_01-16-05"
        assert ref.name_three == "many_two"
        #
        # not an instance
        #
        refstr = refu.results_manifest_path_to_reference(
            archive_name="archive",
            manipath=f"archive{os.sep}many{os.sep}test_resources{os.sep}2025-03-27_01-16-05{os.sep}manifest.json",
            is_instance=False,
        )
        ref = ReferenceParser(refstr)
        assert ref.root_major == "many"
        assert ref.name_one == f"test_resources{os.sep}2025-03-27_01-16-05"
        assert ref.name_three is None

        #
        # instance with sub
        #
        refstr = refu.results_manifest_path_to_reference(
            archive_name="archive",
            manipath=f"archive{os.sep}many{os.sep}test_resources{os.sep}2025-03-27_01-16-05{os.sep}sub{os.sep}myinstance{os.sep}manifest.json",
            is_instance=True,
        )
        ref = ReferenceParser(refstr)
        assert ref.root_major == "many"
        assert ref.name_one == f"test_resources{os.sep}2025-03-27_01-16-05"
        assert ref.name_three == "myinstance"

    def test_files_ref_finder_reference_mani(self):
        paths = self.setup()
        #
        ref = "$food.files.:today:first"
        finder = FilesReferenceFinder(paths, reference=ref)
        assert finder.ref.reference == ref
        assert isinstance(finder._ref, ReferenceParser)
        assert finder._ref.root_major == "food"
        assert finder._ref.name_one_tokens == ["today", "first"]
        assert finder.manifest is not None
        assert len(finder.manifest) >= 1
        assert "file" in finder.manifest[0]
        assert finder.manifest[0]["type"] == "csv"

    def test_b_files_ref_finder_fingerprint(self):
        paths = self.setup()
        ref = "$food.files.:today:first"
        finder = FilesReferenceFinder(paths, reference=ref)
        assert finder.manifest is not None
        assert len(finder.manifest) >= 1
        f = finder.manifest[0]["fingerprint"]
        ref = f"$food.files.{f}"
        print(f"reference is: {ref}")
        results = FilesReferenceFinder(paths, reference=ref).query()
        assert results is not None
        assert results.files is not None
        assert len(results.files) == 1
        assert results.files[0] == finder.manifest[0]["file"]

    def test_b_files_ref_finder_complete_date_string(self):
        paths = self.setup()
        ref = "$food.files.2025-02-26_01-01"
        finder = FilesReferenceFinder(paths, reference=ref)
        s = finder.ref.name_one
        # s = finder._complete_date_string(s)
        s = DateCompleter.get(s)
        assert s == "2025-02-26_01-01-00"
        dat = datetime.datetime.strptime(s, "%Y-%m-%d_%H-%M-%S")
        assert isinstance(dat, datetime.datetime)

        ref = "$food.files.2025-02"
        finder = FilesReferenceFinder(paths, reference=ref)
        s = finder.ref.name_one
        # s = finder._complete_date_string(s)
        s = DateCompleter.get(s)
        assert s == "2025-02-01_00-00-00"
        dat = datetime.datetime.strptime(s, "%Y-%m-%d_%H-%M-%S")
        assert isinstance(dat, datetime.datetime)

        ref = "$food.files.2025-"
        finder = FilesReferenceFinder(paths, reference=ref)
        s = finder.ref.name_one
        # s = finder._complete_date_string(s)
        s = DateCompleter.get(s)
        assert s == "2025-01-01_00-00-00"
        dat = datetime.datetime.strptime(s, "%Y-%m-%d_%H-%M-%S")
        assert isinstance(dat, datetime.datetime)

    def test_b_files_ref_finder_date_if(self):
        self.setup()
        # in the rewrite of files ref finder we ended up with a tool that doesn't fit this test
        # however, the tool mainly relies on daut so we can test that level instead.
        # ref = "$food.files.2025-02-26_01-01"
        # finder = FilesReferenceFinder(paths, reference=ref)
        #
        today = datetime.datetime.today().astimezone(timezone.utc)
        two_days_ago = today - timedelta(days=2)
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        lst = [two_days_ago, yesterday, today, tomorrow]

        before = daut.all_before(today, lst)
        before = daut.dates_from_list(before)
        assert len(before) == 2
        assert before == [two_days_ago, yesterday]

        after = daut.all_after(today, lst)
        after = daut.dates_from_list(after)
        assert len(after) == 1
        assert after == [tomorrow]
