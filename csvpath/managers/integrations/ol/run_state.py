from openlineage.client.facet_v2 import JobFacet
from openlineage.client.event_v2 import Job, Run, RunEvent, RunState

from csvpath.managers.metadata import Metadata
from csvpath.managers.results.results_metadata import ResultsMetadata
from csvpath.managers.results.result_metadata import ResultMetadata
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.managers.files.file_metadata import FileMetadata


class RunStateBuilder:
    def build(self, mdata):
        runstate = RunState.START
        if isinstance(mdata, ResultsMetadata):
            # do we have all the good things?
            if (
                mdata.time_completed is not None
                and mdata.all_completed
                and mdata.all_valid
                and mdata.error_count == 0
                and mdata.all_expected_files
            ):
                runstate = RunState.COMPLETE
            elif (
                mdata.time_completed is not None
                and not mdata.all_completed
                or not mdata.all_expected_files
            ):
                runstate = RunState.ABORT
            elif mdata.time_completed is not None:
                runstate = RunState.FAIL
            else:
                runstate = RunState.START
        elif isinstance(mdata, ResultMetadata):
            if (
                mdata.valid
                and mdata.completed
                and mdata.error_count == 0
                and mdata.files_expected
            ):
                runstate = RunState.COMPLETE
            elif not mdata.completed or not mdata.files_expected:
                runstate = RunState.ABORT
            else:
                runstate = RunState.FAIL
        elif isinstance(mdata, PathsMetadata):
            runstate = RunState.COMPLETE
        elif isinstance(mdata, FileMetadata):
            runstate = RunState.COMPLETE
        #
        # experiment!
        #
        runstate = RunState.START
        #
        #
        #
        return runstate
