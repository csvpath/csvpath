from openlineage.client.event_v2 import Run

from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener

from ...facets.named_file import NamedFileFacet
from ...facets.registration_details import RegistrationDetailsFacet


class FileRunBuilder:
    def __init__(self, *, listener: Listener) -> None:
        if listener is None:
            raise ValueError("Listener cannot be None")
        self.listener = listener

    def build(self, mdata: Metadata) -> Run:
        fs = {}
        fs["namedFile"] = NamedFileFacet(mdata.named_file_name)
        fs["registrationDetails"] = RegistrationDetailsFacet(
            origin_path=mdata.origin_path,
            template=mdata.template,
            uuid=mdata.uuid_string,
            named_file_name=mdata.named_file_name,
        )
        run = Run(runId=mdata.uuid_string, facets=fs)
        return run
