import attr
from typing import Self
from openlineage.client.facet_v2 import BaseFacet

from csvpath.managers.metadata import Metadata


@attr.define
class ActualFile(BaseFacet):
    actual_file: str
    source_mode: str
    method: str

    @classmethod
    def build(cls, mdata: Metadata) -> Self:
        b = mdata.preceding_instance_identity and mdata.source_mode_preceding
        b = b or mdata.by_line
        source_mode = "preceding" if b else "origin"
        return ActualFile(
            actual_file=mdata.actual_data_file,
            source_mode=source_mode,
            method=mdata.method,
        )
