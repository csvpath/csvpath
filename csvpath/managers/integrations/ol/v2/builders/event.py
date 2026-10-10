from openlineage.client.event_v2 import RunEvent
from openlineage.client.event_v2 import Run, Job

from csvpath.managers.metadata import Metadata
from csvpath.managers.results.results_metadata import ResultsMetadata
from csvpath.managers.results.result_metadata import ResultMetadata
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.run.run_metadata import RunMetadata
from csvpath.managers.listener import Listener

from .events.result import ResultEventBuilder
from .events.results import ResultsEventBuilder
from .events.file import FileEventBuilder
from .events.paths import PathsEventBuilder


class EventBuilder:
    PRODUCER = "https://github.com/csvpath/csvpath"
    INTEGRATION = "CSVPATH"

    def __init__(self, *, listener: Listener) -> None:
        if listener is None:
            raise ValueError("Listener cannot be None")
        self.listener = listener

    def build(
        self, mdata: Metadata, job: Job = None, run: Run = None
    ) -> list[RunEvent]:
        if isinstance(mdata, ResultsMetadata):
            return ResultsEventBuilder(listener=self.listener).build(mdata, job, run)
        elif isinstance(mdata, ResultMetadata):
            return ResultEventBuilder(listener=self.listener).build(mdata, job, run)
        elif isinstance(mdata, PathsMetadata):
            return PathsEventBuilder(listener=self.listener).build(mdata, job)
        elif isinstance(mdata, FileMetadata):
            return FileEventBuilder(listener=self.listener).build(mdata, job)
        elif isinstance(mdata, RunMetadata):
            return None
