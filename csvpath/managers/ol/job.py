from ..metadata import Metadata
from ..paths.paths_metadata import PathsMetadata
from ..files.file_metadata import FileMetadata
from ..results.result_metadata import ResultMetadata
from ..results.results_metadata import ResultsMetadata
from ..run.run_metadata import RunMetadata
from openlineage.client.facet_v2 import JobFacet
from openlineage.client.facet_v2 import job_type_job
from openlineage.client.run import Job

from openlineage.client.facet_v2 import documentation_job, source_code_location_job


class JobException(Exception):
    pass


class JobBuilder:
    # https://openlineage.io/docs/spec/facets/job-facets/job-type
    # They must be set after the `set_producer(_PRODUCER)`
    # otherwise the `JobTypeJobFacet._producer` will be set with the default value
    JOB_TYPE_PATH = job_type_job.JobTypeJobFacet(
        jobType="Path", integration="CSVPATH", processingType="DATALOAD"
    )
    JOB_TYPE_RESULT = job_type_job.JobTypeJobFacet(
        jobType="Result", integration="CSVPATH", processingType="BATCH"
    )
    JOB_TYPE_RESULTS = job_type_job.JobTypeJobFacet(
        jobType="Results", integration="CSVPATH", processingType="BATCH"
    )
    JOB_TYPE_FILE = job_type_job.JobTypeJobFacet(
        jobType="File", integration="CSVPATH", processingType="BATCH"
    )

    def build(self, mdata: Metadata):
        if isinstance(mdata, FileMetadata):
            return self.build_file_job(mdata)
        if isinstance(mdata, PathsMetadata):
            return self.build_paths_job(mdata)
        if isinstance(mdata, ResultMetadata):
            return self.build_result_job(mdata)
        if isinstance(mdata, ResultsMetadata):
            return self.build_results_job(mdata)
        if isinstance(mdata, RunMetadata):
            return None
        raise JobException(f"Unknown metadata: {mdata}")

    def build_file_job(self, mdata: Metadata):
        try:
            job = self._base_job(mdata)
            # fs = job.facets
            # why does adding this line blow up OL?
            # fs["jobType"] = JobBuilder.FILE_TYPE_PATH
            job.name = mdata.named_file_name
            return job
        except Exception as e:
            print(f"error in jobbuilder: {e}")

    def build_paths_job(self, mdata: Metadata):
        try:
            job = self._base_job(mdata)
            fs = job.facets
            fs[
                "sourceCodeLocation"
            ] = source_code_location_job.SourceCodeLocationJobFacet(
                type="CsvPath", url=mdata.named_paths_file
            )
            fs["jobType"] = JobBuilder.JOB_TYPE_PATH
            job.name = f"X: {mdata.named_paths_name}"
            return job
        except Exception as e:
            print(f"error in jobbuilder: {e}")

    def build_result_job(self, mdata: Metadata):
        try:
            job = self._base_job(mdata)
            fs = job.facets
            fs["documentation"] = documentation_job.DocumentationJobFacet(
                description=mdata.instance_identity
            )
            fs["jobType"] = JobBuilder.JOB_TYPE_RESULT
            job.name = mdata.named_results_name
            return job
        except Exception as e:
            print(f"error in jobbuilder: {e}")

    def build_results_job(self, mdata: Metadata):
        try:
            job = self._base_job(mdata)
            fs = job.facets
            fs[
                "sourceCodeLocation"
            ] = source_code_location_job.SourceCodeLocationJobFacet(
                type="CsvPath", url=f"{mdata.named_paths_name}/group.csvpaths"
            )
            fs["jobType"] = JobBuilder.JOB_TYPE_RESULTS
            job.name = f"Group: {mdata.named_results_name}"
            return job
        except Exception as e:
            print(f"error in jobbuilder: {e}")

    def _base_job(self, mdata: Metadata):
        try:
            print(f"creating job for {mdata}")
            fs = {}
            fs["documentation"] = documentation_job.DocumentationJobFacet(
                description="no description"
            )
            return Job(namespace=mdata.archive_name, name="", facets=fs)
        except Exception as e:
            print(f"error in jobbuilder: {e}")
