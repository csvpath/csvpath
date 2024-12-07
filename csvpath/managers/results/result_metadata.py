from uuid import UUID
from csvpath.managers.metadata import Metadata


class ResultMetadata(Metadata):
    def __init__(self, config):
        super().__init__(config)
        # these we know right away
        self._named_paths_uuid = None
        self.named_results_name: str = None
        #
        # in a non-source-mode = preceding situation the
        # named-file name is all we need. however, for source-mode
        # and by_lines runs we need the namespace + name of the
        # preceding data
        #
        self.named_file_name: str = None
        #
        # the real input file path. this may not match the named-file path
        #
        self.actual_data_file: str = None
        #
        # the input file path we would use if all instances used the named-file
        #
        self.origin_data_file: str = None
        #
        # if true actual data file is the preceding instance's data.csv
        #
        self.source_mode_preceding = None
        #
        # self if we're source mode preceding we need to know the instance
        # before us so we can construct the instancename/data.cvs ID
        #
        self.preceding_instance_identity = None
        self.run: str = None
        self.run_home: str = None
        self.instance_home: str = None
        self.instance_identity: str = None
        self.instance_index: int = None

        # these we only know at the end
        self.file_count: int = -1
        self.file_fingerprints: dict[str, str] = None
        self.valid: bool = None
        self.completed: bool = None
        self.files_expected: bool = None
        self.error_count: int = -1
        self.by_line: bool = False
        #
        # transfer tuples:
        # 1: filename, no extension needed: data | unmatched
        # 2: variable name containing the path to write to
        # 3: path of source file
        # 3: path to write to
        #
        self.transfers: tuple[str, str, str, str] = None

    def __str__(self) -> str:
        return f"""
ResultMetadata(
  {self.uuid}{self.named_paths_uuid},
  {self.named_results_name},{self.named_file_name},{self.run},{self.instance_identity},{self.by_line},
  {self.run_home},{self.instance_home},
  {self.input_data_file},
  {self.file_fingerprints},
  {self.valid},{self.completed},{self.files_expected},{self.error_count},{self.file_count},
  {self.transfers}
)"""

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
        #
        # this is seen in testing
        #
        if u is None:
            return
        if u and not isinstance(u, str):
            raise ValueError("Must be a string")
        self._named_paths_uuid = UUID(u)
