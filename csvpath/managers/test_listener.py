from .metadata import Metadata
from .listener import Listener


class TestListener(Listener):
    #
    # can capture this metadata for replay in testing
    #
    METADATA = None

    def __init__(self, config=None) -> None:
        self._config = None
        super().__init__(config)
        self.mine = None

    def metadata_update(self, mdata: Metadata) -> None:
        TestListener.METADATA = mdata
        self.mine = mdata
