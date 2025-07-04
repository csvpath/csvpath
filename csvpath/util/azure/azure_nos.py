# pylint: disable=C0114
import os
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.storage.blob._list_blobs_helper import BlobPrefix
from .azure_utils import AzureUtility
from ..path_util import PathUtility as pathu


class AzureDo:
    def __init__(self, path, client=None):
        self._path = path

    @property
    def sep(self) -> str:
        return "/"

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, path: str) -> None:
        path = pathu.resep(path, hint="posix")
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

    def listdir(
        self,
        *,
        files_only: bool = False,
        recurse: bool = False,
        dirs_only: bool = False,
    ) -> list[str]:
        return self._listdir(
            path=self.path, files_only=files_only, recurse=recurse, dirs_only=dirs_only
        )

    def _listdir(
        self,
        *,
        path,
        files_only: bool = False,
        recurse: bool = False,
        dirs_only: bool = False,
    ) -> list[str]:
        if files_only is True and dirs_only is True:
            raise ValueError("Cannot list with neither files nor dirs")
        container, blob = AzureUtility.path_to_parts(path)
        if not blob.endswith("/"):
            blob = f"{blob}/"
        if blob == "/":
            blob = ""
        client = AzureUtility.make_client()
        container_client = client.get_container_client(container)
        blob_list = container_client.walk_blobs(name_starts_with=blob, delimiter="/")
        names = []
        for item in blob_list:
            if isinstance(item, BlobPrefix):
                if files_only is True and recurse is False:
                    name = item.name[len(blob) :]
                    names.append(name)
                elif files_only is True and recurse is True:
                    path = f"{container}/{item.name}"
                    path = path.replace("//", "/")
                    path = f"azure://{path}"
                    names += self._listdir(
                        path=path,
                        files_only=files_only,
                        recurse=recurse,
                        dirs_only=dirs_only,
                    )
                elif files_only is False and recurse is False:
                    name = item.name[len(blob) :]
                    names.append(name.rstrip("/"))
                elif files_only is False and recurse is True:
                    names.append(item.name.rstrip("/"))
                    path = f"{container}/{item.name}"
                    path = path.replace("//", "/")
                    path = f"azure://{path}"
                    names += self._listdir(
                        path=path,
                        files_only=files_only,
                        recurse=recurse,
                        dirs_only=dirs_only,
                    )
            elif dirs_only is False:
                name = item.name
                if recurse is False:
                    name = name[len(blob) :]
                names.append(name)

        return names
