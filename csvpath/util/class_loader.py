import importlib
from typing import Any
from csvpath.util.config_exception import ConfigurationException


class ClassLoader:
    @classmethod
    def load(cls, s: str, args: list = None, kwargs: dict = None) -> Any:
        s = s.strip()
        if s != "":
            instance = None
            cs = s.split(" ")
            #
            # lines in config are like:
            #   from module import class
            #
            if len(cs) == 4 and cs[0] == "from" and cs[2] == "import":
                module = importlib.import_module(cs[1])
                class_ = getattr(module, cs[3])
                args = args if args is not None else []
                kwargs = kwargs if kwargs is not None else {}
                instance = class_(*args, **kwargs)
                return instance
            else:
                raise ConfigurationException(
                    f"Unclear class loading import statement: {s}"
                )
        return None
