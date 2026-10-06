from openlineage.client.event_v2 import Run

from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener

from ...util.engine_utility import EngineUtility as enut


class ResultsRunBuilder:
    def __init__(self, *, listener: Listener) -> None:
        if listener is None:
            raise ValueError("Listener cannot be None")
        self.listener = listener

    def build(self, mdata: Metadata):
        facets = {}
        pe = enut.engine_facet()
        facets["processing_engine"] = pe
        return Run(runId=mdata.run_uuid_string, facets=facets)
