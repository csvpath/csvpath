import unittest

from csvpath import CsvPaths
from csvpath.util.class_loader import ClassLoader


class TestCsvPathsExamplesOpenLineageVersions(unittest.TestCase):
    def test_csvpaths_openlineage_loading_files_v1(self) -> None:
        paths = CsvPaths()
        config = paths.config
        config.set(section="listeners", name="openlineage.version", value=1)
        lst = ClassLoader.load(
            "from csvpath.managers.integrations.ol.file_listener_ol import OpenLineageFileListener",
            [],
            {"config": config},
        )
        assert lst
        assert lst.__class__.__module__.find("v1")

        config.set(section="listeners", name="openlineage.version", value=2)
        lst = ClassLoader.load(
            "from csvpath.managers.integrations.ol.file_listener_ol import OpenLineageFileListener",
            [],
            {"config": config},
        )
        assert lst
        assert lst.__class__.__module__.find("v2")

    def test_csvpaths_openlineage_loading_paths_v1(self) -> None:
        paths = CsvPaths()
        config = paths.config
        config.set(section="listeners", name="openlineage.version", value=1)
        lst = ClassLoader.load(
            "from csvpath.managers.integrations.ol.paths_listener_ol import OpenLineagePathsListener",
            [],
            {"config": config},
        )
        assert lst
        assert lst.__class__.__module__.find("v1")

        config.set(section="listeners", name="openlineage.version", value=2)
        lst = ClassLoader.load(
            "from csvpath.managers.integrations.ol.paths_listener_ol import OpenLineagePathsListener",
            [],
            {"config": config},
        )
        assert lst
        assert lst.__class__.__module__.find("v2")

    def test_csvpaths_openlineage_loading_results_v1(self) -> None:
        paths = CsvPaths()
        config = paths.config
        config.set(section="listeners", name="openlineage.version", value=1)
        lst = ClassLoader.load(
            "from csvpath.managers.integrations.ol.results_listener_ol import OpenLineageResultsListener",
            [],
            {"config": config},
        )
        assert lst
        assert lst.__class__.__module__.find("v1")

        config.set(section="listeners", name="openlineage.version", value=2)
        lst = ClassLoader.load(
            "from csvpath.managers.integrations.ol.results_listener_ol import OpenLineageResultsListener",
            [],
            {"config": config},
        )
        assert lst
        assert lst.__class__.__module__.find("v2")

    def test_csvpaths_openlineage_loading_result_v1(self) -> None:
        paths = CsvPaths()
        config = paths.config
        config.set(section="listeners", name="openlineage.version", value=1)
        lst = ClassLoader.load(
            "from csvpath.managers.integrations.ol.result_listener_ol import OpenLineageResultListener",
            [],
            {"config": config},
        )
        assert lst
        assert lst.__class__.__module__.find("v1")

        config.set(section="listeners", name="openlineage.version", value=2)
        lst = ClassLoader.load(
            "from csvpath.managers.integrations.ol.result_listener_ol import OpenLineageResultListener",
            [],
            {"config": config},
        )
        assert lst
        assert lst.__class__.__module__.find("v2")

    def test_csvpaths_openlineage_loading_runs_v1(self) -> None:
        paths = CsvPaths()
        config = paths.config
        config.set(section="listeners", name="openlineage.version", value=1)
        lst = ClassLoader.load(
            "from csvpath.managers.integrations.ol.run_listener_ol import OpenLineageRunListener",
            [],
            {"config": config},
        )
        assert lst
        assert lst.__class__.__module__.find("v1")

        config.set(section="listeners", name="openlineage.version", value=2)
        lst = ClassLoader.load(
            "from csvpath.managers.integrations.ol.run_listener_ol import OpenLineageRunListener",
            [],
            {"config": config},
        )
        assert lst
        assert lst.__class__.__module__.find("v2")
