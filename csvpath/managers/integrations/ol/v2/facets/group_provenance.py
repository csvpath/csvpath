import attr
from typing import Self
from openlineage.client.facet_v2 import BaseFacet

from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from ..util.name_utility import NameUtility as naut


@attr.define
class GroupProvenance(BaseFacet):
    uuid: str
    path: str
    fingerprint: str
    loaded_at: str
    statements: str

    @classmethod
    def build(self, *, listener: Listener, mdata: Metadata) -> Self:
        uuid = mdata.named_paths_uuid_string
        name = mdata.named_paths_name
        name = naut.from_root_major_if(name)
        mani = listener.csvpaths.paths_manager.get_manifest_for_name(name)
        path = None
        fingerprint = None
        loaded_at = None
        statements = None
        for _ in mani:
            if _.get("uuid") == uuid:
                fingerprint = _.get("fingerprint")
                loaded_at = _.get("time")
                path = _.get("group_file_path")
                statements = _.get("named_paths_count")
                break

        return GroupProvenance(
            uuid=uuid,
            path=path,
            fingerprint=fingerprint,
            statements=statements,
            loaded_at=loaded_at,
        )
