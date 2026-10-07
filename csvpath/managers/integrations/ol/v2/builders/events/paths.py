from openlineage.client.facet_v2 import symlinks_dataset, documentation_dataset

from openlineage.client.event_v2 import RunEvent
from openlineage.client.event_v2 import RunState
from openlineage.client.event_v2 import OutputDataset

from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener


from ..tokens import Tokens
from ..job import JobBuilder
from ..run import RunBuilder
from ...util.name_utility import NameUtility as naut

from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader


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
        fs = {}
        fs["symlink_identifiers"] = self._symlinks(mdata)
        ns, path = naut.namespace_and_name_2(
            config=self.listener.config,
            mdata=mdata,
            eom="output",
            job_type="load",
            entity=mdata.named_paths_name,
        )

        p = Nos(mdata.named_paths_root).join(mdata.named_paths_name)
        p = Nos(p).join("README.md")
        if Nos(p).exists():
            with DataFileReader(p) as reader:
                readme = reader.source.read()
                # readme = json.dumps(readme)
                fs["documentation"] = documentation_dataset.DocumentationDatasetFacet(
                    description=readme
                )

        ds = OutputDataset(namespace=ns, name=path, facets=fs)
        return ds

    def _symlinks(self, mdata: Metadata) -> symlinks_dataset.SymlinksDatasetFacet:
        ns, name = naut.namespace_and_name_2(
            config=self.listener.config,
            mdata=mdata,
            eom="output",
            job_type="load",
            entity=mdata.named_paths_name,
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
        raw_symlink = symlinks_dataset.Identifier(
            namespace=ns,
            name=mdata.group_file_path,
            type="FILE",
        )
        ids = [reference_symlink, uuid_symlink, raw_symlink]
        return symlinks_dataset.SymlinksDatasetFacet(identifiers=ids)

    def _output_metadata(self, mdata: Metadata) -> OutputDataset:
        mani = mdata.named_paths_root
        mani = Nos(mani).join(mdata.named_paths_name)
        mani = Nos(mani).join("manifest.json")
        ns, path = naut.namespace_and_name_2(
            config=self.listener.config,
            mdata=mdata,
            eom="manifest",
            job_type="load",
            entity=mdata.named_paths_name,
        )
        ms = OutputDataset(namespace=ns, name=path, facets={})
        return ms
