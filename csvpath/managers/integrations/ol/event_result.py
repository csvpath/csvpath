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
from csvpath.managers.results.result_metadata import ResultMetadata

from .job import JobBuilder
from .run import RunBuilder
from .run_state import RunStateBuilder


class ResultEventBuilder:
    PRODUCER = "https://github.com/csvpath/csvpath"

    #
    # event for a single csvpath
    #
    def build(self, mdata: Metadata, job, run, facets, inputs, outputs):
        # runstate = RunStateBuilder().build(mdata)
        #
        # if we are source mode preceding we're going to replace the original file
        # with the preceding instance identity/data.csv
        #
        file = Dataset(namespace=mdata.archive_name, name=mdata.input_data_file)
        preceding = mdata.preceding_instance_identity and mdata.source_mode_preceding
        preceding = preceding or mdata.by_line
        if preceding is True and mdata.preceding_instance_identity:
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

                if exists and fingerprint == "errors.json":
                    fields = []
                    afield = schema_dataset.SchemaDatasetFacetFields(
                        name="error count", type=f"{mdata.error_count}", description=""
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
            producer=ResultEventBuilder.PRODUCER,
        )
        complete = RunEvent(
            eventType=RunState.COMPLETE,
            eventTime=mdata.time_string,
            run=run,
            job=job,
            inputs=inputs,
            outputs=outputs,
            producer=ResultEventBuilder.PRODUCER,
        )
        return [start, complete]
