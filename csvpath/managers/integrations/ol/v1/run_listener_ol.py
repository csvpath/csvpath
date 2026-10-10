from csvpath.managers.integrations.ol.v1.ol_listener import OpenLineageListener


class OpenLineageRunListener(OpenLineageListener):
    def __init__(self, config=None, client=None):
        super().__init__(config=config, client=client)
