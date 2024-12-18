from datetime import datetime
import os
import json
from pathlib import Path
from openlineage.client.facet_v2 import (
    JobFacet,
    schema_dataset,
    output_statistics_output_dataset,
)
from openlineage.client.event_v2 import Dataset, RunEvent
from openlineage.client.event_v2 import Job, Run, RunState
from openlineage.client.event_v2 import InputDataset, OutputDataset

from csvpath.managers.metadata import Metadata
from csvpath.managers.results.results_metadata import ResultsMetadata
from csvpath.managers.results.result_metadata import ResultMetadata
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.run.run_metadata import RunMetadata

from .job import JobBuilder
from .run import RunBuilder
from .run_state import RunStateBuilder
from .event_result import ResultEventBuilder


class EventBuilder:
    PRODUCER = "https://github.com/csvpath/csvpath"

    def build(
        self, mdata, job=None, run=None, facets=None, inputs=None, outputs=None
    ) -> list[RunEvent]:
        if isinstance(mdata, ResultsMetadata):
            return self._build_results_event(mdata, job, run, facets, inputs)
        elif isinstance(mdata, ResultMetadata):
            return ResultEventBuilder().build(mdata, job, run, facets, inputs, outputs)
        elif isinstance(mdata, PathsMetadata):
            return self._build_paths_event(mdata, job, facets)
        elif isinstance(mdata, FileMetadata):
            return self._build_file_event(mdata, job, facets)
        elif isinstance(mdata, RunMetadata):
            # do we want to support this one, if it comes?
            return None

    def _build_results_event(self, mdata: Metadata, job, run, facets, inputs):
        file = InputDataset(
            namespace=mdata.archive_name, name=f"{mdata.named_file_name}"
        )
        path = InputDataset(
            namespace=mdata.archive_name, name=f"{mdata.named_paths_name}"
        )
        inputs = [file, path]
        runstate = RunStateBuilder().build(mdata)
        job = job or JobBuilder().build(mdata)
        run = run or RunBuilder().build(mdata)

        output = OutputDataset(
            namespace=mdata.archive_name,
            name=f"Group:{mdata.named_results_name}/manifest.json",
        )

        start = RunEvent(
            eventType=RunState.START,
            eventTime=mdata.time_string,
            run=run,
            job=job,
            inputs=inputs,
            outputs=[output],
            producer=EventBuilder.PRODUCER,
        )
        complete = RunEvent(
            eventType=runstate,
            eventTime=mdata.time_string,
            run=run,
            job=job,
            inputs=inputs,
            outputs=[output],
            producer=EventBuilder.PRODUCER,
        )
        return [start, complete]

    def _build_paths_event(self, mdata, job, facets):
        # runstate = RunStateBuilder().build(mdata)
        ds = OutputDataset(
            namespace=mdata.archive_name, name=f"{mdata.named_paths_name}"
        )
        ms = OutputDataset(
            namespace=mdata.archive_name, name=f"{mdata.named_paths_name}/manifest.json"
        )
        outputs = [ds, ms]
        job = job or JobBuilder().build(mdata)
        run = RunBuilder().build(mdata)
        start = RunEvent(
            eventType=RunState.START,
            eventTime=datetime.now().isoformat(),
            run=run,
            job=job,
            inputs=[],
            outputs=outputs,
            producer=EventBuilder.PRODUCER,
        )
        complete = RunEvent(
            eventType=RunState.COMPLETE,
            eventTime=datetime.now().isoformat(),
            run=run,
            job=job,
            inputs=[],
            outputs=outputs,
            producer=EventBuilder.PRODUCER,
        )
        return [start, complete]

    def _build_file_event(self, mdata, job, facets):
        # runstate = RunStateBuilder().build(mdata)
        ds = OutputDataset(
            namespace=mdata.archive_name, name=f"{mdata.named_file_name}"
        )
        ms = OutputDataset(
            namespace=mdata.archive_name, name=f"{mdata.named_file_name}/manifest.json"
        )
        outputs = [ds, ms]
        job = job or JobBuilder().build(mdata)
        run = RunBuilder().build(mdata)
        start = RunEvent(
            eventType=RunState.START,
            eventTime=datetime.now().isoformat(),
            run=run,
            job=job,
            inputs=[],
            outputs=outputs,
            producer=EventBuilder.PRODUCER,
        )
        complete = RunEvent(
            eventType=RunState.COMPLETE,
            eventTime=datetime.now().isoformat(),
            run=run,
            job=job,
            inputs=[],
            outputs=outputs,
            producer=EventBuilder.PRODUCER,
        )
        return [start, complete]
