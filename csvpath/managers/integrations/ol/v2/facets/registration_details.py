from openlineage.client.facet_v2 import BaseFacet
import attr


#
# for file reg, prefer the details facet rather than three individual facets
#
@attr.define
class RegistrationDetailsFacet(BaseFacet):
    template: str
    uuid: str
    origin_path: str
    named_file_name: str
