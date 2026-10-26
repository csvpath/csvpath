from csvpath.managers.metadata import Metadata


class PathsMetadata(Metadata):
    """@private"""

    def __init__(self, config):
        super().__init__(config)
        self.named_paths_name: str = None
        self.named_paths_home: str = None
        self.group_file_path: str = None
        self.named_paths_count: int = 0
        self.named_paths_identities: list[str] = None
        self.named_paths: list[str] = None
        self.source_path: str = None
        self.template: str = None
        #
        # set only for an unchanged reload: status is
        # PathsRegistrar.UNCHANGED and version_uuid is the version the
        # load matched. both go into the root ledger entry.
        #
        self.status: str | None = None
        self.version_uuid: str | None = None
        #
        # TODO: make sure append is in manifests
        #
        self.append: bool = None
