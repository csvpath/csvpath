import os
import json

from openlineage.client.facet_v2 import JobFacet, parent_run, error_message_run
from openlineage.client.event_v2 import Job, Run, RunEvent, RunState

from csvpath.managers.metadata import Metadata
from csvpath.managers.results.results_metadata import ResultsMetadata
from csvpath.managers.results.result_metadata import ResultMetadata
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.run.run_metadata import RunMetadata
from .job import JobBuilder


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
        if mdata.named_paths_uuid is not None:
            parent_run_facet = parent_run.ParentRunFacet(
                run=parent_run.Run(runId=mdata.named_paths_uuid_string),
                job=parent_run.Job(
                    namespace=mdata.archive_name,
                    name=f"Group:{mdata.named_results_name}",
                ),
            )
            facets["parent"] = parent_run_facet
        else:
            print(
                "The OpenLineage run event builder cannot find the named_paths_uuid value in Metadata. If this is not testing please log a bug."
            )

        epath = f"{mdata.instance_home}/errors.json"
        if os.path.exists(epath):
            with open(epath, "r", encoding="utf-8") as file:
                j = json.load(file)
                for e in j:
                    msg = f"{e['error']} at {e['line_count']}\nSource: {e['source']}\nFile: {e['filename']}\nSee errors.json for more details"
                    facets["errorMessage"] = error_message_run.ErrorMessageRunFacet(
                        message=msg,
                        programmingLanguage="CsvPath and/or Python",
                        stackTrace=e["trace"],
                    )

        return Run(runId=mdata.uuid_string, facets=facets)

    def build_results_run(self, mdata: Metadata):
        facets = {}
        #
        # get the named paths uuid
        #
        puuid = None
        npn = mdata.named_paths_name
        if npn.startswith("$"):
            npn = npn[1 : npn.find(".")]
        #
        # npn should also == mdata.named_results_name but let's go with
        # the reference prefix because it is more likely to reflect the
        # named-paths dir
        #
        m = npn.find("#")
        if m > -1:
            npn = npn[0:m]
        mp = f"{mdata.named_paths_root}{os.sep}{npn}/manifest.json"
        with open(mp, "r", encoding="utf-8") as file:
            d = json.load(file)
            puuid = d[len(d) - 1]["uuid"]
        parent_run_facet = parent_run.ParentRunFacet(
            run=parent_run.Run(runId=puuid),
            job=parent_run.Job(
                namespace=mdata.archive_name,
                name=f"Load:{mdata.named_results_name}",
            ),
        )
        facets["parent"] = parent_run_facet
        return Run(runId=mdata.uuid_string, facets=facets)
