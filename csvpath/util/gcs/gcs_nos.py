# pylint: disable=C0114
import os
from google.cloud import storage
from .gcs_utils import GcsUtility
from ..path_util import PathUtility as pathu


class GcsDo:
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

    def listdir(self) -> list[str]:
        bucket, blob = GcsUtility.path_to_parts(self.path)
        # print(f"\ngcs_nos: listdir: bucket: {bucket}, blob: {blob}")
        if not blob.endswith("/"):
            blob = f"{blob}/"
        client = GcsUtility.make_client()
        bucket_obj = client.bucket(bucket)
        # print(f"gcs_nos: listdir: bucket_obj: {bucket_obj}")
        # blobs = client.list_blobs(bucket_obj, prefix=blob)
        blobs = client.list_blobs(bucket_obj, prefix=blob, delimiter="/")
        lst = [blob.name for blob in blobs]
        # print(f"gcs_nos: listdir: lst: {lst}")
        prefixes = [blob for blob in blobs.prefixes]
        # print(f"gcs_nos: listdir: prefixes: {prefixes}")
        allnames = lst + prefixes
        # print(f"gcs_nos: listdir: allnames: {allnames}")
        names = []
        for name in allnames:
            # print(f"gcs_nos: listdir: name 1: {name}")
            name = name[len(blob) :]
            # print(f"gcs_nos: listdir: name 2: {name}")
            if "/" not in name:
                names.append(name)
            else:
                names.append(name[0 : name.find("/")])
        # print(f"gcsnos: listdir: returning: {names}")
        return names

    def makedirs(self) -> None:
        # Not required for GCS
        ...

    def makedir(self) -> None:
        # Not required for GCS
        ...
