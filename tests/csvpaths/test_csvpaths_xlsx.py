import unittest
import os
from csvpath import CsvPath
from tests.csvpaths.builder import Builder

FILES = {
    "energy": f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}xlsx{os.sep}2023-reported-energy-and-water-metrics.xlsx",
    "primary": f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}xlsx{os.sep}Table_1.1_Primary_Energy_Overview.xlsx",
}
NAMED_PATHS_DIR = (
    f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}xlsx{os.sep}named_paths"
)
PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}Book1.xlsx"


class TestCsvPathsXlsx(unittest.TestCase):
    def test_csvpaths_xlsx_primary_1(self):
        paths = Builder().build()
        paths.file_manager.set_named_files(FILES)
        paths.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        paths.collect_paths(filename="primary", pathsname="primary")
        pathresults = paths.results_manager.get_named_results("primary")
        results = pathresults[0]
        valid = paths.results_manager.is_valid("primary")
        # set for no-fail
        assert valid
        # increase rejects most of the lines
        assert len(results) == 22

    def test_csvpaths_bytes_written_1(self):
        #
        # currently bytes written only works for local files because FileInfo only
        # handles local files.
        #
        paths = Builder().build()
        paths.file_manager.set_named_files(FILES)
        paths.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        paths.collect_paths(filename="energy", pathsname="bytes")
        assert paths.results_manager.is_valid("bytes")

    def test_csvpaths_xlsx_sheets_1(self):

        lines1 = CsvPath().parse(f"""${PATH}#world[*][#0=="a"]""").collect()
        assert len(lines1) == 1
        print(f"lines1: {lines1}")

        lines2 = CsvPath().parse(f"""${PATH}#hello[*][#0=="my"]""").collect()
        assert len(lines2) == 1
        print(f"lines2: {lines2}")

        assert lines1 != lines2

        paths = Builder().build()
        paths.file_manager.remove_named_file("excel")
        paths.file_manager.add_named_file(name="excel", path=PATH)

        paths.paths_manager.remove_named_paths("excel")
        group = {
            "excel": [
                """~id:second~$[*][
                    #0=="my"
                    print("$.csvpath.identity: $.csvpath.line_number: $.csvpath.count_matches")
                ]""",
                """~id:first~$[*][
                    #0=="a"
                    print("$.csvpath.identity: $.csvpath.line_number: $.csvpath.count_matches")
                ]""",
            ]
        }
        paths.paths_manager.set_named_paths(group)

        # ==============================
        # do the 1st sheet "hello"
        #

        paths.collect_paths(filename="$excel#hello.files.:last", pathsname="excel")
        results = paths.results_manager.get_named_results("excel")
        print(f"results: {results}")
        result = results[0]
        print(f"result: {len(result)}")
        for _ in result.lines.next():
            print(f"result: {_}")
        assert len(result) == 1
        result = results[1]
        print(f"result: {len(result)}")
        for _ in result.lines.next():
            print(f"result: {_}")
        assert len(result) == 0

        # ==============================
        # do the 2nd sheet "world"
        #

        paths.collect_paths(filename="$excel#world.files.:last", pathsname="excel")
        results = paths.results_manager.get_named_results("excel")
        print(f"results: {results}")
        result = results[0]
        print(f"result: {len(result)}")
        for _ in result.lines.next():
            print(f"result: {_}")
        assert len(result) == 0
        result = results[1]
        print(f"result: {len(result)}")
        for _ in result.lines.next():
            print(f"result: {_}")
        assert len(result) == 1
