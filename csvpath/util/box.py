from typing import Any
import threading

#
# just a box to put shared things in.
#
# Box is a simple thread-safe way to separate/collect things in that need to
# be reused within the thread by name. to clear, use Box.empty_my_stuff(). this
# removes everything the calling thread added to the box. CsvPaths.wrap_up()
# calls empty_my_stuff().
#
# in a server-like context threads are reused across user contexts. e.g.
# a user could fill the box in a thread, release the thread, and have the next
# unrelated user pickup the thread with all the box stuff still available, even
# though the two users shouldn't see each others stuff. that makes it important
# to remember to clear the box -- ideally before and after use.
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
