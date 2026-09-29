from openlineage.client.facet_v2 import symlinks_dataset

from openlineage.client.event_v2 import RunEvent
from openlineage.client.event_v2 import RunState
from openlineage.client.event_v2 import OutputDataset

from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener


from ..tokens import Tokens
from ..job import JobBuilder
from ..run import RunBuilder
from ...util.protocol_utility import ProtocolUtility as prut

from csvpath.util.nos import Nos


class PathsEventBuilder:
    def __init__(self, *, listener: Listener) -> None:
        if listener is None:
            raise ValueError("Listener cannot be None")
        self.listener = listener

    def build(self, mdata: Metadata, job) -> list[RunEvent]:

        ds = self._output_data(mdata)
        ms = self._output_metadata(mdata)
        outputs = [ds, ms]

        job = job or JobBuilder(listener=self.listener).build(mdata)

        run = RunBuilder(listener=self.listener).build(mdata)

        complete = RunEvent(
            eventType=RunState.COMPLETE,
            eventTime=mdata.time.isoformat(),
            run=run,
            job=job,
            inputs=[],
            outputs=outputs,
            producer=Tokens.PRODUCER,
        )
        return [complete]

    def _output_data(self, mdata: Metadata) -> OutputDataset:
        ns = prut.update_protocol_if(
            config=self.listener.config, mdata=mdata, root=mdata.named_paths_root
        )
        fs = {}
        fs["symlink_identifiers"] = self._symlinks(mdata)

        path = prut.update_protocol_if(
            config=self.listener.config, mdata=mdata, root=mdata.group_file_path
        )

        if path.startswith(ns):
            path = path[len(ns) + 1 :]

        ds = OutputDataset(namespace=ns, name=f"{path}", facets=fs)
        return ds

    def _symlinks(self, mdata: Metadata) -> symlinks_dataset.SymlinksDatasetFacet:
        ns = prut.update_protocol_if(
            config=self.listener.config, mdata=mdata, root=mdata.named_paths_root
        )

        reference_symlink = symlinks_dataset.Identifier(
            namespace=ns,
            name=mdata.reference,
            type="FILE",
        )
        uuid_symlink = symlinks_dataset.Identifier(
            namespace=ns,
            name=mdata.uuid_string,
            type="UUID",
        )
        #
        # if we updated a local path or azure URI we should put the orig
        # as a symlink
        #
        path = prut.update_protocol_if(
            config=self.listener.config, mdata=mdata, root=mdata.group_file_path
        )
        ids = [reference_symlink, uuid_symlink]
        if mdata.group_file_path != path:
            path = mdata.group_file_path
            if path.startswith(ns):
                path = path[len(ns) + 1 :]
            raw_symlink = symlinks_dataset.Identifier(
                namespace=ns,
                name=path,
                type="FILE",
            )
            ids.append(raw_symlink)

        return symlinks_dataset.SymlinksDatasetFacet(identifiers=ids)

    def _output_metadata(self, mdata: Metadata) -> OutputDataset:
        ns = prut.update_protocol_if(
            config=self.listener.config, mdata=mdata, root=mdata.named_paths_root
        )
        mani = mdata.named_paths_root
        mani = Nos(mani).join(mdata.named_paths_name)
        mani = Nos(mani).join("manifest.json")

        if mani.startswith(ns):
            mani = mani[len(ns) + 1 :]

        fs = {}
        ms = OutputDataset(namespace=ns, name=mani, facets=fs)
        return ms
