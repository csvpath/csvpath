import unittest
import os
from uuid import uuid4
from tests.csvpaths.builder import Builder

CSV = os.path.join(
    "tests",
    "csvpaths",
    "examples",
    "csvpaths_examples_ref_for_uuid",
    "csvs",
    "March-2024.csv",
)


class TestCsvPathsExamplesRefForUuid(unittest.TestCase):
    def test_ref_for_uuid_1(self):
        paths = Builder().build()
        paths.config.set(
            section="errors", name="csvpaths", value="raise, collect, print"
        )
        paths.config.set(
            section="errors", name="csvpath", value="raise, collect, print"
        )
        #
        # clear and add files
        #
        if paths.file_manager.has_named_file("utr"):
            paths.file_manager.remove_named_file("utr")
        assert not paths.file_manager.has_named_file("utr")
        uuid = str(uuid4())
        ref = paths.file_manager.add_named_file(
            name="utr", path=CSV, registration_uuid=uuid
        )
        r2 = paths.file_manager.get_reference_for_uuid("utr", uuid)
        assert ref is not None
        assert ref == r2
