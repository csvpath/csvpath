from openlineage.client import OpenLineageClient

from ..metadata import Metadata
from ..ol.event import EventBuilder
from ..ol.sender import Sender
from ..ol.ol_listener import OpenLineageListener


class OpenLineagePathsListener(OpenLineageListener):
    def __init__(self, config=None, client=None):
        super().__init__(config=config, client=client)
