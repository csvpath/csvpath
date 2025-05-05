from openlineage.client import OpenLineageClient

from csvpath.managers.metadata import Metadata
from csvpath.managers.integrations.ol.ol_listener import OpenLineageListener


class OpenLineagePathsListener(OpenLineageListener):
    def __init__(self, config=None, client=None):
        super().__init__(config=config, client=client)
