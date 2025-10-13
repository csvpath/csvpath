import sys
import os


class PyFileUtility:
    @classmethod
    def filepath(cls, t) -> str:
        return os.path.abspath(sys.modules[t.__class__.__module__].__file__)
