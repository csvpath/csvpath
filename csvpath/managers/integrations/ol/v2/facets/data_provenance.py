import attr
import json
from typing import Self
from openlineage.client.facet_v2 import BaseFacet

from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from csvpath.managers.results.result_metadata import ResultMetadata
from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader


@attr.define
class DataProvenance(BaseFacet):
    uuid: str
    path: str
    fingerprint: str
    origin_path: str
    registered_at: str

    @classmethod
    def build(cls, *, listener: Listener, mdata: Metadata) -> Self:
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        if listener is None:
            raise ValueError("Listener cannot be None")
        uuid = mdata.named_file_uuid_string
        if uuid is None and not isinstance(mdata, ResultMetadata):
            raise ValueError(f"{type(mdata)} UUID cannot be None in {mdata}")
        fingerprint = None
        path = None
        origin_path = None
        registered_at = None
        #
        # if we're a result our data may have come from the directly preceding
        # statement, or a combination of preceding statements, if breadth-first.
        # in that case we'll say the fingerprint is "dynamically set" (i.e.
        # unknown till complete). likewise origin_path will "preceding" and
        # registered_at, "dynamic". Note that in the case of a dynamic run
        # method used programmatically on JSON input we may never register the
        # data.
        #
        if isinstance(mdata, ResultMetadata):
            if mdata.source_mode_preceding or mdata.by_line:
                uuid = None
                fingerprint = "dynamically set"
                origin_path = "preceding"
                registered_at = "dynamic"
            else:
                ...
                # here we should find the UUID. we know it from the parent's manifest

                nos = Nos(mdata.instance_home)
                path = nos.path[0 : nos.path.rfind(nos.sep)]
                path = Nos(path).join("manifest.json")
                with DataFileReader(path) as reader:
                    js = json.load(reader.source)
                    uuid = js.get("named_file_uuid")
            path = mdata.actual_data_file
        else:
            fingerprint = mdata.named_file_fingerprint
            path = mdata.named_file_path
        if uuid:
            mani = listener.csvpaths.file_manager.get_manifest(mdata.named_file_name)
            for _ in mani:
                if _.get("uuid") == uuid:
                    origin_path = _.get("origin_path")
                    registered_at = _.get("time")
                    break
            else:
                if not isinstance(mdata, ResultMetadata):
                    listener.config.logger().warning(
                        "Could not match UUID {uuid} in root manifest"
                    )

        dp = DataProvenance(
            uuid=uuid,
            path=path,
            fingerprint=fingerprint,
            origin_path=origin_path,
            registered_at=registered_at,
        )
        return dp
