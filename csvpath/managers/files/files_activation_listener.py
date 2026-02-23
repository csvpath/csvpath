import requests
import threading

from abc import ABC

from csvpath import CsvPaths
from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener


class FileActivationListener(Listener, threading.Thread):
    def __init__(self, *, config=None):
        Listener.__init__(self, config=config)
        threading.Thread.__init__(self)
        self.csvpaths = None
        self.result = None
        self.metadata = None

    def run(self):
        self._metadata_update(self.metadata)
        self.csvpaths.wrap_up()

    def metadata_update(self, mdata: Metadata) -> None:
        self.metadata = mdata
        self.start()

    def _metadata_update(self, mdata: Metadata) -> None:
        csvpaths = CsvPaths()
        activator = csvpaths.file_manager.activator
        ref = mdata.named_file_ref
        csvpaths.logger.info("Activating for {ref} if any activation is configured")
        activator.activate_if(ref)
        csvpaths.logger.info("Activation for {ref} if any completed")
