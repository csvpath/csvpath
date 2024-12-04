import os
import json

from .job import JobBuilder
from openlineage.client.facet_v2 import JobFacet, parent_run
from openlineage.client.event_v2 import Job, Run, RunEvent, RunState

from ..metadata import Metadata
from ..results.results_metadata import ResultsMetadata
from ..results.result_metadata import ResultMetadata
from ..paths.paths_metadata import PathsMetadata
from ..files.file_metadata import FileMetadata
from ..run.run_metadata import RunMetadata


class RunBuilder:
    def build(self, mdata: Metadata) -> Run:
        if isinstance(mdata, ResultsMetadata):
            return self.build_results_run(mdata)
        elif isinstance(mdata, ResultMetadata):
            return self.build_result_run(mdata)
        elif isinstance(mdata, PathsMetadata):
            return self.build_paths_run(mdata)
        elif isinstance(mdata, FileMetadata):
            return self.build_file_run(mdata)
        elif isinstance(mdata, RunMetadata):
            # do we want to support this one, if it comes?
            return None

    def build_file_run(self, mdata: Metadata):
        run = Run(runId=mdata.uuid_string, facets={})
        return run

    def build_paths_run(self, mdata: Metadata):
        run = Run(runId=mdata.uuid_string, facets={})
        return run

    def build_result_run(self, mdata: Metadata):
        facets = {}
        if mdata.named_paths_uuid is None:
            raise Exception(
                "runbuilder result run: mdata.named_paths_uuid  cannot be None"
            )
        else:
            parent_run_facet = parent_run.ParentRunFacet(
                run=parent_run.Run(runId=mdata.named_paths_uuid_string),
                job=parent_run.Job(
                    namespace=mdata.archive_name,
                    name=f"Group:{mdata.named_results_name}",
                ),
            )
            facets["parent"] = parent_run_facet
        return Run(runId=mdata.uuid_string, facets=facets)

    def build_results_run(self, mdata: Metadata):
        facets = {}
        #
        # get the named paths uuid
        #
        puuid = None
        mp = f"{mdata.named_paths_root}{os.sep}{mdata.named_paths_name}/manifest.json"
        print(f"\n>>>>>> mpis: {mp}")
        with open(mp, "r", encoding="utf-8") as file:
            d = json.load(file)
            puuid = d[len(d) - 1]["uuid"]
        print(f">>>>>> puuid: {puuid} is: Load:{mdata.named_results_name}")
        parent_run_facet = parent_run.ParentRunFacet(
            run=parent_run.Run(runId=puuid),
            job=parent_run.Job(
                namespace=mdata.archive_name,
                name=f"Load:{mdata.named_results_name}",
            ),
        )
        facets["parent"] = parent_run_facet
        return Run(runId=mdata.uuid_string, facets=facets)
