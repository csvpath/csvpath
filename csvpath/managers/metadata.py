from uuid import uuid4, UUID
import os
from abc import ABC
from datetime import datetime, timezone
from dateutil import parser
import getpass
import socket


class Metadata(ABC):
    def __init__(self, config):
        self.config = config
        #
        # fields
        #
        self.set_time()
        self._time_started: datetime = None
        self._time_completed: datetime = None
        self._uuid = uuid4()
        self.manifest_path: str = None
        self.archive_name: str = None
        self.archive_path: str = None
        self._base_path = None
        self._named_files_root: str = None
        self._named_paths_root: str = None
        self.username = None
        try:
            self.username = getpass.getuser()
        except Exception:
            ...
        self.hostname = None
        self.ip_address = None
        try:
            self.hostname = socket.gethostname()
            self.ip_address = socket.gethostbyname(self.hostname)
        except Exception:
            ...
        if config:
            self.archive_name = config.archive_name
            self.archive_path = config.archive_path

    #
    # find base dir so we can add file:// refs, if needed
    #
    @property
    def base_path(self):
        if self._base_path is None:
            self._base_path = os.getcwd()
        return self._base_path

    @property
    def named_files_root(self):
        if self._named_files_root is None:
            self._named_files_root = self.config.inputs_files_path
        return self._named_files_root

    @property
    def named_paths_root(self):
        if self._named_paths_root is None:
            self._named_paths_root = self.config.inputs_csvpaths_path
        return self._named_paths_root

    def from_manifest(self, m) -> None:
        if m is None:
            return
        if m.get("time") is not None:
            self.time_string = m.get("time")
        if m.get("time_started") is not None:
            self.time_started_string = m.get("time_started")
        if m.get("time_completed") is not None:
            self.time_completed_string = m.get("time_completed")
        if m.get("uuid") is not None:
            self.uuid_string = m.get("uuid")
        if m.get("manifest_path") is not None:
            self.manifest_path = m.get("manifest_path")
        if m.get("archive_name") is not None:
            self.archive_name = m.get("archive_name")
        if m.get("archive_path") is not None:
            self.archive_path = m.get("archive_path")

    @property
    def uuid(self) -> UUID:
        return self._uuid

    @uuid.setter
    def uuid(self, u: UUID) -> None:
        if u and not isinstance(u, UUID):
            raise ValueError("Must be a UUID")
        self._uuid = u

    @property
    def uuid_string(self) -> str:
        return str(self._uuid)

    @uuid_string.setter
    def uuid_string(self, u: str) -> None:
        self._uuid = UUID(u)

    def set_time(self) -> None:
        self._time = datetime.now(timezone.utc)

    def set_time_started(self) -> None:
        self._time_started = datetime.now(timezone.utc)

    def set_time_completed(self) -> None:
        self._time_completed = datetime.now(timezone.utc)

    @property
    def time(self) -> datetime:
        return self._time

    @time.setter
    def time(self, t: datetime) -> None:
        if t and not isinstance(t, datetime):
            raise ValueError("Must be a datetime")
        self._time = t

    @property
    def time_string(self) -> str:
        return self._time.isoformat() if self.time else None

    @time_string.setter
    def time_string(self, s: str) -> None:
        if not isinstance(s, str):
            raise ValueError("Time string must be a string")
        self._time = parser.parse(s)

    @property
    def time_started(self) -> datetime:
        return self._time_started

    @time_started.setter
    def time_started(self, t: datetime) -> None:
        if t and not isinstance(t, datetime):
            raise ValueError("Must be a datetime")
        self._time_started = t

    @property
    def time_started_string(self) -> datetime:
        return self._time_started.isoformat() if self.time_started else None

    @time_started_string.setter
    def time_started_string(self, s: str) -> None:
        # self._time_started = datetime.date.fromisoformat(s)
        self._time_started = parser.parse(s)

    @property
    def time_completed_string(self) -> datetime:
        return self._time_completed.isoformat() if self.time_completed else None

    @time_completed_string.setter
    def time_completed_string(self, s: str) -> None:
        self._time_completed = parser.parse(s)

    @property
    def time_completed(self) -> datetime:
        return self._time_completed

    @time_completed.setter
    def time_completed(self, t: datetime) -> None:
        if t and not isinstance(t, datetime):
            raise ValueError("Must be a datetime")
        self._time_completed = t
