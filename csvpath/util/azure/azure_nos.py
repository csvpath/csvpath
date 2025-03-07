# pylint: disable=C0114
import os
from azure.storage.blob import BlobServiceClient, ContainerClient
from .azure_utils import AzureUtility
from ..path_util import PathUtility as pathu


class AzureDo:
    def __init__(self, path, client=None):
        self._path = path

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, path: str) -> None:
        path = pathu.resep(path)
        self._path = path

    def remove(self) -> None:
        container, blob = AzureUtility.path_to_parts(self.path)
        lst = self.listdir()
        for item in lst:
            self.path = f"azure://{container}/{blob}/{item}"
            self.remove()
        if AzureUtility.exists(container, blob):
            AzureUtility.remove(container, blob)

    def exists(self) -> bool:
        container, blob = AzureUtility.path_to_parts(self.path)
        return AzureUtility.exists(container, blob)

    def dir_exists(self) -> bool:
        lst = self.listdir()
        #
        # can we say a dir doesn't exist if it's empty? we do in S3 but
        # it is a bit odd because dirs aren't a thing exactly. :/
        #
        return bool(lst)

    def physical_dirs(self) -> bool:
        return False

    def rename(self, new_path: str) -> None:
        container, blob = AzureUtility.path_to_parts(self.path)
        new_container, new_blob = AzureUtility.path_to_parts(new_path)
        return AzureUtility.rename(container, blob, new_container, new_blob)

    def copy(self, new_path: str) -> None:
        container, blob = AzureUtility.path_to_parts(self.path)
        new_container, new_blob = AzureUtility.path_to_parts(new_path)
        return AzureUtility.copy(container, blob, new_container, new_blob)

    def listdir(self) -> list[str]:
        container, blob = AzureUtility.path_to_parts(self.path)
        if not blob.endswith("/"):
            blob = f"{blob}/"
        client = AzureUtility.make_client()
        container_client = client.get_container_client(container)
        blob_list = container_client.walk_blobs(name_starts_with=blob, delimiter="/")
        names = []
        for item in blob_list:
            name = item.name[len(blob) :]
            if "/" not in name:  # Only include direct children
                names.append(name)
            else:
                names.append(name.rstrip("/"))
        return names

    def isfile(self) -> bool:
        container, blob = AzureUtility.path_to_parts(self.path)
        client = AzureUtility.make_client()
        try:
            blob_client = client.get_blob_client(container=container, blob=blob)
            return blob_client.exists()
        except Exception:
            return False

    def makedirs(self) -> None:
        # seems not needed
        ...

    def makedir(self) -> None:
        # seems not needed
        ...
