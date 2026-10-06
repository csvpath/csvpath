from openlineage.client.facet_v2 import (
    job_type_job,
    documentation_job,
)
from openlineage.client.event_v2 import Job

from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener
from csvpath.util.file_readers import DataFileReader

from ..tokens import Tokens
from ...util.metadata_utility import MetadataUtility as meut
from ...util.name_utility import NameUtility as naut
from ...facets.source import SourceFacet


class PathsJobBuilder:
    PATHS_JOB_TYPE = "LOAD"
    JOB_NAME = "load group"

    def __init__(self, *, listener: Listener) -> None:
        if listener is None:
            raise ValueError("Listener cannot be None")
        self.listener = listener

    def build(self, mdata: Metadata) -> Job:
        try:
            q = ""
            with DataFileReader(mdata.group_file_path) as reader:
                q = reader.read()
            facets = {}
            facets["source"] = SourceFacet(source=q, fingerprint=mdata.fingerprint)
            facets["documentation"] = documentation_job.DocumentationJobFacet(
                description="""Loads a validation and upgrading group. This job assembles the csvpaths into a group.csvpaths file and makes it ready to run."""
            )
            f = job_type_job.JobTypeJobFacet(
                processingType=meut.type_of_job(mdata),
                integration=Tokens.INTEGRATION,
                jobType=PathsJobBuilder.PATHS_JOB_TYPE,
            )
            facets["jobType"] = f

            ns, name = naut.namespace_and_name_2(
                config=self.listener.config,
                mdata=mdata,
                eom="entity",
                job_type="load",
                entity=mdata.named_paths_name,
            )
            return Job(
                namespace=ns,
                name=name,
                facets=facets,
            )
        except Exception as e:
            import traceback

            print(traceback.format_exc())
            self.listener.config.logger.error(e)
