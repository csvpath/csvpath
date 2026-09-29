from openlineage.client.facet_v2 import (
    job_type_job,
    documentation_job,
)
from openlineage.client.event_v2 import Job

from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener
from csvpath.util.nos import Nos

from ...util.metadata_utility import MetadataUtility as meut
from ...util.protocol_utility import ProtocolUtility as prut
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
            #
            # end exp
            #
            # if we have meta.json available (after run is done) we can grab the
            # csvpath for the instance job. we could go after it from the results's
            # manifest or the group.csvpaths. tho atm not sure when it is available
            # in results either and parsing the group file would be a small pain.
            # after seems fine.
            #
            """
            qp = Nos(mdata.instance_home).join("meta.json")
            if Nos(qp).exists():
                q = ""
                with DataFileReader(qp) as reader:
                    m = json.load(reader.source)
                    q = f"{m['runtime_data']['scan_part']}{m['runtime_data']['match_part']}"
                fs["sql"] = sql_job.SQLJobFacet(query=q)
            """
            ns = prut.update_protocol_if(
                config=self.listener.config, mdata=mdata, root=mdata.archive_path
            )
            name = Nos(mdata.run_home).join(mdata.instance_identity)
            name = naut.trim_namespace_if(namespace=ns, path=name)
            job = Job(namespace=ns, name=name, facets=fs)
            return job
        except Exception as e:
            import traceback

            print(traceback.format_exc())
            self.listener.config.logger.exception(e)
