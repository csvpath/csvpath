from abc import ABC, abstractmethod
from .metadata import Metadata
from ..util.config import Config


class Listener(ABC):
    def __init__(self, config=None) -> None:
        self._config = None
        super().__init__()
        self.config = config

    @property
    def config(self):
        if self._config is None:
            #
            # this really should never happen. but perhaps in testing?
            #
            self._config = Config()
        return self._config

    @config.setter
    def config(self, c):
        self._config = c

    @abstractmethod
    def metadata_update(self, mdata: Metadata) -> None:
        """any system that wants updates about a registrar or manager registers to
        receive updates. for e.g. an OpenLineage integration might register for
        named-results and other metadata to track jobs and datasets. the first
        registrar in the list of metadata receivers must be CsvPath Library's own
        registrar, which is also the source of the metadata that is shared."""
