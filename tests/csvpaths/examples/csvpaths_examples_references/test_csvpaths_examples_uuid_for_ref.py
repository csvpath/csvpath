import unittest
import os
from csvpath import CsvPaths

FILE = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_references{os.sep}assets{os.sep}people.csv"


class TestCsvPathsExamplesUuidForRef(unittest.TestCase):
    def test_csvpaths_examples_uuid_for_ref(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")

        if paths.file_manager.has_named_file("people"):
            paths.file_manager.remove_named_file("people")
        ref = paths.file_manager.add_named_file(
            name="people",
            path=FILE,
        )
        print(f"refx: {ref}")
        assert ref is not None
        uuid = paths.file_manager.get_named_file_uuid(name=ref)
        print(f"uuidx: {uuid}")
        assert uuid is not None
        chk = paths.file_manager.get_reference_for_uuid("people", uuid)
        print(f"chkx: {chk}")
        assert chk is not None
        assert chk == ref

        paths.file_manager.remove_named_file("people")
