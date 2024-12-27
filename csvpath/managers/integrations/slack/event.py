from datetime import datetime
import os
import json
from pathlib import Path
import textwrap
from tabulate import tabulate

from csvpath.managers.metadata import Metadata
from csvpath.managers.results.results_metadata import ResultsMetadata
from csvpath.managers.results.result_metadata import ResultMetadata
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.run.run_metadata import RunMetadata
from csvpath.managers.results.result_file_reader import ResultFileReader


class Event(dict):
    pass


class EventBuilder:
    def __init__(self, sender) -> None:
        self.sender = sender

    def _get(self, key: str, default: str = None) -> str:
        ret = default
        if self.sender is not None and key in self.sender.metadata:
            ret = self.sender.metadata[key]
        return f"{key} is unavailable" if ret is None else ret

    def build(self, mdata: Metadata) -> list[Event]:
        if isinstance(mdata, ResultsMetadata):
            return self._build_results_event(mdata)
        elif isinstance(mdata, ResultMetadata):
            return self._build_result_event(mdata)
        elif isinstance(mdata, PathsMetadata):
            return self._build_paths_event(mdata)
        elif isinstance(mdata, FileMetadata):
            return self._build_file_event(mdata)
        elif isinstance(mdata, RunMetadata):
            return None

    def _build_results_event(self, mdata: Metadata) -> Event:
        #
        # easier to load the manifest than serialize the metadata. maybe fix that.
        #
        mani = ResultFileReader.json_file(mdata.manifest_path)
        event = Event()
        event["payload"] = {}
        headers = ["Key", "Value"]
        rows = []
        for k, v in mani.items():
            headers.append(k)
            v = str(v)
            if len(v) > 35:
                v = textwrap.fill(v, width=35)
            rows.append([k, v])
        text = f"""{tabulate(rows, headers=headers, tablefmt='simple_grid')}"""
        blocks = []
        blocks.append(
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"""{mdata.named_results_name} completed.""",
                },
            }
        )
        blocks.append(
            {
                "type": "rich_text",
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [
                            {
                                "type": "text",
                                "text": "The results manifest is as follows.",
                                "style": {"italic": True},
                            }
                        ],
                    }
                ],
            }
        )
        blocks.append({"type": "divider"})
        blocks.append(
            {
                "type": "rich_text",
                "elements": [
                    {
                        "type": "rich_text_preformatted",
                        "elements": [{"type": "text", "text": text}],
                    }
                ],
            }
        )
        event["payload"]["blocks"] = blocks
        return event

    def _build_result_event(self, mdata: Metadata):
        #
        # manifest_path will be none when the run starts and
        # not none when it ends.
        #
        if mdata.manifest_path is not None:
            event = Event()
            #
            # if not valid we check if the user put an 'on-invalid-slack' metadata
            # value. otherwise 'on-valid-slack'. if they did we'll use that as
            # the webhook url. the value cannot start with https:// because of the
            # colon in the protocol. we'll add that as a prefix.
            #
            if mdata.valid is False:
                # original but deprecated. prefer the slack namespace first to match other
                # integrations with more metadata needs
                invalid = self.sender.result.csvpath.metadata.get("on-invalid-slack")
                if invalid is None:
                    invalid = self.sender.result.csvpath.metadata.get(
                        "slack-on-invalid"
                    )
                if invalid is not None:
                    event["webhook_url"] = f"https://{invalid}"
            else:
                # original but deprecated. prefer the slack namespace first to match other
                # integrations with more metadata needs
                valid = self.sender.result.csvpath.metadata.get("on-valid-slack")
                if valid is None:
                    valid = self.sender.result.csvpath.metadata.get("slack-on-valid")
                if valid is not None:
                    event["webhook_url"] = f"https://{valid}"
            mani = ResultFileReader.json_file(mdata.manifest_path)
            event["payload"] = {}
            headers = ["Key", "Value"]
            rows = []
            for k, v in mani.items():
                headers.append(k)
                v = str(v)
                if len(v) > 35:
                    v = textwrap.fill(v, width=35)
                rows.append([k, v])
            text = f"""{tabulate(rows, headers=headers, tablefmt='simple_grid')}"""
            blocks = []
            blocks.append(
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"""Group:{mdata.named_results_name}.Instance:{mdata.instance_identity} completed.""",
                    },
                }
            )
            blocks.append(
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": "The results manifest is as follows.",
                                    "style": {"italic": True},
                                }
                            ],
                        }
                    ],
                }
            )
            blocks.append({"type": "divider"})
            blocks.append(
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_preformatted",
                            "elements": [{"type": "text", "text": text}],
                        }
                    ],
                }
            )
            event["payload"]["blocks"] = blocks
            return event

    def _build_paths_event(self, mdata: Metadata):
        event = Event()
        return event

    def _build_file_event(self, mdata: Metadata):
        event = Event()
        return event
