from openlineage.client.facet_v2 import BaseFacet
import attr


#
# the registration UUID is created automatically if it is not
# provided in the add_named_file call. async requests must pass
# the uuid and we need to capture it if present. regardless, it
# is an output as well as an input.
#
@attr.define
class RegistrationUuidFacet(BaseFacet):
    uuid: str
