from csvpath.managers.metadata import Metadata

from uuid import uuid4, UUID


class RunMetadata(Metadata):
    def __init__(self, config):
        super().__init__(config)
        self.run_home: str = None
        self.named_paths_name: str = None
        self.named_file_name: str = None
        self.identity: str = None
        self._run_uuid: UUID = None

    @property
    def run_uuid(self) -> UUID:
        return self._run_uuid

    @run_uuid.setter
    def run_uuid(self, u: UUID) -> None:
        if u and not isinstance(u, UUID):
            raise ValueError("Must be a UUID")
        self._run_uuid = u

    @property
    def run_uuid_string(self) -> str:
        return str(self._run_uuid)

    @run_uuid_string.setter
    def run_uuid_string(self, u: str) -> None:
        self._run_uuid = UUID(u)
