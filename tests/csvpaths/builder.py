from csvpath import CsvPaths
from tests.csvpaths.kit.tracking_file_manager import TrackingFileManager
from tests.csvpaths.kit.tracking_paths_manager import TrackingPathsManager


class Builder:
    def build(self) -> CsvPaths:
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpaths", "raise, print")
        paths.config.add_to_config("errors", "csvpath", "raise, print")
        #
        # swap in tracking paths and files managers
        #
        paths.file_manager = TrackingFileManager(csvpaths=paths, mgr=paths.file_manager)
        paths.paths_manager = TrackingPathsManager(
            csvpaths=paths, mgr=paths.paths_manager
        )
        #
        # put any custom stuff here
        #
        paths.config.set(section="listeners", name="groups", value="default,otlp")

        #
        # end custom
        #
        return paths
