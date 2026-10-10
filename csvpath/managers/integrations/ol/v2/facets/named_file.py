from openlineage.client.facet_v2 import BaseFacet
import attr


@attr.define
class NamedFileFacet(BaseFacet):
    named_file: str
