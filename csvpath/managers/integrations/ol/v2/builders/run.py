from openlineage.client.event_v2 import Run

from csvpath.managers.metadata import Metadata
from csvpath.managers.results.results_metadata import ResultsMetadata
from csvpath.managers.results.result_metadata import ResultMetadata
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.run.run_metadata import RunMetadata
from csvpath.managers.listener import Listener

from .runs.file import FileRunBuilder
from .runs.paths import PathsRunBuilder
from .runs.result import ResultRunBuilder
from .runs.results import ResultsRunBuilder


class RunBuilder:
    def __init__(self, *, listener: Listener) -> None:
        if listener is None:
            raise ValueError("Listener cannot be None")
        self.listener = listener

    def build(self, mdata: Metadata) -> Run:
        if isinstance(mdata, ResultsMetadata):
            return ResultsRunBuilder(listener=self.listener).build(mdata)
        elif isinstance(mdata, ResultMetadata):
            return ResultRunBuilder(listener=self.listener).build(mdata)
        elif isinstance(mdata, PathsMetadata):
            return PathsRunBuilder(listener=self.listener).build(mdata)
        elif isinstance(mdata, FileMetadata):
            return FileRunBuilder(listener=self.listener).build(mdata)
        elif isinstance(mdata, RunMetadata):
            return None
