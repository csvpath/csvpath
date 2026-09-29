from openlineage.client.facet_v2 import BaseFacet
import attr


@attr.define
class RunStatistics(BaseFacet):
    errors: int
    all_valid: bool
