from openlineage.client.event_v2 import Job

from csvpath.managers.metadata import Metadata
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.results.result_metadata import ResultMetadata
from csvpath.managers.results.results_metadata import ResultsMetadata
from csvpath.managers.run.run_metadata import RunMetadata
from csvpath.managers.listener import Listener

from .jobs.file import FileJobBuilder
from .jobs.paths import PathsJobBuilder
from .jobs.results import ResultsJobBuilder
from .jobs.result import ResultJobBuilder


class JobException(Exception):
    pass


class JobBuilder:
    def __init__(self, *, listener: Listener) -> None:
        if listener is None:
            raise ValueError("Listener cannot be None")
        self.listener = listener

    def build(self, mdata: Metadata) -> Job:
        if isinstance(mdata, FileMetadata):
            return FileJobBuilder(listener=self.listener).build(mdata)
        if isinstance(mdata, PathsMetadata):
            return PathsJobBuilder(listener=self.listener).build(mdata)
        if isinstance(mdata, ResultMetadata):
            return ResultJobBuilder(listener=self.listener).build(mdata)
        if isinstance(mdata, ResultsMetadata):
            return ResultsJobBuilder(listener=self.listener).build(mdata)
        if isinstance(mdata, RunMetadata):
            return None
        raise JobException(f"Unknown metadata: {mdata}")
