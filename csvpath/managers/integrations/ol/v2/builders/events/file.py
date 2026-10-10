from openlineage.client.facet_v2 import (
    output_statistics_output_dataset,
    symlinks_dataset,
    documentation_dataset,
)
from openlineage.client.event_v2 import (
    RunEvent,
    Job,
    InputDataset,
    OutputDataset,
    RunState,
)

from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener
from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader

from ...util.name_utility import NameUtility as naut

from ...facets.source import SourceFacet

from ..tokens import Tokens
from ..job import JobBuilder
from ..run import RunBuilder


class FileEventBuilder:
    def __init__(self, *, listener: Listener) -> None:
        if listener is None:
            raise ValueError("Listener cannot be None")
        self.listener = listener

    def build(
        self,
        mdata: Metadata,
        job: Job = None,
    ) -> list[RunEvent]:
        inputs = self._inputs(mdata)
        #
        # create the outputs for the registered data
        #
        # maybe StorageDatasetFacet
        ds = self._output_data(mdata)
        ms = self._output_metadata(mdata)
        outputs = [ds, ms]

        job = job or JobBuilder(listener=self.listener).build(mdata)

        run = RunBuilder(listener=self.listener).build(mdata)
        start = RunEvent(
            eventType=RunState.START,
            eventTime=mdata.first_time().isoformat(),
            run=run,
            job=job,
            inputs=inputs,
            outputs=[],
            producer=Tokens.PRODUCER,
        )
        complete = RunEvent(
            eventType=RunState.COMPLETE,
            eventTime=mdata.time.isoformat(),
            run=run,
            job=job,
            inputs=inputs,
            outputs=outputs,
            producer=Tokens.PRODUCER,
        )
        return [start, complete]

    def _inputs(self, mdata: Metadata) -> list[InputDataset]:
        source = SourceFacet(mdata.origin_path)
        fs = {}
        ifs = {"source": source}
        #
        # Note: we don't use a trimmed version of orgin_path because
        # the origin path is physically outside the namespace. we could
        # use naut.namespace_and_name just for consistency but prut is
        # more clear
        #
        path = Nos(mdata.named_files_root).join(mdata.named_file_name)
        path = Nos(path).join("README.md")
        if Nos(path).exists():
            with DataFileReader(path) as reader:
                readme = reader.source.read()
                fs["documentation"] = documentation_dataset.DocumentationDatasetFacet(
                    description=readme
                )
        ns, name = naut.namespace_and_name(
            config=self.listener.config, mdata=mdata, path=mdata.origin_path
        )
        ds = InputDataset(namespace=ns, name=name, facets=fs, inputFacets=ifs)
        return [ds]

    def _output_data(self, mdata: Metadata) -> OutputDataset:
        fs = {}
        fs["symlink_identifiers"] = self._symlinks(mdata)
        stats = output_statistics_output_dataset.OutputStatisticsOutputDatasetFacet(
            size=mdata.file_size, fileCount=1
        )
        outputfs = {"outputStatistics": stats}
        ns, path = naut.namespace_and_name_2(
            config=self.listener.config,
            mdata=mdata,
            eom="output",
            job_type="register",
            entity=mdata.named_file_name,
        )
        ds = OutputDataset(namespace=ns, name=path, facets=fs, outputFacets=outputfs)
        return ds

    def _symlinks(self, mdata: Metadata) -> symlinks_dataset.SymlinksDatasetFacet:
        ns, name = naut.namespace_and_name_2(
            config=self.listener.config,
            mdata=mdata,
            eom="output",
            job_type="register",
            entity=mdata.named_file_name,
        )
        reference_symlink = symlinks_dataset.Identifier(
            namespace=ns,
            name=mdata.reference,
            type="FILE",
        )
        origin_symlink = symlinks_dataset.Identifier(
            namespace=ns,
            name=mdata.uuid_string,
            type="UUID",
        )
        return symlinks_dataset.SymlinksDatasetFacet(
            identifiers=[reference_symlink, origin_symlink]
        )

    def _output_metadata(self, mdata: Metadata) -> OutputDataset:
        mani = mdata.named_files_root
        mani = Nos(mani).join(mdata.named_file_name)
        mani = Nos(mani).join("manifest.json")
        fs = {}
        ns, path = naut.namespace_and_name_2(
            config=self.listener.config,
            mdata=mdata,
            job_type="register",
            eom="manifest",
            entity=mdata.named_file_name,
        )
        ms = OutputDataset(namespace=ns, name=path, facets=fs)
        return ms
