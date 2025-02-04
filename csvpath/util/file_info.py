import os


class FileInfo:
    @classmethod
    def info(cls, path) -> dict[str, str | int | float]:
        if path is None:
            raise ValueError("Path cannot be None")
        try:
            if path.find("://") > -1:
                return cls._remote(path)
            return cls._local(path)
        except Exception:
            # this shouldn't happen, but it also shouldn't be the
            # main source of friction. If we have a wrong path or
            # an asset we don't know how to get info on, we'll know it
            # above and can handle it there in a more meaningful
            # context.
            return cls._empty()

    @classmethod
    def _remote(cls, path):
        return cls._empty()

    @classmethod
    def _empty(cls) -> dict:
        return {
            "mode": "",
            "device": "",
            "bytes": -1,
            "created": None,
            "last_read": None,
            "last_mod": None,
        }

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
        }
        return meta
