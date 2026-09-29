from openlineage.client.event_v2 import Run

from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener

from ...util.protocol_utility import ProtocolUtility as prut
from ...facets.named_paths import NamedPathsFacet
from ...facets.load_details import LoadDetailsFacet


class PathsRunBuilder:
    def __init__(self, *, listener: Listener) -> None:
        if listener is None:
            raise ValueError("Listener cannot be None")
        self.listener = listener

    def build(self, mdata: Metadata) -> Run:
        ns = prut.update_protocol_if(
            config=self.listener.config, mdata=mdata, root=mdata.named_paths_root
        )
        fs = {}
        fs["groupName"] = NamedPathsFacet(mdata.named_paths_name)
        fs["loadDetails"] = LoadDetailsFacet(
            template=mdata.template,
            append=mdata.append,
            named_paths_name=mdata.named_paths_name,
            named_paths_count=mdata.named_paths_count,
        )
        path = mdata.group_file_path
        if path.startswith(ns):
            path = path[len(ns) + 1 :]
        run = Run(runId=mdata.uuid_string, facets=fs)
        return run
