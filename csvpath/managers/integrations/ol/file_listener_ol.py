from csvpath.managers.integrations.ol.ol_listener import OpenLineageListener


class OpenLineageFileListener(OpenLineageListener):
    def __init__(self, config=None, client=None):
        super().__init__(config=config, client=client)
