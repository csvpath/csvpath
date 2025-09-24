from typing import Any
import threading

#
# just a box to put shared things in. separates things in the box
# by thread using thread name. use CsvPaths.wrap_up() to clear the
# box for the thread calling the method. remember that CsvPaths adds
# its config to the box, but may clear it out while others are still
# interested in it if its thread finishes before another box user.
# new threads should consider readding it as part of their own namespace.
#


class Box:
    BOTO_S3_NOS = "boto_s3_nos"
    BOTO_S3_CLIENT = "boto_s3_client"
    CSVPATHS_CONFIG = "csvpaths_config"
    SSH_CLIENT = "ssh_client"
    SFTP_CLIENT = "sftp_client"
    AZURE_BLOB_CLIENT = "azure_blob_client"
    GCS_STORAGE_CLIENT = "gcs_storage_client"
    SQL_ENGINE = "sql_engine"

    STUFF = {}

    def __str__(self) -> str:
        s = "Box: "
        for k, v in Box.STUFF.items():
            s = f"{s}\n  {k}={v}"
        return s

    @property
    def _thread(self) -> str:
        current_thread = threading.current_thread()
        return current_thread.name

    def add(self, key: str, value: Any) -> None:
        s = Box.STUFF.get(self._thread)
        if s is None:
            s = {}
            Box.STUFF[self._thread] = s
        s[key] = value

    def get(self, key: str) -> Any:
        s = Box.STUFF.get(self._thread)
        if s is None:
            s = {}
            Box.STUFF[self._thread] = s
        return s.get(key)

    def empty_my_stuff(self) -> None:
        s = Box.STUFF.get(self._thread)
        if s is None:
            return
        s = list(s.keys())[:]
        for key in s:
            self.remove(key)

    def get_my_stuff(self) -> dict:
        s = Box.STUFF.get(self._thread)
        if s is None:
            s = {}
            Box.STUFF[self._thread] = s
        return s

    def remove(self, key: str) -> None:
        s = Box.STUFF.get(self._thread)
        if s is None:
            return
        if key in s:
            del s[key]
