from abc import ABC
from openlineage.client import OpenLineageClient
from openlineage.client.transport.http import (
    ApiKeyTokenProvider,
    HttpConfig,
    HttpCompression,
    HttpTransport,
)
from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener
from .event import EventBuilder


class Sender(Listener):
    def __init__(self, *, config=None, client=None):
        super().__init__(config)
        self._client = client

    @property
    def client(self):
        if self._client is None:
            h = HttpConfig(
                url=self.config._get("marquez", "base_url", "https://backend:5000"),
                endpoint=self.config._get("marquez", "endpoint", "api/v1/lineage"),
                timeout=int(self.config._get("marquez", "timeout", 5)),
                verify=bool(self.config._get("marquez", "verify", False)) is True,
                auth=ApiKeyTokenProvider(
                    {"apiKey": self.config._get("marquez", "api_key", "none")}
                ),
                compression=HttpCompression.GZIP,
            )
            self._client = OpenLineageClient(transport=HttpTransport(h))
        return self._client

    def metadata_update(self, mdata: Metadata) -> None:
        es = EventBuilder().build(mdata)
        for e in es:
            self.client.emit(e)
