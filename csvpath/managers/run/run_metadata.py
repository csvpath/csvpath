from csvpath.managers.metadata import Metadata


class RunMetadata(Metadata):
    def __init__(self, config):
        super().__init__(config)
        self.run_home: str = None
        self.named_paths_name: str = None
        self.named_file_name: str = None
        self.identity: str = None
