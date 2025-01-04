import os


class FileInfo:
    @classmethod
    def info(self, path) -> dict[str, str | int | float]:
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
