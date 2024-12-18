from csvpath.managers.metadata import Metadata
from .sender import Sender


class OpenLineageListener(Sender):
    def __init__(self, config=None, client=None):
        super().__init__(config=config, client=client)
