from openlineage.client.client import OpenLineageClient

from ..metadata import Metadata
from ..listener import Listener
from ..ol.event import EventBuilder
from ..ol.job import JobBuilder


class OpenLineagePathsListener(Listener):
    def __init__(self, config=None):
        super().__init__(config)
        self.ol_client = None

    def metadata_update(self, mdata: Metadata) -> None:
        if self.ol_client is None:
            client_url = self.config._get("marquez", "base_url")
            if client_url is None:
                print(
                    "WARNING: OpenLineage listeners are live but there is no Marquez API URL"
                )
                return
                # client_url = "http://localhost:5000"
            self.ol_client = OpenLineageClient(url=client_url)

        es = EventBuilder().build(mdata)
        for e in es:
            self.ol_client.emit(e)
