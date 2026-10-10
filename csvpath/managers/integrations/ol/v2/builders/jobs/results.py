import traceback

from openlineage.client.facet_v2 import (
    job_type_job,
    source_code_location_job,
    documentation_job,
)
from openlineage.client.event_v2 import Job

from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener
from csvpath.util.nos import Nos

from ..tokens import Tokens
from ...util.metadata_utility import MetadataUtility as meut
from ...util.name_utility import NameUtility as naut


class ResultsJobBuilder:
    RESULTS_JOB_TYPE = "VALIDATION"

    def __init__(self, *, listener: Listener) -> None:
        if listener is None:
            raise ValueError("Listener cannot be None")
        self.listener = listener

    def build(self, mdata: Metadata) -> Job:
        try:
            fs = {}
            fs["documentation"] = documentation_job.DocumentationJobFacet(
                description="Kicks off a run that validates one or more data items using a named-paths group"
            )
            fs["sourceCodeLocation"] = (
                source_code_location_job.SourceCodeLocationJobFacet(
                    type="CsvPath Framework", url=self._group_file_path(mdata)
                )
            )
            f = job_type_job.JobTypeJobFacet(
                processingType=meut.type_of_job(mdata),
                integration=Tokens.INTEGRATION,
                jobType=ResultsJobBuilder.RESULTS_JOB_TYPE,
            )
            fs["jobType"] = f

            ns, name = naut.namespace_and_name_2(
                config=self.listener.config,
                mdata=mdata,
                entity=mdata.named_results_name,
                eom="entity",
                job_type="run",
            )
            job = Job(namespace=ns, name=name, facets=fs)
            return job
        except Exception as e:
            print(traceback.format_exc())
            self.listener.config.logger.error(e)

    def _group_file_path(self, mdata: Metadata) -> str:
        paths = mdata.named_paths_name
        paths = naut.from_root_major_if(paths)
        root = self.listener.config.get(section="inputs", name="csvpaths")
        path = Nos(root).join(paths)
        path = Nos(path).join("group.csvpaths")
        #
        # marquez doesn't like non-uris
        #
        from pathlib import Path

        path = Path(path).resolve()
        path = path.as_uri()

        return path
