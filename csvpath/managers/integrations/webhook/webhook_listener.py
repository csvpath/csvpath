import requests
import threading

from abc import ABC
from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener

#
# ~
#    webhook-url: https://zapier.com/hooks/asdf
#    webhook-data: name > var|name, phone > $mygroup#result.variables.cell, $.csvpath.total_lines
#
#
#    webhook-file: $.results.files.data, $mygroup#myinstance.results.files.errors
#    $.results.
#    $clean-invoices.results.acme/invoices/2025/Feb:0.step-three#var|cell
#    $mygroup#myinstance.variables.cell
#
# ~
#


class WebhookListener(Listener, threading.Thread):
    def __init__(self, *, config=None):
        super().__init__(config)
        self._url = None
        self.csvpaths = None
        self.result = None
        self.metadata = None

    @property
    def csvpath(self):
        return self.result.csvpath

    @property
    def url(self):
        if self._url is None:
            if self.result is None:
                self.csvpaths.logger.info(
                    "Cannot send to webhook because there is no result"
                )
            self._url = self.csvpath.metadata.get("webhook-url")
            if self._url is not None:
                self._url = self._url.strip()
        return self._url

    def run(self):
        self._metadata_update(self.metadata)

    def metadata_update(self, mdata: Metadata) -> None:
        self.metadata = mdata
        self.start()

    def _metadata_update(self, mdata: Metadata) -> None:
        payload = self.create_payload(mdata)
        #
        # prep request
        #
        headers = {"Content-Type": "application/json"}
        #
        # send
        #
        x = requests.post(self.url, json=payload, headers=headers)
        if x and x.status_code != 200:
            if self.csvpaths is not None:
                self.csvpaths.logger.warning(
                    "WebhookListener received status code %s from %s",
                    x.status_code,
                    "",
                )
            elif self.result is not None:
                self.result.csvpath.logger.warning(
                    "WebhookListener received status code %s from %s",
                    x.status_code,
                    "",
                )
            else:
                print(
                    f"WARNING: WebhookListener received status code {x.status_code} from"
                )

    def create_payload(self, mdata: Metadata) -> dict:
        ...
