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
        ret = None
        if isinstance(mdata, FileMetadata):
            ret = FileJobBuilder(listener=self.listener).build(mdata)
        elif isinstance(mdata, PathsMetadata):
            ret = PathsJobBuilder(listener=self.listener).build(mdata)
        elif isinstance(mdata, ResultMetadata):
            ret = ResultJobBuilder(listener=self.listener).build(mdata)
        elif isinstance(mdata, ResultsMetadata):
            ret = ResultsJobBuilder(listener=self.listener).build(mdata)
        elif isinstance(mdata, RunMetadata):
            ret = None
        else:
            raise JobException(f"Unknown metadata: {mdata}")
        return ret
