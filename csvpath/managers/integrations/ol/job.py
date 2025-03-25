import os
import json

from openlineage.client.facet_v2 import (
    JobFacet,
    job_type_job,
    schema_dataset,
    source_code_location_job,
    documentation_job,
    sql_job,
)
from openlineage.client.event_v2 import Job

from csvpath.managers.metadata import Metadata
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.results.result_metadata import ResultMetadata
from csvpath.managers.results.results_metadata import ResultsMetadata
from csvpath.managers.run.run_metadata import RunMetadata


class JobException(Exception):
    pass


class JobBuilder:
    JOB_TYPE_PATH = job_type_job.JobTypeJobFacet(
        jobType="COMMAND", integration="CSVPATH", processingType="LOAD"
    )
    JOB_TYPE_RESULT = job_type_job.JobTypeJobFacet(
        jobType="JOB", integration="CSVPATH", processingType="BATCH"
    )
    JOB_TYPE_RESULTS = job_type_job.JobTypeJobFacet(
        jobType="JOB", integration="CSVPATH", processingType="BATCH"
    )
    JOB_TYPE_FILE = job_type_job.JobTypeJobFacet(
        jobType="COMMAND", integration="CSVPATH", processingType="BATCH"
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
            facets = {}
            location = f"file:////{mdata.base_path}{os.sep}{mdata.file_path}"
            facets[
                "sourceCodeLocation"
            ] = source_code_location_job.SourceCodeLocationJobFacet(
                type="CsvPath", url=location, tag=f"{mdata.fingerprint}"
            )
            facets["documentation"] = documentation_job.DocumentationJobFacet(
                description="""Stages a source file for validation.
                This job imports the file, registers it, and makes it available
                for further processing."""
            )
            name = f"Stage:{mdata.named_file_name}"
            return Job(namespace=mdata.archive_name, name=name, facets=facets)
        except Exception as e:
            print(f"error in jobbuilder: {e}")

    def build_paths_job(self, mdata: Metadata):
        try:
            facets = {}
            location = f"file:////{mdata.base_path}{os.sep}{mdata.group_file_path}"
            facets[
                "sourceCodeLocation"
            ] = source_code_location_job.SourceCodeLocationJobFacet(
                type="CsvPath", url=location, tag=f"{mdata.fingerprint}"
            )
            #
            #
            #
            qp = f"{mdata.group_file_path}"
            q = ""
            with open(qp, "r", encoding="utf-8") as qf:
                q = qf.read()
            facets["sql"] = sql_job.SQLJobFacet(query=q)

            #
            #
            #
            facets["documentation"] = documentation_job.DocumentationJobFacet(
                description="""Loads a set of validation CsvPaths.
                This job assembles the csvpaths into a named-paths group file, registers
                them, and makes them ready for a run."""
            )
            name = f"Load:{mdata.named_paths_name}"
            return Job(namespace=mdata.archive_name, name=name, facets=facets)
        except Exception as e:
            print(f"error in jobbuilder: {e}")

    def build_result_job(self, mdata: Metadata):
        try:
            fs = {}
            fs["documentation"] = documentation_job.DocumentationJobFacet(
                description=mdata.instance_identity
            )
            #
            # exp: processing type seems to be fixed at batch, streaming, service.
            # the others seem to be open, but also aren't shown in the UI afaik.
            #
            f = job_type_job.JobTypeJobFacet(
                processingType="BATCH", integration="CSVPATH", jobType="VALIDATION"
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
            qp = f"{mdata.instance_home}{os.sep}meta.json"
            if os.path.exists(qp):
                q = ""
                with open(qp, "r", encoding="utf-8") as file:
                    m = json.load(file)
                    q = f"{m['runtime_data']['scan_part']}{m['runtime_data']['match_part']}"
                fs["sql"] = sql_job.SQLJobFacet(query=q)

            name = f"Instance:{mdata.instance_identity}"
            job = Job(namespace=mdata.archive_name, name=name, facets=fs)
            return job
        except Exception as e:
            print(f"error in jobbuilder: {e}")

    def build_results_job(self, mdata: Metadata):
        try:
            fs = {}
            fs["documentation"] = documentation_job.DocumentationJobFacet(
                description="Kicks off the individual csvpath jobs within this named-paths group"
            )
            fs[
                "sourceCodeLocation"
            ] = source_code_location_job.SourceCodeLocationJobFacet(
                type="CsvPath", url=f"{mdata.named_paths_name}/group.csvpaths"
            )
            name = f"Group:{mdata.named_results_name}"
            job = Job(namespace=mdata.archive_name, name=name, facets=fs)
            return job
        except Exception as e:
            print(f"error in jobbuilder: {e}")

    def _base_job(self, mdata: Metadata):
        try:
            fs = {}
            fs["documentation"] = documentation_job.DocumentationJobFacet(
                description="no description"
            )
            return Job(namespace=mdata.archive_name, name="", facets=fs)
        except Exception as e:
            print(f"error in jobbuilder: {e}")
