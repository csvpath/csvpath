from openlineage.client.facet_v2 import BaseFacet
import attr


@attr.define
class LoadDetailsFacet(BaseFacet):
    template: str
    append: bool
    named_paths_name: str
    named_paths_count: int
