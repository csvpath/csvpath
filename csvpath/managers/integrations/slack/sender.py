import requests
import threading

from abc import ABC
from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener
from csvpath.util.box import Box
from .event import EventBuilder


class SlackSender(Listener, threading.Thread):
    def __init__(self, *, config=None):
        Listener.__init__(self, config=config)
        threading.Thread.__init__(self)
        self._url = None
        self.csvpaths = None
        self.result = None
        self.metadata = None

    @property
    def url(self):
        if self._url is None:
            self._url = self.config._get("slack", "webhook_url")
            if self._url is not None:
                self._url = self._url.strip()
        return self._url

    def run(self):
        self._metadata_update(self.metadata)
        self.csvpaths.wrap_up()

    def metadata_update(self, mdata: Metadata) -> None:
        self.metadata = mdata
        self.start()

    def _metadata_update(self, mdata: Metadata) -> None:
        #
        # build event
        #
        event = EventBuilder(self).build(mdata)
        if event and "payload" in event:
            payload = event["payload"]
            #
            # prep request
            #
            url = None
            headers = {"Content-Type": "application/json"}
            #
            # we allow other parties -- presumably csvpath writers using
            # metadata fields -- to redirect events
            #
            if "webhook_url" in event:
                url = event["webhook_url"]
            if url is None:
                url = self.url
            #
            # send
            #
            x = requests.post(url, json=payload, headers=headers)
            if x and x.status_code != 200:
                if self.csvpaths is not None:
                    self.csvpaths.logger.info(
                        "SlackSender received status code %s from %s",
                        x.status_code,
                        url,
                    )
                elif self.result is not None:
                    self.result.csvpath.logger.info(
                        "SlackSender received status code %s from %s",
                        x.status_code,
                        url,
                    )
                else:
                    print(f"SlackSender received code {x.status_code} from {url}")
