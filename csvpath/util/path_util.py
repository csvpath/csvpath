import os


class PathUtility:
    @classmethod
    def norm(cls, apath: str) -> str:
        if apath is None:
            return None
        return os.path.normpath(os.path.normcase(apath))

    @classmethod
    def equal(cls, pathone: str, pathtwo: str) -> bool:
        return cls.norm(pathone) == cls.norm(pathtwo)
