import requests
from abc import ABC
from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener
from .event import EventBuilder


class SlackSender(Listener):
    def __init__(self, *, config=None):
        super().__init__(config)
        self._url = None
        self.csvpaths = None
        self.result = None

    @property
    def url(self):
        if self._url is None:
            self._url = self.config._get("slack", "webhook_url")
            if self._url is not None:
                self._url = self._url.strip()
        return self._url

    def metadata_update(self, mdata: Metadata) -> None:
        print(f"mdataupdate: sending to slack on {self.url}")
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
            else:
                url = self._url
            #
            # send
            #
            x = requests.post(url, json=payload, headers=headers)
            print(f"mdataupdate: x: {x}")
            print(f"mdataupdate: content: {x.content}")
