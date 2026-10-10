import logging
from openlineage.client import OpenLineageClient
from openlineage.client.transport.http import (
    ApiKeyTokenProvider,
    HttpConfig,
    HttpTransport,
)
from openlineage.client.serde import Serde

from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener
from .builders.event import EventBuilder


class Sender(Listener):
    def __init__(self, *, config=None, client=None):
        super().__init__(config)
        self._client = client

    @property
    def client(self):
        if self._client is None:
            z = self.config._get(
                "openlineage", "gzip", None
            )  # null is default, otherwise `gzip`
            if str(z).strip() == "":
                z = None
            r = self.config._get("openlineage", "retries", 0)
            url = self.config._get("openlineage", "base_url", "https://backend:5000")
            p = self.config._get("openlineage", "endpoint", "api/v1/lineage")
            t = int(self.config._get("openlineage", "timeout", 2))
            v = bool(self.config._get("openlineage", "verify", False)) is True
            #
            # better me vvvv
            #
            logger = None
            if hasattr(self, "csvpaths"):
                logger = self.csvpaths.logger
            else:
                logger = self.config.logger
            if logger.getEffectiveLevel() == logging.DEBUG:
                _ = f"OpenLineage.v2: config: {self.config.configpath}, z: {z}, r: {r}, url: {url}, p: {p}, t: {t}, v: {v}"
                logger.debug(_)
            #
            #
            #
            h = HttpConfig(
                url=url,
                endpoint=p,
                timeout=t,
                verify=v,
                auth=ApiKeyTokenProvider(
                    {"apiKey": self.config._get("openlineage", "api_key", "none")}
                ),
                compression=z,
                retry={"total": int(r)},
            )

            self._client = OpenLineageClient(transport=HttpTransport(h))
        return self._client

    def metadata_update(self, mdata: Metadata) -> None:
        if not hasattr(self, "csvpaths"):
            self.config.logger.warning(
                "No CsvPaths available. OpenLineage only works with CsvPaths instances."
            )
            return
        es = EventBuilder(listener=self).build(mdata)
        for e in es:
            if False:
                #
                # TODO: in some cases -- e.g. Syniti -- a system may want to collect OL events
                # off the disk, rather than from an endpoint. we could save them out here in
                # _extra_data
                #
                import json

                print("OL EVENT: ")
                je = Serde.to_json(e)
                obj = json.loads(je)
                s = json.dumps(obj, indent=4)
                print(s)
            #
            #
            #
            self.client.emit(e)
