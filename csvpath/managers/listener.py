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

    def raise_on_update_error(self) -> bool:
        """True if an exception from metadata_update should propagate out
        of Registrar.distribute_update instead of only being logged. most
        listeners are integrations whose failures must not stop a run, so
        the default is False."""
        return False

    def update_is_required(self) -> bool:
        """True if a failed metadata_update must stop the flow regardless
        of the error policy. Registrar.distribute_update raises a
        RequiredListenerException, which do_i_raise(ex) always raises."""
        return False

    def metadata_patch(self, mdata: Metadata) -> None:
        """a change to an existing manifest entry, e.g. a named-file's type
        or file name, rather than a new registration. Registrar.distribute_patch
        calls the primary registrar first, which applies the patch and sets
        mdata.manifest_entry to the patched entry; listeners that mirror
        manifests then update their copy. the default is to ignore patches,
        because most listeners report events and a patch is not one."""
        return None

    @abstractmethod
    def metadata_update(self, mdata: Metadata) -> None:
        """any system that wants updates about a registrar or manager registers to
        receive updates. for e.g. an OpenLineage integration might register for
        named-results and other metadata to track jobs and datasets. the first
        registrar in the list of metadata receivers must be CsvPath Library's own
        registrar, which is also the source of the metadata that is shared."""
