import os
from google.cloud import storage
from csvpath.util.box import Box


class GcsUtility:
    _client_count = 0
    GCS_CREDENTIALS_PATH = "GCS_CREDENTIALS_PATH"

    @classmethod
    def make_client(cls):
        """Creates a GCS Storage Client."""
        box = Box()
        client = box.get(Box.GCS_STORAGE_CLIENT)
        if client is None:
            cls._client_count += 1
            credentials_path = os.getenv(cls.GCS_CREDENTIALS_PATH)
            if not credentials_path:
                raise ValueError(
                    f"{cls.GCS_CREDENTIALS_PATH} environment variable not set."
                )
            client = storage.Client.from_service_account_json(credentials_path)
            box.add(Box.GCS_STORAGE_CLIENT, client)
        return client

    @classmethod
    def path_to_parts(cls, path) -> tuple[str, str]:
        """Splits a GCS blob path into bucket and blob parts."""
        if not path.startswith("gs://"):
            raise ValueError("Path must be a GCS URI with the gs protocol")
        path = path[5:]
        i = path.find("/", 1)
        bucket = path[0:i]
        blob = path[i + 1 :]
        return bucket, blob

    @classmethod
    def exists(cls, bucket: str, blob: str) -> bool:
        client = cls.make_client()
        if client is None:
            raise ValueError("Client cannot be None")
        try:
            bucket_obj = client.bucket(bucket)
            blob_obj = bucket_obj.blob(blob)
            return blob_obj.exists()
        except Exception:
            return False

    @classmethod
    def remove(cls, bucket: str, blob: str) -> None:
        client = cls.make_client()
        if client is None:
            raise ValueError("Client cannot be None")
        bucket_obj = client.bucket(bucket)
        blob_obj = bucket_obj.blob(blob)
        blob_obj.delete()

    @classmethod
    def copy(cls, bucket: str, blob: str, new_bucket: str, new_blob: str) -> None:
        client = cls.make_client()
        if client is None:
            raise ValueError("Client cannot be None")
        bucket_obj = client.bucket(bucket)
        blob_obj = bucket_obj.blob(blob)
        new_bucket_obj = client.bucket(new_bucket)
        new_blob_obj = new_bucket_obj.blob(new_blob)
        new_blob_obj.rewrite(blob_obj)

    @classmethod
    def rename(cls, bucket: str, blob: str, new_bucket: str, new_blob: str) -> None:
        """Renames a blob by copying it to a new location and deleting the old one."""
        cls.copy(bucket, blob, new_bucket, new_blob)
        cls.remove(bucket, blob)
