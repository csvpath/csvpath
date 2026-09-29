from csvpath.util.config import Config
from .proxy_listener_ol import OpenLineageListenerProxy


class OpenLineagePathsListener(OpenLineageListenerProxy):
    def __init__(self, config=None, client=None):
        super().__init__(config=config, client=client)

    def __new__(cls, *, config: Config):
        if config is None:
            raise ValueError("Config cannot be None")
        if cls == OpenLineagePathsListener:
            return cls._load(
                config=config,
                sig="from csvpath.managers.integrations.ol.v{version}.paths_listener_ol import OpenLineagePathsListener",
            )
        else:
            instance = super().__new__(cls)
            return instance
