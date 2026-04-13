import unittest
import os

from csvpath import CsvPaths
from csvpath.managers.test_listener import TestListener


class TestCsvPathsExamplesDynamicListeners(unittest.TestCase):
    def test_dynamic_listeners_1(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "collect, raise, print")
        paths.config.add_to_config("errors", "csvpaths", "collect, raise, print")

        if paths.file_manager.has_named_file("hooks"):
            paths.file_manager.remove_named_file("hooks")

        if paths.paths_manager.has_named_paths("hooks"):
            paths.paths_manager.remove_named_paths("hooks")

        runs = TestListener()
        results = TestListener()
        result = TestListener()
        groups = TestListener()
        files = TestListener()
        errors = TestListener()

        paths.paths_manager.registrar.add_internal_listener(groups)
        paths.file_manager.registrar.add_internal_listener(files)
        paths.results_manager.dynamic_result_listeners.append(result)
        paths.results_manager.dynamic_results_listeners.append(results)
        paths.results_manager.dynamic_run_listeners.append(runs)
        paths.dynamic_csvpath_error_listeners.append(errors)

        paths.file_manager.add_named_file(
            name="hooks",
            path=f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_webhooks{os.sep}csvs{os.sep}hooks.csv",
        )

        assert files.mine is not None
        assert files.mine.named_file_name == "hooks"

        paths.paths_manager.add_named_paths_from_json(
            file_path=f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_webhooks{os.sep}csvpaths{os.sep}hooks.json"
        )

        assert groups.mine is not None
        assert groups.mine.named_paths_name == "hooks"

        paths.fast_forward_paths(pathsname="hooks", filename="hooks")

        assert errors.mine is not None
        assert errors.mine.scan_count > -1

        assert runs.mine is not None
        assert runs.mine.run_uuid is not None

        assert results.mine is not None
        assert results.mine.all_completed is not None

        assert result.mine is not None
        assert result.mine.actual_data_file is not None
