import os


class FileInfo:
    @classmethod
    def info(cls, path) -> dict[str, str | int | float]:
        if path is None:
            raise ValueError("Path cannot be None")
        if path.find("://") > -1:
            return cls._remote(path)
        return cls._local(path)

    @classmethod
    def _remote(cls, path):
        return {}

    @classmethod
    def _local(cls, path):
        s = os.stat(path)
        meta = {
            "mode": s.st_mode,
            "device": s.st_dev,
            "bytes": s.st_size,
            "created": s.st_ctime,
            "last_read": s.st_atime,
            "last_mod": s.st_mtime,
            "flags": s.st_flags,
        }
        return meta
