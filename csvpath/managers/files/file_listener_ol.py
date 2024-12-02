from openlineage.client.client import OpenLineageClient

from ..metadata import Metadata
from ..listener import Listener
from ..ol.event import EventBuilder
from ..ol.job import JobBuilder


class OpenLineageFileListener(Listener):
    def __init__(self, config=None):
        super().__init__(config)
        self.ol_client = None

    def metadata_update(self, mdata: Metadata) -> None:
        if self.ol_client is None:
            client_url = self.config._get("marquez", "base_url")
            if client_url is None:
                client_url = "http://localhost:5000"
            self.ol_client = OpenLineageClient(url=client_url)

        e = EventBuilder().build(mdata)
        self.ol_client.emit(e)
