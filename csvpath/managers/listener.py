from abc import ABC, abstractmethod
from .metadata import Metadata


class Listener(ABC):
    def __init__(self, config=None) -> None:
        self.config = config

    @abstractmethod
    def metadata_update(self, mdata: Metadata) -> None:
        """any system that wants updates about a registrar's actions registers to
        receive updates. for e.g. an OpenLineage integration might register for
        named-results and other metadata to track jobs and datasets. the first
        registrar in the list of metadata receivers must be CsvPath Library's own
        registrar, which is also the source of the metadata that is shared."""
        pass
