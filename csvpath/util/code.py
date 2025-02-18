import os
import inspect
from typing import Type, Any


class Code:
    @classmethod
    def get_source_path(cls, class_to_find: Type[Any]) -> str:
        source_file = inspect.getsourcefile(class_to_find)
        if source_file:
            ap = os.path.abspath(source_file)
            return ap
        else:
            return None

    @classmethod
    def get_source_dir(cls, class_to_find: Type[Any]) -> str:
        path = cls.get_source_path(class_to_find)
        if path is not None:
            path = os.path.dirname(path)
        return path
