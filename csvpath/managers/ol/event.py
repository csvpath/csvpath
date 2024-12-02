from datetime import datetime

from openlineage.client.facet_v2 import JobFacet
from openlineage.client.event_v2 import Dataset
from openlineage.client.run import Job, Run, RunEvent, RunState
from openlineage.client.run import InputDataset, OutputDataset

from ..metadata import Metadata
from ..results.results_metadata import ResultsMetadata
from ..results.result_metadata import ResultMetadata
from ..paths.paths_metadata import PathsMetadata
from ..files.file_metadata import FileMetadata
from ..run.run_metadata import RunMetadata

from .job import JobBuilder
from .run import RunBuilder
from .run_state import RunStateBuilder


class EventBuilder:
    PRODUCER = "https://github.com/csvpath/csvpath"

    def build(
        self, mdata, job=None, run=None, facets=None, inputs=None, outputs=None
    ) -> RunEvent:
        if isinstance(mdata, ResultsMetadata):
            return self._build_results_event(mdata, job, run, facets, inputs)
        elif isinstance(mdata, ResultMetadata):
            return self._build_result_event(mdata, job, run, facets, inputs, outputs)
        elif isinstance(mdata, PathsMetadata):
            return self._build_paths_event(mdata, job, facets)
        elif isinstance(mdata, FileMetadata):
            return self._build_file_event(mdata, job, inputs)
        elif isinstance(mdata, RunMetadata):
            # do we want to support this one, if it comes?
            return None

    #
    # event for a single csvpath
    #
    def _build_result_event(self, mdata: Metadata, job, run, facets, inputs, outputs):
        runstate = RunStateBuilder().build(mdata)

        file = Dataset(namespace=mdata.archive_name, name=mdata.input_data_file)
        path = Dataset(namespace=mdata.archive_name, name=mdata.named_results_name)
        inputs = [file, path]

        outputs = []
        if mdata.file_fingerprints is not None:
            for fingerprint in mdata.file_fingerprints:
                o = Dataset(namespace=mdata.archive_name, name=fingerprint)
                outputs.append(o)
        job = job or JobBuilder().build(mdata)
        run = run or RunBuilder().build(mdata)
        if mdata.time is None:
            mdata.set_time()
        event = RunEvent(
            eventType=runstate,
            eventTime=mdata.time_string,
            run=run,
            job=job,
            inputs=inputs,
            outputs=outputs,
            producer=EventBuilder.PRODUCER,
        )
        return event

    def _build_results_event(self, mdata: Metadata, job, run, facets, inputs):
        file = InputDataset(namespace=mdata.archive_name, name=mdata.named_file_name)
        path = Dataset(namespace=mdata.archive_name, name=mdata.named_results_name)
        inputs = [file, path]
        runstate = RunStateBuilder().build(mdata)
        job = job or JobBuilder().build(mdata)
        run = run or RunBuilder().build(mdata)
        event = RunEvent(
            eventType=runstate,
            eventTime=mdata.time_string,
            run=run,
            job=job,
            inputs=inputs,
            outputs=[],
            producer=EventBuilder.PRODUCER,
        )
        return event

    def _build_paths_event(self, mdata, job, facets):
        runstate = RunStateBuilder().build(mdata)
        ds = OutputDataset(namespace=mdata.archive_name, name=mdata.named_paths_name)
        outputs = [ds]
        job = job or JobBuilder().build(mdata)
        run = RunBuilder().build(mdata)
        event = RunEvent(
            eventType=runstate,
            eventTime=datetime.now().isoformat(),
            run=run,
            job=job,
            inputs=[],
            outputs=outputs,
            producer=EventBuilder.PRODUCER,
        )
        return event

    def _build_file_event(self, mdata, job, inputs):
        runstate = RunStateBuilder().build(mdata)
        ds = OutputDataset(namespace=mdata.archive_name, name=mdata.named_file_name)
        outputs = [ds]
        job = job or JobBuilder().build(mdata)
        run = RunBuilder().build(mdata)
        event = RunEvent(
            eventType=runstate,
            eventTime=datetime.now().isoformat(),
            run=run,
            job=job,
            inputs=[],
            outputs=outputs,
            producer=EventBuilder.PRODUCER,
        )
        return event
