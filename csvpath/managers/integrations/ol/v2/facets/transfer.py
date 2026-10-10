from openlineage.client.facet_v2 import BaseFacet
import attr


@attr.define
class TransferFacet(BaseFacet):
    name: str
    status: str
