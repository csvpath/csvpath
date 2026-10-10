from openlineage.client.event_v2 import Run
from openlineage.client.facet_v2 import execution_parameters_run

from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener

from ...util.engine_utility import EngineUtility as enut


class ResultsRunBuilder:
    def __init__(self, *, listener: Listener) -> None:
        if listener is None:
            raise ValueError("Listener cannot be None")
        self.listener = listener

    def build(self, mdata: Metadata):
        fs = {}
        pe = enut.engine_facet()
        fs["processing_engine"] = pe
        fs["executionParameters"] = self._execution_params(mdata)
        return Run(runId=mdata.run_uuid_string, facets=fs)

    def _execution_params(
        self, mdata: Metadata
    ) -> execution_parameters_run.ExecutionParametersRunFacet:
        parameters = []
        p = execution_parameters_run.ExecutionParameter(
            key="template",
            name="Template",
            description="A pattern for generating a destination path using the original source data location as an input",
            value=mdata.template
            if mdata.template is not None
            else "None",  # we want to see the param, even if blank.
        )
        parameters.append(p)
        m = None
        if mdata.method.find("_paths") > -1:
            m = "Validations ran serially"
        elif mdata.method.find("_by_line") > -1:
            m = "Validations ran breadth-first"
        elif mdata.method.find("dynamic") > -1:
            m = "Serial validation of live objects"
        #
        # no else because we don't want to break here if there is weirdness.
        # catching an invalid run method is definitely someone elses problem.
        #
        p = execution_parameters_run.ExecutionParameter(
            key="method", name="Run method", description=m, value=mdata.method
        )
        parameters.append(p)

        p = execution_parameters_run.ExecutionParameter(
            key="named_file_name",
            name="The named-file name",
            description="The registered source data. Names beginning with `$` are references.",
            value=mdata.template if mdata.template is not None else "None",
        )
        parameters.append(p)

        p = execution_parameters_run.ExecutionParameter(
            key="named_paths_name",
            name="The named-paths group name",
            description="The validation statements group. Names beginning with `$` are references.",
            value=mdata.template if mdata.template is not None else "None",
        )
        parameters.append(p)
        return execution_parameters_run.ExecutionParametersRunFacet(parameters)
