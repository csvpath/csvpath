from openlineage.client.facet_v2 import BaseFacet
import attr


@attr.define
class DataSourceFacet(BaseFacet):
    origin_path: str
