import traceback

from openlineage.client.facet_v2 import (
    job_type_job,
    documentation_job,
)
from openlineage.client.event_v2 import Job

from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener

from ...util.metadata_utility import MetadataUtility as meut
from ...util.name_utility import NameUtility as naut


class ResultJobBuilder:
    def __init__(self, *, listener: Listener) -> None:
        if listener is None:
            raise ValueError("Listener cannot be None")
        self.listener = listener

    def build(self, mdata: Metadata) -> Job:
        try:
            fs = {}
            fs["documentation"] = documentation_job.DocumentationJobFacet(
                description="An execution of an individual validation within a run of a named-paths group"
            )
            f = job_type_job.JobTypeJobFacet(
                processingType=meut.type_of_job(mdata),
                integration="CSVPATH",
                jobType="VALIDATION",
            )
            fs["jobType"] = f
            ns, name = naut.namespace_and_name_2(
                config=self.listener.config,
                mdata=mdata,
                instance=mdata.instance_identity,
                entity=mdata.named_results_name,
                eom="entity",
                job_type="run_instance",
            )
            job = Job(namespace=ns, name=name, facets=fs)
            return job
        except Exception as e:
            print(traceback.format_exc())
            self.listener.config.logger.exception(e)
