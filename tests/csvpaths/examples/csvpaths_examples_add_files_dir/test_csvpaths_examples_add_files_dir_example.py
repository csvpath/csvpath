import unittest
import pytest
import os
from csvpath import CsvPaths
from os import environ


class TestCsvPathsExamplesAddFilesDirExample(unittest.TestCase):
    def test_add_files_dir_example_1(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        print(f"paths: {paths.config.configpath}")
        #
        # this add has blown up on finding a . extension. turns out the dot is in the
        # name, not the extension. the success is simply not blowing up.
        #
        # tests/examples/add_files_dir/assets
        #
        # after noodling, for now, we'll leave it as-is. may want to reconsider at some
        # point. in references we expect _ and make the switch automatically. I don't love
        # that solution either, but either way references cannot do the .s.
        #
        dirname = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_add_files_dir{os.sep}assets"
        with pytest.raises(ValueError):
            paths.file_manager.add_named_files_from_dir(
                name=None, dirname=dirname, template=None, recurse=True
            )
