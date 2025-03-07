from typing import Any

#
# just a box to put things in. initial use is
# sharing a boto3 client under "boto_s3_client".
# sftp also needs it.
#
# can be used as a context mgr, but be careful
# that you don't empty someone else's box stuff.
#


class Box:
    BOTO_S3_NOS = "boto_s3_nos"
    BOTO_S3_CLIENT = "boto_s3_client"
    CSVPATHS_CONFIG = "csvpaths_config"
    SSH_CLIENT = "ssh_client"
    SFTP_CLIENT = "sftp_client"
    AZURE_BLOB_CLIENT = "azure_blob_client"
    GCS_STORAGE_CLIENT = "gcs_storage_client"

    STUFF = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        Box.STUFF = {}

    def add(self, key: str, value: Any) -> None:
        Box.STUFF[key] = value

    def get(self, key: str):
        return Box.STUFF.get(key)
