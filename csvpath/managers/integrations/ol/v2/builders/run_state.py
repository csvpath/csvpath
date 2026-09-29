from openlineage.client.event_v2 import RunState

from csvpath.managers.results.results_metadata import ResultsMetadata
from csvpath.managers.results.result_metadata import ResultMetadata
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.run.run_metadata import RunMetadata
from csvpath.managers.listener import Listener


class RunStateBuilder:
    def __init__(self, *, listener: Listener) -> None:
        if listener is None:
            raise ValueError("Listener cannot be None")
        self.listener = listener

    def build(self, mdata):
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        runstate = RunState.START
        #
        # a run
        #
        if isinstance(mdata, ResultsMetadata):
            if (
                mdata.time_completed is not None
                and mdata.all_completed
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
        #
        # a result
        #
        elif isinstance(mdata, ResultMetadata):
            if mdata.completed and mdata.files_expected:
                runstate = RunState.COMPLETE
            elif (
                #
                # the default is valid. if the author set invalid
                # or set validation-mode:fail we can be sure this
                # run failed
                #
                not mdata.valid and mdata.completed
            ):
                runstate = RunState.FAIL
            else:
                runstate = RunState.START

        #
        # a load
        #
        elif isinstance(mdata, PathsMetadata):
            runstate = RunState.COMPLETE
        #
        # a registration
        #
        elif isinstance(mdata, FileMetadata):
            runstate = RunState.COMPLETE
        #
        #
        elif isinstance(mdata, RunMetadata):
            runstate = RunState.START
        else:
            raise ValueError("Unknown metadata type: {type(mdata)}")
        #
        #
        #
        return runstate
