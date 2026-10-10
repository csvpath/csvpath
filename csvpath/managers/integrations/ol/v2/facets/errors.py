from typing import Any
from openlineage.client.facet_v2 import BaseFacet
import attr


@attr.define
class ErrorsFacet(BaseFacet):
    errors: list[dict[str, Any]]
