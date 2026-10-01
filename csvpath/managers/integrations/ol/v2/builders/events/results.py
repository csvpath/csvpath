import json
import traceback
from openlineage.client.facet_v2 import symlinks_dataset
from openlineage.client.facet_v2 import schema_dataset
from openlineage.client.event_v2 import RunEvent
from openlineage.client.event_v2 import Job, Run
from openlineage.client.event_v2 import InputDataset, OutputDataset

from csvpath import CsvPath
from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener
from csvpath.matching.util.expression_utility import ExpressionUtility as exut
from csvpath.matching.productions.header import Header

from ...facets.run_statistics import RunStatistics
from ...facets.group_provenance import GroupProvenance
from ...facets.data_provenance import DataProvenance

from ..tokens import Tokens
from ..job import JobBuilder
from ..run import RunBuilder
from ..run_state import RunStateBuilder
from ...util.protocol_utility import ProtocolUtility as prut
from ...util.name_utility import NameUtility as naut

from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader


class ResultsEventBuilder:
    def __init__(self, *, listener: Listener) -> None:
        if listener is None:
            raise ValueError("Listener cannot be None")
        self.listener = listener

    def build(self, mdata: Metadata, job: Job, run: Run) -> list[RunEvent]:
        try:
            ns, path = naut.namespace_and_name(
                config=self.listener.config,
                mdata=mdata,
                namespace=mdata.named_files_root,
                path=mdata.named_file_name,
            )
            path = naut.from_root_major_if(path)
            prov = self._file_provenance(mdata)
            file = InputDataset(namespace=ns, name=path, facets={"provenance": prov})

            prov = self._paths_provenance(mdata)
            ns, path = naut.namespace_and_name(
                config=self.listener.config,
                mdata=mdata,
                namespace=mdata.named_paths_root,
                path=mdata.named_paths_name,
            )
            links = self._input_symlinks(mdata)
            schema = self._input_schema(mdata)
            paths = InputDataset(
                namespace=ns,
                name=path,
                facets={
                    "symlink_identifiers": links,
                    "provenance": prov,
                    "schema": schema,
                },
            )

            inputs = [file, paths]
            runstate = RunStateBuilder(listener=self.listener).build(mdata)
            job = job or JobBuilder(listener=self.listener).build(mdata)
            run = run or RunBuilder(listener=self.listener).build(mdata)

            ds = self._output_data(mdata)
            ms = self._output_metadata(mdata)

            e = RunEvent(
                eventType=runstate,
                eventTime=mdata.time.isoformat(),
                run=run,
                job=job,
                inputs=inputs,
                outputs=[ds, ms],
                producer=Tokens.PRODUCER,
            )
            return [e]
        except Exception as e:
            print(traceback.format_exc())
            self.listener.config.logger.exception(e)

    def _file_provenance(self, mdata: Metadata) -> DataProvenance:
        prov = DataProvenance.build(listener=self.listener, mdata=mdata)
        return prov

    def _paths_provenance(self, mdata: Metadata) -> GroupProvenance:
        prov = GroupProvenance.build(listener=self.listener, mdata=mdata)
        return prov

    def _output_data(self, mdata: Metadata) -> OutputDataset:
        fs = {}
        fs["symlink_identifiers"] = self._symlinks(mdata)
        with DataFileReader(mdata.manifest_path) as reader:
            mani = json.load(reader.source)
            stats = RunStatistics(
                errors=mani.get("error_count"), all_valid=mani.get("all_valid")
            )
            outputfs = {"runStatistics": stats}
        ns, path = naut.namespace_and_name(
            config=self.listener.config,
            mdata=mdata,
            namespace=mdata.named_files_root,
            path=mdata.manifest_path,
        )
        ds = OutputDataset(namespace=ns, name=path, facets=fs, outputFacets=outputfs)
        return ds

    def _input_schema(self, mdata: Metadata) -> schema_dataset.SchemaDatasetFacet:
        fields = []
        path = Nos(mdata.named_paths_root).join(mdata.named_paths_name)
        path = Nos(path).join("manifest.json")
        paths = []
        with DataFileReader(path) as reader:
            js = json.load(reader.source)
            for _ in js:
                a = str(_.get("uuid")).strip()
                b = str(mdata.named_paths_uuid).strip()
                if a == b:
                    paths = _.get("named_paths")
                    break
            else:
                ...
        for _ in paths:
            matcher = CsvPath().parse(_, disposably=True)
            headers = []
            lst = [e[0] for e in matcher.expressions]
            for _ in lst:
                headers += exut.get_my_descendents_of_class(thing=_, clazz=Header)
            for h in headers:
                name = h.name
                ttype = "Unknown"
                if h.parent and h.parent.name == "string":
                    ttype = "STRING"
                elif h.parent and h.parent.name == "integer":
                    ttype = "INT"
                elif h.parent and h.parent.name == "decimal":
                    ttype = "FLOAT"
                elif h.parent and h.parent.name == "date":
                    ttype = "DATE"
                elif h.parent and h.parent.name == "datetime":
                    ttype = "DATETIME"
                elif h.parent and h.parent.name == "boolean":
                    ttype = "BOOLEAN"
                elif h.parent and h.parent.name == "email":
                    ttype = "EMAIL"
                elif h.parent and h.parent.name == "url":
                    ttype = "URL"
                elif h.parent and h.parent.name in [
                    "nonspecific",
                    "unspecified",
                    "blank",
                ]:
                    ttype = "BLANK"
                elif h.parent and h.parent.name == "wildcard":
                    ttype = "WILDCARD"
                elif h.parent and h.parent.name == "uuid":
                    ttype = "UUID"
                field = schema_dataset.SchemaDatasetFacetFields(name=name, type=ttype)
                field.fields = None
                fields.append(field)
        return schema_dataset.SchemaDatasetFacet(fields=fields)

    def _input_symlinks(self, mdata: Metadata) -> symlinks_dataset.SymlinksDatasetFacet:
        path = Nos(mdata.named_file_name).join("group.csvpaths")
        ns, path = naut.namespace_and_name(
            config=self.listener.config,
            mdata=mdata,
            namespace=mdata.named_files_root,
            path=path,
        )
        group_file_symlink = symlinks_dataset.Identifier(
            namespace=ns,
            name=path,
            type="FILE",
        )
        return symlinks_dataset.SymlinksDatasetFacet(identifiers=[group_file_symlink])

    def _symlinks(self, mdata: Metadata) -> symlinks_dataset.SymlinksDatasetFacet:
        ns = prut.update_protocol_if(
            config=self.listener.config, mdata=mdata, root=mdata.named_files_root
        )
        reference_symlink = symlinks_dataset.Identifier(
            namespace=ns,
            name=mdata.reference,
            type="FILE",
        )
        origin_symlink = symlinks_dataset.Identifier(
            namespace=ns,
            name=mdata.run_uuid_string,
            type="UUID",
        )
        return symlinks_dataset.SymlinksDatasetFacet(
            identifiers=[reference_symlink, origin_symlink]
        )

    def _output_metadata(self, mdata: Metadata) -> OutputDataset:
        mani = mdata.archive_path
        mani = Nos(mani).join(mdata.named_paths_name)
        mani = Nos(mani).join("manifest.json")
        ns, path = naut.namespace_and_name(
            config=self.listener.config,
            mdata=mdata,
            namespace=mdata.archive_path,
            path=mani,
        )
        ms = OutputDataset(namespace=ns, name=path, facets={})
        return ms
