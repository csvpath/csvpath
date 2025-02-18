from csvpath.managers.metadata import Metadata
from datetime import datetime


class ResultsMetadata(Metadata):
    """@private"""

    def __init__(self, config):
        super().__init__(config)
        self.time_completed: datetime = None
        self.run_home: str = None
        self.named_paths_name: str = None
        self.named_paths_uuid: str = None
        self.named_results_name: str = None
        self.named_file_uuid: str = None
        self.named_file_name: str = None
        self.named_file_path: str = None
        self.named_file_fingerprint: str = None
        self.named_file_fingerprint_on_file: str = None
        self.named_file_size: str = None
        self.named_file_last_change: str = None
        self.status: str = None
        self.all_completed: bool = None
        self.all_valid: bool = None
        self.error_count: int = None
        self.all_expected_files: bool = None
        self.by_line: bool = False

    def from_manifest(self, m) -> None:
        if m is None:
            return
        super().from_manifest(m)
        self.run_home = m["run_home"]
        self.named_paths_name = m.get("named_paths_name")
        self.named_paths_uuid = m.get("named_paths_uuid")
        self.named_file_name = m.get("named_file_name")
        self.named_file_uuid = m.get("named_file_uuid")
        self.named_file_path = m.get("named_file_path")
        self.named_file_fingerprint = m.get("named_file_fingerprint")
        self.named_file_fingerprint_on_file = m.get("")
        self.named_file_size: str = m.get("")
        self.named_file_last_change = m.get("")
        self.all_completed = m.get("all_completed")
        self.all_valid = m.get("all_valid")
        self.error_count = m.get("error_count")
        self.all_expected_files = m.get("all_expected_files")
