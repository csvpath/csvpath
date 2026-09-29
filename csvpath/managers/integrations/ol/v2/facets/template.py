from openlineage.client.facet_v2 import BaseFacet
import attr


@attr.define
class TemplateFacet(BaseFacet):
    template: str
