# pylint: disable=C0114
import os
from google.cloud import storage
from .gcs_utils import GcsUtility
from ..path_util import PathUtility as pathu


class GcsDo:
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
        bucket, blob = GcsUtility.path_to_parts(self.path)
        lst = self.listdir()
        for item in lst:
            self.path = f"gs://{bucket}/{blob}/{item}"
            self.remove()
        if GcsUtility.exists(bucket, blob):
            GcsUtility.remove(bucket, blob)

    def exists(self) -> bool:
        bucket, blob = GcsUtility.path_to_parts(self.path)
        return GcsUtility.exists(bucket, blob)

    def rename(self, new_path: str) -> None:
        bucket, blob = GcsUtility.path_to_parts(self.path)
        new_bucket, new_blob = GcsUtility.path_to_parts(new_path)
        return GcsUtility.rename(bucket, blob, new_bucket, new_blob)

    def copy(self, new_path: str) -> None:
        bucket, blob = GcsUtility.path_to_parts(self.path)
        new_bucket, new_blob = GcsUtility.path_to_parts(new_path)
        return GcsUtility.copy(bucket, blob, new_bucket, new_blob)

    def isfile(self) -> bool:
        bucket, blob = GcsUtility.path_to_parts(self.path)
        client = GcsUtility.make_client()
        try:
            bucket_obj = client.bucket(bucket)
            blob_obj = bucket_obj.blob(blob)
            return blob_obj.exists()
        except Exception:
            return False

    def dir_exists(self) -> bool:
        lst = self.listdir()
        #
        # Similar to Azure, we consider a directory to exist if there are blobs under its prefix.
        #
        return bool(lst)

    def physical_dirs(self) -> bool:
        return False

    def makedirs(self) -> None:
        # Not required for GCS
        ...

    def makedir(self) -> None:
        # Not required for GCS
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
        bucket, blob = GcsUtility.path_to_parts(path)
        if not blob.endswith("/") and blob.strip() != "":
            blob = f"{blob}/"
        client = GcsUtility.make_client()
        bucket_obj = client.bucket(bucket)
        blobs = client.list_blobs(bucket_obj, prefix=blob, delimiter="/")

        names = []
        for b in blobs:
            if dirs_only is False:
                name = b.name
                if recurse is True:
                    names.append(name)
                else:
                    name = name[len(blob) :]
                    i = name.find("/")
                    if i > -1:
                        name = name[0:i]
                    names.append(name)

        for prefix in blobs.prefixes:
            if files_only is True and recurse is True:
                path = f"{bucket}/{prefix}/"
                path = path.replace("//", "/")
                path = f"gs://{path}"
                names += self._listdir(
                    path=path,
                    files_only=files_only,
                    recurse=recurse,
                    dirs_only=dirs_only,
                )
            if files_only is True and recurse is False:
                continue
            if files_only is False and recurse is True:
                names.append(prefix.rstrip("/"))
                path = f"{bucket}/{prefix}"
                path = path.replace("//", "/")
                path = f"gs://{path}"
                names += self._listdir(
                    path=path,
                    files_only=files_only,
                    recurse=recurse,
                    dirs_only=dirs_only,
                )
            if files_only is False and recurse is False:
                prefix = prefix[len(blob) :]
                names.append(prefix.rstrip("/"))

        return names
