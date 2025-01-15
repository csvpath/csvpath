# pylint: disable=C0114
import os
import shutil
import boto3
from botocore.exceptions import ClientError
from .s3.s3_utils import S3Utils
from pathlib import Path


class Nos:
    def __init__(self, path):
        self.path = path
        self._do = None

    @property
    def do(self):
        if self.path is not None and self._do is None:
            if self.path.startswith("s3://"):
                self._do = S3Do(self.path)
            else:
                self._do = FileDo(self.path)
        return self._do

    @property
    def sep(self) -> str:
        return "/" if self.path.find("\\") == -1 else os.sep

    def join(self, name: str) -> str:
        return self.do.join(name)

    def remove(self) -> None:
        self.do.remove()

    def exists(self) -> bool:
        self.do
        return self.do.exists()

    def dir_exists(self) -> bool:
        return self.do.dir_exists()

    def rename(self, new_path: str) -> None:
        self.do.rename(new_path)

    def copy(self, new_path) -> None:
        self.do.copy(new_path)

    def makedirs(self) -> None:
        self.do.makedirs()

    def makedir(self) -> None:
        self.do.makedir()

    def listdir(self) -> list[str]:
        return self.do.listdir()

    def isfile(self) -> bool:
        return self.do.isfile()


class S3Do:
    def __init__(self, path):
        self.path = path

    def remove(self) -> None:
        bucket, key = S3Utils.path_to_parts(self.path)
        lst = self.listdir()
        for item in lst:
            Nos(f"s3://{bucket}/{key}/{item}").remove()
        S3Utils.remove(bucket, key)

    def exists(self) -> bool:
        bucket, key = S3Utils.path_to_parts(self.path)
        ret = S3Utils.exists(bucket, key)
        return ret

    def dir_exists(self) -> bool:
        lst = self.listdir()
        if lst and len(lst) > 0:
            return True
        return False

    def rename(self, new_path: str) -> None:
        bucket, key = S3Utils.path_to_parts(self.path)
        same_bucket, new_key = S3Utils.path_to_parts(new_path)
        if bucket != same_bucket:
            raise ValueError(
                "The old path and the new location must have the same bucket"
            )
        return S3Utils.rename(bucket, key, new_key)

    def copy(self, new_path) -> None:
        bucket, key = S3Utils.path_to_parts(self.path)
        new_bucket, new_key = S3Utils.path_to_parts(new_path)
        return S3Utils.copy(bucket, key, new_bucket, new_key)

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
        client = boto3.client("s3")

        #
        # boto3 uses a deprecated feature. pytest doesn't like it. this is a quick fix.
        #
        import warnings

        warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

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
        client = boto3.client("s3")
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


class FileDo:
    def __init__(self, path):
        self.path = path

    def remove(self) -> None:
        if os.path.isfile(self.path):
            os.remove(self.path)
        else:
            shutil.rmtree(self.path)

    def copy(self, to) -> None:
        shutil.copy(self.path, to)

    def exists(self) -> bool:
        return os.path.exists(self.path)

    def dir_exists(self) -> bool:
        return os.path.exists(self.path)

    def rename(self, new_path: str) -> None:
        os.rename(self.path, new_path)

    def makedirs(self) -> None:
        os.makedirs(self.path)

    def makedir(self) -> None:
        Path(self.path).mkdir(parents=True, exist_ok=True)

    def listdir(self) -> list[str]:
        return os.listdir(self.path)

    def isfile(self) -> bool:
        return os.path.isfile(self.path)
