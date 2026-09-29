from openlineage.client.facet_v2 import BaseFacet
import attr


@attr.define
class SourceFacet(BaseFacet):
    source: str
    fingerprint: str
