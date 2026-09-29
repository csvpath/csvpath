import os
from openlineage.client.event_v2 import Dataset, RunEvent
from openlineage.client.event_v2 import Job, Run, RunState
from openlineage.client.event_v2 import InputDataset, OutputDataset

from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener
from csvpath.util.nos import Nos

from ..tokens import Tokens
from ..job import JobBuilder
from ..run import RunBuilder
from ..run_state import RunStateBuilder
from ...facets.group_provenance import GroupProvenance
from ...facets.data_provenance import DataProvenance
from ...facets.actual_file import ActualFile
from ...util.protocol_utility import ProtocolUtility as prut
from ...util.name_utility import NameUtility as naut


class ResultEventBuilder:
    def __init__(self, *, listener: Listener) -> None:
        if listener is None:
            raise ValueError("Listener cannot be None")
        self.listener = listener

    #
    # event for a single csvpath in a group
    #
    def build(self, mdata: Metadata, job: Job, run: Run):
        #
        # if we are source mode preceding we're going to replace the original file
        # with the preceding instance identity/data.csv
        #
        file = self._file_inputs(mdata)
        paths = self._paths_inputs(mdata)
        inputs = [file, paths]

        runstate = RunStateBuilder(listener=self.listener).build(mdata)
        #
        # there are 3 types of outputs
        #  - 6 standard files: data.csv, vars.json, errors.json, etc.
        #  - manifest.json
        #  - 0 or more transfers
        #
        # NOTE: we need to add parquet
        #
        outputs = [] if runstate == RunState.START else self._outputs(mdata)

        #
        # manifest
        #
        ns = prut.update_protocol_if(
            config=self.listener.config, mdata=mdata, root=mdata.archive_path
        )
        path = naut.trim_namespace_if(namespace=ns, path=mdata.manifest_path)
        outmani = Dataset(
            namespace=ns,
            name=path,
        )
        outputs.append(outmani)
        # transfers
        tpaths = mdata.transfers
        if tpaths is not None:
            for t in tpaths:
                o = Dataset(
                    namespace=mdata.archive_path,
                    name=f"{t[3]}",
                )
                outputs.append(o)
        job = job or JobBuilder(listener=self.listener).build(mdata)
        run = run or RunBuilder(listener=self.listener).build(mdata)
        if mdata.time is None:
            mdata.set_time()
        e = RunEvent(
            eventType=runstate,
            eventTime=mdata.first_time().isoformat(),
            run=run,
            job=job,
            inputs=inputs,
            outputs=outputs,
            producer=Tokens.PRODUCER,
        )
        return [e]

    def _outputs(self, mdata: Metadata) -> list:
        outputs = []
        #
        # loop on all the actual data files and just name them
        #
        try:
            ns = prut.update_protocol_if(
                config=self.listener.config, mdata=mdata, root=mdata.archive_path
            )
            nos = Nos(mdata.instance_home)
            files = nos.listdir(files_only=True)
            for file in files:
                if file == "manifest.json":
                    continue
                path = nos.join(file)
                path = naut.trim_namespace_if(namespace=ns, path=path)
                o = OutputDataset(
                    name=path,
                    namespace=ns,
                    # facets=fs,
                    # outputFacets=of,
                )
                outputs.append(o)
        except Exception:
            import traceback

            print(traceback.format_exc())
        return outputs

    def _file_inputs(self, mdata: Metadata) -> InputDataset:
        try:
            ns = prut.update_protocol_if(
                config=self.listener.config, mdata=mdata, root=mdata.named_files_root
            )
            fs = {}
            fs["provenance"] = self._file_provenance(mdata)
            fs["actual_file"] = self._actual_file(mdata)
            path = None
            preceding = (
                mdata.preceding_instance_identity and mdata.source_mode_preceding
            )
            preceding = preceding or mdata.by_line
            if preceding is True and mdata.preceding_instance_identity:
                path = f"{mdata.preceding_instance_identity}{os.sep}data.csv"
            else:
                path = mdata.actual_data_file
            path = naut.from_root_major_if(path)
            path = naut.trim_namespace_if(namespace=ns, path=path)
            return InputDataset(namespace=ns, name=path, facets=fs)
        except Exception as e:
            import traceback

            print(traceback.format_exc())
            self.listener.config.logger.exception(e)

    def _actual_file(self, mdata: Metadata) -> ActualFile:
        return ActualFile.build(mdata)

    def _file_provenance(self, mdata: Metadata) -> DataProvenance:
        prov = DataProvenance.build(listener=self.listener, mdata=mdata)
        return prov

    def _paths_inputs(self, mdata: Metadata) -> InputDataset:
        ns = prut.update_protocol_if(
            config=self.listener.config, mdata=mdata, root=mdata.named_paths_root
        )
        #
        # named_results_name shouldn't be a reference, but the guard is cheap.
        #
        path = mdata.named_results_name
        path = naut.from_root_major_if(path)
        prov = self._paths_provenance(mdata)
        paths = InputDataset(namespace=ns, name=path, facets={"provenance": prov})
        return paths

    def _paths_provenance(self, mdata: Metadata) -> GroupProvenance:
        prov = GroupProvenance.build(listener=self.listener, mdata=mdata)
        return prov
