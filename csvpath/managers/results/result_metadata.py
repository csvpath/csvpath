import uuid
from datetime import datetime
from csvpath.managers.metadata import Metadata


class ResultMetadata(Metadata):
    def __init__(self):
        super().__init__()
        self.archive_name: str = None
        self.named_results_name: str = None
        self.instance: str = None
        self.instance_dir: str = None
        self.identity: str = None
        self.identity_home: str = None
        self.input_data_file: str = None
        self.file_count: int = -1
        self.file_fingerprints: dict[str, str] = None
        self.valid: bool = None
        self.completed: bool = None
        self.files_expected: bool = None
        self.transfers: tuple[str, str] = None
