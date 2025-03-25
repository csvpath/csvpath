from csvpath.managers.metadata import Metadata


class PathsMetadata(Metadata):
    """@private"""

    def __init__(self, config):
        super().__init__(config)
        self.named_paths_name: str = None
        self.named_paths_home: str = None
        self.group_file_path: str = None
        self.named_paths_count: int = -1
        self.named_paths_identities: list[str] = None
        self.named_paths: list[str] = None
        self.source_path: str = None
        self.template: str = None
