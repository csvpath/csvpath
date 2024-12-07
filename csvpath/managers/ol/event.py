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
        #
        # if we are source mode preceding we're going to replace the original file
        # with the preceding instance identity/data.csv
        #
        file = Dataset(namespace=mdata.archive_name, name=mdata.input_data_file)
        if mdata.preceding_instance_identity and mdata.source_mode_preceding is True:
            file = Dataset(
                namespace=mdata.archive_name,
                name=f"{mdata.preceding_instance_identity}{os.sep}data.csv",
            )
        #
        # we were showing the manifest as an input. that's not 100% obvious and
        # it adds noise to the diagram. OL and the manifests or result of other
        # listeners are orthogonal
        #
        """
        manifest = Dataset(
            namespace=mdata.archive_name,
            name=f"Group:{mdata.named_results_name}/manifest.json",
        )
        """
        path = Dataset(namespace=mdata.archive_name, name=mdata.named_results_name)
        # inputs = [file, path, manifest]
        inputs = [file, path]
        #
        # there are 3 types of outputs
        #  - 6 standard files: data.csv, vars.json, errors.json, etc.
        #  - manifest.json
        #  - 0 or more transfers
        #
        outputs = []
        if mdata.file_fingerprints is not None:
            for fingerprint in mdata.file_fingerprints:
                # o = Dataset(
                #    namespace=mdata.archive_name,
                #    name=f"{mdata.instance_identity}/{fingerprint}",
                # )
                fs = {}
                #
                # experiment: add output statistics facet. not working yet
                # but doesn't break anything.
                #
                of = {}
                fp = f"{mdata.instance_home}{os.sep}{fingerprint}"
                exists = os.path.exists(fp)
                if exists:
                    size = Path(fp).stat().st_size
                    lines = 0
                    with open(fp, "r", encoding="utf-8") as file:
                        for line in file:
                            lines += 1
                    of[
                        "outputStatistics"
                    ] = output_statistics_output_dataset.OutputStatisticsOutputDatasetFacet(
                        rowCount=lines, size=size
                    )

                if exists and fingerprint == "vars.json":
                    fields = []
                    with open(fp, "r", encoding="utf-8") as file:
                        j = json.load(file)
                        for k, v in j.items():
                            if not k.startswith("_intx_"):
                                afield = schema_dataset.SchemaDatasetFacetFields(
                                    name=f"{k}", type=f"{type(v)}", description=""
                                )
                                fields.append(afield)
                    sdf = schema_dataset.SchemaDatasetFacet(fields=fields)
                    fs["schema"] = sdf

                if exists and fingerprint == "meta.json":
                    fields = []
                    with open(fp, "r", encoding="utf-8") as file:
                        j = json.load(file)
                        metadata = j["metadata"]
                        if metadata:
                            for k, v in metadata.items():
                                if k.endswith("mode"):
                                    afield = schema_dataset.SchemaDatasetFacetFields(
                                        name=f"{k}",
                                        type=f"{v}",
                                        description="Instance-level setting",
                                    )
                                    fields.append(afield)
                        runtime_data = j["runtime_data"]
                        if runtime_data:
                            _ = "Serial" if mdata.by_line else "Breadth-first"
                            afield = schema_dataset.SchemaDatasetFacetFields(
                                name="Data flow",
                                type=f"{_}",
                                description="Sequential or breadth-first run",
                            )
                            fields.append(afield)

                            if "count lines" in runtime_data:
                                afield = schema_dataset.SchemaDatasetFacetFields(
                                    name="count_lines",
                                    type=f"{runtime_data['count_lines']}",
                                    description="Number of lines",
                                )
                                fields.append(afield)
                            if "count matches" in runtime_data:
                                afield = schema_dataset.SchemaDatasetFacetFields(
                                    name="count_matches",
                                    type=f"{runtime_data['count_matches']}",
                                    description="Number of lines that matched",
                                )
                                fields.append(afield)
                            if "valid" in runtime_data:
                                afield = schema_dataset.SchemaDatasetFacetFields(
                                    name="valid",
                                    type=f"{runtime_data['valid']}",
                                    description="True if validation does not fail",
                                )
                                fields.append(afield)
                            if "stopped" in runtime_data:
                                afield = schema_dataset.SchemaDatasetFacetFields(
                                    name="stopped",
                                    type=f"{runtime_data['stopped']}",
                                    description="True if processing stopped early",
                                )
                                fields.append(afield)

                    sdf = schema_dataset.SchemaDatasetFacet(fields=fields)
                    fs["schema"] = sdf

                o = OutputDataset(
                    name=f"{mdata.instance_identity}/{fingerprint}",
                    namespace=mdata.archive_name,
                    facets=fs,
                    outputFacets=of,
                )

                #
                # end exp
                #
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
