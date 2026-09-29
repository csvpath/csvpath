import attr
from typing import Self
from openlineage.client.facet_v2 import BaseFacet

from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from csvpath.managers.results.result_metadata import ResultMetadata


@attr.define
class DataProvenance(BaseFacet):
    uuid: str
    path: str
    origin_path: str
    registered_at: str
    fingerprint: str

    @classmethod
    def build(self, *, listener: Listener, mdata: Metadata) -> Self:
        uuid = (
            None if isinstance(mdata, ResultMetadata) else mdata.named_file_uuid_string
        )
        path = (
            mdata.actual_data_file
            if isinstance(mdata, ResultMetadata)
            else mdata.named_file_path
        )
        fingerprint = (
            None if isinstance(mdata, ResultMetadata) else mdata.named_file_fingerprint
        )
        origin_path = None
        registered_at = None
        #
        # going to the named-file's own manifest would probably be faster.
        #
        if not isinstance(mdata, ResultMetadata):
            mani = listener.csvpaths.file_manager.files_root_manifest
            for _ in mani:
                if _.get("uuid") == uuid:
                    origin_path = _.get("source_path")
                    registered_at = _.get("time")
                    break

        print(f"uuid: {uuid}")
        print(f"path: {path}")
        print(f"fingerprint: {fingerprint}")
        print(f"origin_path: {origin_path}")
        print(f"registered_at: {registered_at}")

        return DataProvenance(
            uuid=uuid,
            path=path,
            fingerprint=fingerprint,
            origin_path=origin_path,
            registered_at=registered_at,
        )
