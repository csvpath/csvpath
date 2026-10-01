from openlineage.client.facet_v2 import job_type_job, documentation_job
from openlineage.client.event_v2 import Job

from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener

from ...util.metadata_utility import MetadataUtility as meut
from ..tokens import Tokens


class FileJobBuilder:
    FILE_JOB_TYPE = "REGISTER"
    JOB_NAME = "register"

    def __init__(self, *, listener: Listener) -> None:
        if listener is None:
            raise ValueError("Listener cannot be None")
        self.listener = listener

    def build(self, mdata: Metadata) -> Job:
        try:
            facets = {}
            facets["documentation"] = documentation_job.DocumentationJobFacet(
                description="""Stages a source file for validation and upgrading. This job imports the file, registers it, and makes it available for further processing."""
            )
            f = job_type_job.JobTypeJobFacet(
                processingType=meut.type_of_job(mdata),
                integration=Tokens.INTEGRATION,
                jobType=FileJobBuilder.FILE_JOB_TYPE,
            )
            facets["jobType"] = f
            return Job(
                namespace=Tokens.JOB_NAMESPACE,
                name=f"{FileJobBuilder.JOB_NAME}:{mdata.named_file_name}",
                facets=facets,
            )
        except Exception as e:
            self.listener.config.logger.error(e)
