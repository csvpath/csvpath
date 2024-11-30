from csvpath.managers.metadata import Metadata


class ResultsMetadata(Metadata):
    def __init__(self):
        super().__init__()
        self.time_completed: str = None
        self.run_home: str = None
        self.named_paths_name: str = None
        self.named_file_name: str = None
        self.named_file_path: str = None
        self.named_file_fingerprint: str = None

        self.named_file_fingerprint_on_file: str = None
        self.named_file_size: str = None
        self.named_file_last_change: str = None

        self.all_completed: bool = None
        self.all_valid: bool = None
        self.error_count: int = None
        self.all_expected_files: bool = None
