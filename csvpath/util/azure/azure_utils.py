import os
from azure.storage.blob import BlobServiceClient, BlobClient
from csvpath.util.box import Box


class AzureUtility:
    _client_count = 0
    AZURE_STORAGE_CONNECTION_STRING = "AZURE_STORAGE_CONNECTION_STRING"

    @classmethod
    def make_client(cls):
        """Creates a BlobServiceClient."""
        box = Box()
        client = box.get(Box.AZURE_BLOB_CLIENT)
        if client is None:
            cls._client_count += 1
            connection_string = os.getenv(cls.AZURE_STORAGE_CONNECTION_STRING)
            if not connection_string:
                raise ValueError(
                    f"{cls.AZURE_STORAGE_CONNECTION_STRING} environment variable not set."
                )
            client = BlobServiceClient.from_connection_string(connection_string)
            box.add(Box.AZURE_BLOB_CLIENT, client)
        return client

    @classmethod
    def path_to_parts(cls, path) -> tuple[str, str]:
        """Splits an Azure blob path into container and blob parts."""
        if not path.startswith("azure://"):
            raise ValueError("Path must be an azure URI with the azure protocol")
        path = path[8:]
        i = path.find("/", 1)
        container = path[0:i]
        blob = path[i + 1 :]
        return container, blob

    @classmethod
    def exists(cls, container: str, blob: str) -> bool:
        client = cls.make_client()
        if client is None:
            raise ValueError("Client cannot be None")
        try:
            blob_client = client.get_blob_client(container=container, blob=blob)
            return blob_client.exists()
        except Exception:
            return False

    @classmethod
    def remove(cls, container: str, blob: str) -> None:
        client = cls.make_client()
        if client is None:
            raise ValueError("Client cannot be None")
        blob_client = client.get_blob_client(container=container, blob=blob)
        blob_client.delete_blob()

    @classmethod
    def copy(cls, container: str, blob: str, new_container: str, new_blob: str) -> None:
        client = cls.make_client()
        if client is None:
            raise ValueError("Client cannot be None")
        source_blob_client = client.get_blob_client(container=container, blob=blob)
        new_blob_client = client.get_blob_client(container=new_container, blob=new_blob)
        copy_url = source_blob_client.url
        new_blob_client.start_copy_from_url(copy_url)

    @classmethod
    def rename(
        cls, container: str, blob: str, new_container: str, new_blob: str
    ) -> None:
        """Renames a blob by copying it to a new location and deleting the old one."""
        client = cls.make_client()
        if client is None:
            raise ValueError("Client cannot be None")
        cls.copy(container, blob, container, new_blob)
        cls.remove(container, blob)
