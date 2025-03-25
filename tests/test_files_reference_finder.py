import unittest
import os
import datetime
from datetime import timedelta, timezone
from csvpath import CsvPaths
from csvpath.util.references.reference_parser import ReferenceParser
from csvpath.util.references.files_reference_finder import FilesReferenceFinder
from csvpath.util.path_util import PathUtility as pathu
from csvpath.util.references.ref_utils import ReferenceUtility as refu

FILES = {
    "food": f"tests{os.sep}test_resources{os.sep}named_files{os.sep}food.csv",
    "test": f"tests{os.sep}test_resources{os.sep}named_files{os.sep}test.csv",
}
NAMED_PATHS_DIR = f"tests{os.sep}test_resources{os.sep}named_paths{os.sep}"


class TestFilesReferenceFinder(unittest.TestCase):
    def setup(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        paths.file_manager.set_named_files(FILES)
        paths.fast_forward_paths(filename="food", pathsname="food")
        return paths

    def test_files_ref_finder_reference_mani(self):
        paths = self.setup()
        #
        ref = "$food.files.today:first"
        finder = FilesReferenceFinder(paths, name=ref)
        assert finder.name == ref
        assert isinstance(finder._ref, ReferenceParser)
        assert finder._ref.root_major == "food"
        assert finder._ref.name_one == "today:first"
        assert finder.manifest is not None
        assert len(finder.manifest) >= 1
        assert "file" in finder.manifest[0]
        assert finder.manifest[0]["type"] == "csv"

    def test_files_ref_finder_fingerprint(self):
        paths = self.setup()
        ref = "$food.files.today:first"
        finder = FilesReferenceFinder(paths, name=ref)
        assert finder.manifest is not None
        assert len(finder.manifest) >= 1
        f = finder.manifest[0]["fingerprint"]
        #
        ref = f"$food.files.{f}"
        finder = FilesReferenceFinder(paths, name=ref)
        file = finder._path_for_fingerprint_if()
        assert file is not None
        assert file == finder.manifest[0]["file"]

    def test_files_ref_finder_index(self):
        print("init csvpaths")
        paths = self.setup()
        print("starting ref finding")
        ref = "$food.files.today:first"
        finder = FilesReferenceFinder(paths, name=ref)
        assert finder.manifest is not None
        assert len(finder.manifest) >= 1
        f = finder.manifest[0]["fingerprint"]
        #
        ref = "$food.files.:0"
        finder = FilesReferenceFinder(paths, name=ref)
        file = finder._path_for_bare_index_if()
        assert file is not None
        assert len(file) == 1
        assert pathu.equal(
            file[0],
            f"inputs{os.sep}named_files{os.sep}food{os.sep}food.csv{os.sep}{f}.csv",
            True,
        )

    def test_files_ref_finder_for_day(self):
        paths = self.setup()
        paths.file_manager.add_named_file(
            name="food", path=f"tests{os.sep}test_resources{os.sep}people.csv"
        )
        paths.file_manager.add_named_file(
            name="food", path=f"tests{os.sep}test_resources{os.sep}people2.csv"
        )
        #
        #
        #
        ref = "$food.files.today:first"
        finder = FilesReferenceFinder(paths, name=ref)
        assert finder.manifest is not None
        assert len(finder.manifest) >= 3
        f = finder.manifest[0]["fingerprint"]

        file = finder._path_for_day_if()
        assert file is not None
        assert len(file) == 1
        assert pathu.equal(file[0], f"inputs/named_files/food/food.csv/{f}.csv", True)
        #
        #
        #
        ref = "$food.files.today:last"
        finder = FilesReferenceFinder(paths, name=ref)
        assert finder.manifest is not None
        assert len(finder.manifest) >= 3
        f = finder.manifest[len(finder.manifest) - 1]["fingerprint"]

        file = finder._path_for_day_if()
        print(f"testfrf: file: {file}")
        assert file is not None
        assert len(file) == 1
        assert pathu.equal(
            file[0], f"inputs/named_files/food/people2.csv/{f}.csv", True
        )

    def test_files_ref_finder_pointer(self):
        paths = self.setup()
        ref = "$food.files.today:first"
        finder = FilesReferenceFinder(paths, name=ref)
        n = finder._ref.name_one
        p = refu.pointer(n, "last")
        assert p == "first"

    def test_files_ref_finder_not_pointer(self):
        paths = self.setup()
        ref = "$food.files.today:first"
        finder = FilesReferenceFinder(paths, name=ref)
        n = finder.ref.name_one
        p = refu.not_pointer(n)
        assert p == "today"

    def test_files_ref_finder_complete_date_string(self):
        paths = self.setup()
        ref = "$food.files.2025-02-26_01-01"
        finder = FilesReferenceFinder(paths, name=ref)
        s = finder.ref.name_one
        s = finder._complete_date_string(s)
        assert s == "2025-02-26_01-01-00"
        dat = datetime.datetime.strptime(s, "%Y-%m-%d_%H-%M-%S")
        assert isinstance(dat, datetime.datetime)

        ref = "$food.files.2025-02"
        finder = FilesReferenceFinder(paths, name=ref)
        s = finder.ref.name_one
        s = finder._complete_date_string(s)
        assert s == "2025-02-01_00-00-00"
        dat = datetime.datetime.strptime(s, "%Y-%m-%d_%H-%M-%S")
        assert isinstance(dat, datetime.datetime)

        ref = "$food.files.2025-"
        finder = FilesReferenceFinder(paths, name=ref)
        s = finder.ref.name_one
        s = finder._complete_date_string(s)
        assert s == "2025-01-01_00-00-00"
        dat = datetime.datetime.strptime(s, "%Y-%m-%d_%H-%M-%S")
        assert isinstance(dat, datetime.datetime)

    def test_files_ref_finder_date_if(self):
        paths = self.setup()
        ref = "$food.files.2025-02-26_01-01"
        finder = FilesReferenceFinder(paths, name=ref)

        two_days_ago = datetime.datetime.today().astimezone(timezone.utc) - timedelta(
            days=2
        )
        yesterday = datetime.datetime.today().astimezone(timezone.utc) - timedelta(
            days=1
        )
        today = datetime.datetime.today().astimezone(timezone.utc)
        tomorrow = datetime.datetime.today().astimezone(timezone.utc) + timedelta(
            days=1
        )

        lst = [two_days_ago, yesterday, today, tomorrow]
        pointer = "before"
        i = finder._find_in_dates(lst, today, pointer)
        assert i == [0, 1]

        pointer = "after"
        i = finder._find_in_dates(lst, today, pointer)
        assert i == [3]
