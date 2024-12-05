from datetime import datetime
import os
import json

from openlineage.client.facet_v2 import JobFacet, schema_dataset
from openlineage.client.event_v2 import Dataset, RunEvent
from openlineage.client.event_v2 import Job, Run, RunState
from openlineage.client.event_v2 import InputDataset, OutputDataset

# from openlineage.client import set_producer

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
    ) -> list[RunEvent]:
        if isinstance(mdata, ResultsMetadata):
            return self._build_results_event(mdata, job, run, facets, inputs)
        elif isinstance(mdata, ResultMetadata):
            return self._build_result_event(mdata, job, run, facets, inputs, outputs)
        elif isinstance(mdata, PathsMetadata):
            return self._build_paths_event(mdata, job, facets)
        elif isinstance(mdata, FileMetadata):
            return self._build_file_event(mdata, job, facets)
        elif isinstance(mdata, RunMetadata):
            # do we want to support this one, if it comes?
            return None

    #
    # event for a single csvpath
    #
    def _build_result_event(self, mdata: Metadata, job, run, facets, inputs, outputs):
        # runstate = RunStateBuilder().build(mdata)

        file = Dataset(namespace=mdata.archive_name, name=mdata.input_data_file)
        manifest = Dataset(
            namespace=mdata.archive_name,
            name=f"Group:{mdata.named_results_name}/manifest.json",
        )
        path = Dataset(namespace=mdata.archive_name, name=mdata.named_results_name)
        inputs = [file, path, manifest]
        #
        # there are 3 types of outputs
        #  - 6 standard files: data.csv, vars.json, errors.json, etc.
        #  - manifest.json
        #  - 0 or more transfers
        #
        outputs = []
        if mdata.file_fingerprints is not None:
            for fingerprint in mdata.file_fingerprints:
                o = Dataset(
                    namespace=mdata.archive_name,
                    name=f"{mdata.instance_identity}/{fingerprint}",
                )
                outputs.append(o)
        # manifest
        outmani = Dataset(
            namespace=mdata.archive_name,
            name=f"{mdata.instance_identity}/manifest.json",
        )
        outputs.append(outmani)
        # transfers
        tpaths = mdata.transfers
        if tpaths is not None:
            for t in tpaths:
                o = Dataset(
                    namespace=mdata.archive_name,
                    name=f"{t[3]}",
                )
                outputs.append(o)

        job = job or JobBuilder().build(mdata)
        run = run or RunBuilder().build(mdata)
        if mdata.time is None:
            mdata.set_time()
        start = RunEvent(
            eventType=RunState.START,
            eventTime=mdata.time_string,
            run=run,
            job=job,
            inputs=inputs,
            outputs=outputs,
            producer=EventBuilder.PRODUCER,
        )
        complete = RunEvent(
            eventType=RunState.COMPLETE,
            eventTime=mdata.time_string,
            run=run,
            job=job,
            inputs=inputs,
            outputs=outputs,
            producer=EventBuilder.PRODUCER,
        )
        return [start, complete]

    """
    def get_identities_facet(self, mdata):
        mp = f"{mdata.base_path}{os.sep}{mdata.named_paths_root}{os.sep}{mdata.named_paths_name}/manifest.json"
        j = []
        with open(mp, "r", encoding="utf-8") as file:
            j = json.load(file)
        d = j[len(j)-1]
        ps = d["named_paths"]
        fields=[]
        for p in d:
            f = schema_dataset.SchemaDatasetFacetFields(
                name=p, type="CsvPath", description=""
            )
            fields.append(f)
        csvpaths = self.dataset(
            f"{mdata.archive_name}/{mdata.named_paths_name}",
            schema_dataset.SchemaDatasetFacet(fields=fields),
            mdata.archive_name
        )
        return csvpaths

    def dummy_facets(self):
        print(">>> creating dataset data #{i}" )
        user_history = self.dataset(
            "archive",
            schema_dataset.SchemaDatasetFacet(
                fields=[
                    schema_dataset.SchemaDatasetFacetFields(
                        name="id", type="BIGINT", description="the user id"
                    ),
                    schema_dataset.SchemaDatasetFacetFields(
                        name="email_domain", type="VARCHAR", description="the user id"
                    ),
                    schema_dataset.SchemaDatasetFacetFields(
                        name="status", type="BIGINT", description="the user id"
                    ),
                ]
            ),
            "archive"
        )
        return user_history
    """

    def _build_results_event(self, mdata: Metadata, job, run, facets, inputs):
        file = InputDataset(
            namespace=mdata.archive_name, name=f"{mdata.named_file_name}"
        )  # , inputFacets=inputfacets
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
