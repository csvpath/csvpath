from ..metadata import Metadata
from ..paths.paths_metadata import PathsMetadata
from ..files.file_metadata import FileMetadata
from openlineage.client.facet_v2 import JobFacet
from openlineage.client.facet_v2 import job_type_job
from openlineage.client.run import Job

from openlineage.client.facet_v2 import documentation_job, source_code_location_job

class JobBuilder:
    # https://openlineage.io/docs/spec/facets/job-facets/job-type
    # They must be set after the `set_producer(_PRODUCER)`
    # otherwise the `JobTypeJobFacet._producer` will be set with the default value
    JOB_TYPE_NAMED_PATHS = job_type_job.JobTypeJobFacet(jobType="Group", integration="CSVPATH", processingType="BATCH")
    JOB_TYPE_PATH = job_type_job.JobTypeJobFacet(jobType="Path", integration="CSVPATH", processingType="BATCH")
    JOB_TYPE_FILE = job_type_job.JobTypeJobFacet(jobType="File", integration="CSVPATH", processingType="BATCH")

    def build(self, mdata:Metadata):
        try:
            print(f"creating job for {mdata}")
            fs = {}
            fs["documentation"] = documentation_job.DocumentationJobFacet(
                description="this is a test"
            )


            if isinstance(mdata, PathsMetadata):
                print(f"paths meetatdta found")
                fs["sourceCodeLocation"] = source_code_location_job.SourceCodeLocationJobFacet(
                    type="CsvPath",
                    url=mdata.named_paths_file
                )
                fs["jobType"] = JobBuilder.JOB_TYPE_PATH
            if isinstance(mdata, FileMetadata):
                print(f"file meetatdta found")
                fs["sourceCodeLocation"] = source_code_location_job.SourceCodeLocationJobFacet(
                    type="CsvPath",
                    url=mdata.file_path
                )
                fs["jobType"] = JobBuilder.JOB_TYPE_FILE


            #print(f"creating job facets with {fs}")
            #print(f"jobbuilder: mdata: {mdata}")
            name = None
            if hasattr(mdata, "named_results_name"):
                name=mdata.named_results_name
            elif hasattr(mdata, "named_file_name"):
                name=mdata.named_file_name
            else:
                name=mdata.named_paths_name
            return Job(namespace=mdata.archive_name, name=name, facets=fs)
        except Exception as e:
            print(f"error in jobbuilder: {e}")

