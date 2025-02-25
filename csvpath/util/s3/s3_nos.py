# pylint: disable=C0114
import os
import boto3
from botocore.exceptions import ClientError
from .s3_utils import S3Utils
from csvpath.util.box import Box


class S3Do:
    def __init__(self, path, client=None):
        self._path = path
        self._client = client

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, p: str) -> None:
        self._path = p

    @property
    def client(self):
        if self._client is None:
            self._client = Box.STUFF.get(Box.BOTO_S3_CLIENT)
            if self._client is None:
                self._client = S3Utils.make_client()
                Box().add(Box.BOTO_S3_CLIENT, self._client)
        return self._client

    def remove(self) -> None:
        bucket, key = S3Utils.path_to_parts(self.path)
        lst = self.listdir()
        for item in lst:
            self.path = f"s3://{bucket}/{key}/{item}"
            self.remove()
        S3Utils.remove(bucket, key, client=self.client)

    def exists(self) -> bool:
        bucket, key = S3Utils.path_to_parts(self.path)
        ret = S3Utils.exists(bucket, key, client=self.client)
        return ret

    def dir_exists(self) -> bool:
        lst = self.listdir()
        if lst and len(lst) > 0:
            return True

    def rename(self, new_path: str) -> None:
        bucket, key = S3Utils.path_to_parts(self.path)
        same_bucket, new_key = S3Utils.path_to_parts(new_path)
        if bucket != same_bucket:
            raise ValueError(
                "The old path and the new location must have the same bucket"
            )
        return S3Utils.rename(bucket, key, new_key, client=self.client)

    def copy(self, new_path) -> None:
        bucket, key = S3Utils.path_to_parts(self.path)
        new_bucket, new_key = S3Utils.path_to_parts(new_path)
        return S3Utils.copy(bucket, key, new_bucket, new_key, client=self.client)

    def makedirs(self) -> None:
        # may not be needed?
        ...

    def makedir(self) -> None:
        # may not be needed?
        ...

    def listdir(self) -> list[str]:
        bucket, key = S3Utils.path_to_parts(self.path)
        if not key.endswith("/"):
            key = f"{key}/"
        prefix = key
        client = self.client
        # client = boto3.client("s3")
        # client = S3Utils.make_client()
        #
        # boto3 uses a deprecated feature. pytest doesn't like it. this is a quick fix.
        #
        import warnings

        warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")
        ##
        result = client.list_objects(Bucket=bucket, Prefix=prefix, Delimiter="/")
        names = []
        # if result has direct children they are in contents
        lst = result.get("Contents")
        if lst is not None:
            for o in lst:
                nkey = o["Key"]
                name = nkey[nkey.rfind("/") + 1 :]
                names.append(name)
        # if result is for an intermediate dir with or without direct children
        # the notional child directories are in common prefixes.
        lst = result.get("CommonPrefixes")
        if lst is not None:
            for o in lst:
                nkey = o["Prefix"]
                nkey = nkey[0 : len(nkey) - 1] if len(nkey) > 0 else nkey
                name = nkey[nkey.rfind("/") + 1 :]
                if name.strip() != "":
                    names.append(name)
        return names

    def isfile(self) -> bool:
        bucket, key = S3Utils.path_to_parts(self.path)
        client = self.client
        #
        # boto3 uses a deprecated feature. pytest doesn't like it. this is a quick fix.
        #
        import warnings

        warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")
        try:
            client.head_object(Bucket=bucket, Key=key)
        except ClientError as e:
            assert str(e).find("404") > -1
            return False
        return True
