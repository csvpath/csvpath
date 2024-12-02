from uuid import UUID
from csvpath.managers.metadata import Metadata


class ResultMetadata(Metadata):
    def __init__(self):
        super().__init__()
        # these we know right away
        self._named_paths_uuid = None
        self.named_results_name: str = None
        self.named_file_name: str = None
        self.run: str = None
        self.run_home: str = None
        self.instance_home: str = None
        self.instance_identity: str = None
        self.input_data_file: str = None
        # these we only know at the end
        self.file_count: int = -1
        self.file_fingerprints: dict[str, str] = None
        self.valid: bool = None
        self.completed: bool = None
        self.files_expected: bool = None
        self.error_count: int = -1
        self.transfers: tuple[str, str] = None

    def from_manifest(self, m) -> None:
        if m is None:
            return
        super().from_manifest(m)
        self.named_paths_uuid_string = m.get("named_paths_uuid")
        self.named_results_name = m.get("named_results_name")
        self.named_file_name = m.get("named_file_name")
        self.run = m.get("run")
        self.run_home = m.get("run_home")
        self.instance_home = m.get("instance_home")
        self.instance_identity = m.get("instance_identity")
        self.input_data_file = m.get("input_data_file")
        self.file_count = m.get("file_count")
        self.file_fingerprints = m.get("file_fingerprints")
        self.valid = m.get("valid")
        self.completed = m.get("completed")
        self.files_expected = m.get("files_expected")
        self.error_count = m.get("error_count")
        self.transfers = m.get("transfers")

    @property
    def named_paths_uuid(self) -> UUID:
        return self._named_paths_uuid

    @named_paths_uuid.setter
    def named_paths_uuid(self, u: UUID) -> None:
        if u and not isinstance(u, UUID):
            raise ValueError("Must be a UUID")
        self._named_paths_uuid = u

    @property
    def named_paths_uuid_string(self) -> str:
        if self._named_paths_uuid is None:
            return None
        return str(self._named_paths_uuid)
        # return self._named_paths_uuid.hex

    @named_paths_uuid_string.setter
    def named_paths_uuid_string(self, u: str) -> None:
        if u and not isinstance(u, str):
            raise ValueError("Must be a string")
        self._named_paths_uuid = UUID(u)
