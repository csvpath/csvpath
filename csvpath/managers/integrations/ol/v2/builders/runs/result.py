import json

from openlineage.client.facet_v2 import parent_run, error_message_run
from openlineage.client.event_v2 import Run

from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener
from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader

from ...util.name_utility import NameUtility as naut
from ...util.engine_utility import EngineUtility as enut
from ...facets.actual_file import ActualFile


class ResultRunBuilder:
    def __init__(self, *, listener: Listener) -> None:
        if listener is None:
            raise ValueError("Listener cannot be None")
        self.listener = listener

    def build(self, mdata: Metadata):
        fs = {}
        if mdata.run_uuid is not None:
            ns, path = naut.namespace_and_name_2(
                config=self.listener.config,
                mdata=mdata,
                instance=mdata.instance_identity,
                entity=mdata.named_results_name,
                eom="entity",
                job_type="run",
            )

            job = parent_run.Job(namespace=ns, name=path)
            parent_run_facet = parent_run.ParentRunFacet(
                run=parent_run.Run(runId=mdata.run_uuid_string),
                job=job,
            )
            fs["parent"] = parent_run_facet
            fs["actual_file"] = ActualFile.build(mdata)

        else:
            print(
                "The OpenLineage run event builder cannot find the named_paths_uuid value in Metadata. If this is not testing please log a bug."
            )

        epath = Nos(mdata.instance_home).join("errors.json")
        if Nos(epath).exists():
            with DataFileReader(epath) as reader:
                try:
                    j = json.load(reader.source)
                    for e in j:
                        msg = f"{e['error']} at {e['line_count']}\nSource: {e['source']}\nFile: {e['filename']}\nSee errors.json for more details"
                        fs["errorMessage"] = error_message_run.ErrorMessageRunFacet(
                            message=msg,
                            programmingLanguage="CsvPath and/or Python",
                            stackTrace=e["trace"],
                        )
                except Exception:
                    self.listener.csvpaths.logger.exception(e)

        fs["processing_engine"] = enut.engine_facet()
        return Run(runId=mdata.uuid_string, facets=fs)
