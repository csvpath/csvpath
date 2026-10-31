# pylint: disable=C0114
import os
import logging
import importlib
from csvpath.matching.productions.expression import Matchable
from .function import Function


class InternalFunctionException(Exception):
    """thrown when internal.imports is malformed or one of its functions
    cannot be loaded"""


class InternalFunctions:
    """finds the Framework's own add-on functions, e.g. Macie's. they are
    listed in internal.imports, next to this file, in the same format as a
    user's [functions] imports file:

        from module import Class as function_name

    unlike a user's imports, nothing is imported until a csvpath uses the
    function's name. that way FunctionFactory doesn't need to know about
    add-ons and a csvpath that doesn't use them never imports them.

    the file is read once per process. a bad line, or a name that is also a
    built-in function, is a Framework bug, so we raise rather than skip it."""

    IMPORTS = os.path.join(os.path.dirname(__file__), "internal.imports")
    #
    # function name -> (module, class name). None until the file is read.
    #
    _TABLE = None
    #
    # function name -> class, filled in as each function is first used
    #
    _CLASSES = {}

    @classmethod
    def logger(cls) -> logging.Logger:
        return logging.getLogger(cls.__name__)

    @classmethod
    def get_function(
        cls, *, matcher, name: str, child: Matchable = None, builtins: dict
    ) -> Function | None:
        """returns a new instance of the named function, or None if the name
        is not an internal function"""
        if not isinstance(name, str) or name.strip() == "":
            raise ValueError("Name cannot be None or empty")
        if not isinstance(builtins, dict):
            raise TypeError(f"builtins must be a dict, not {type(builtins)}")
        if cls._TABLE is None:
            cls._TABLE = cls.read(path=cls.IMPORTS, builtins=builtins)
        if name not in cls._TABLE:
            return None
        c = cls.function_class(name=name)
        return c(matcher, name, child)

    @classmethod
    def read(cls, *, path: str, builtins: dict) -> dict:
        """parses an internal imports file into function name -> (module,
        class name). imports nothing."""
        if not isinstance(path, str) or path.strip() == "":
            raise ValueError("path must be a non-empty str")
        if not isinstance(builtins, dict):
            raise TypeError(f"builtins must be a dict, not {type(builtins)}")
        table = {}
        with open(path, "r", encoding="utf-8") as file:
            for i, line in enumerate(file, start=1):
                line = line.strip()
                if line == "" or line.startswith("#"):
                    continue
                module, class_name, name = cls._parse(line=line, path=path, number=i)
                if name in table:
                    cls._fail(f"{path} line {i}: {name} is listed twice")
                if name in builtins:
                    cls._fail(
                        f"{path} line {i}: {name} is a built-in function, "
                        "so the internal one could never be used"
                    )
                table[name] = (module, class_name)
        return table

    @classmethod
    def function_class(cls, *, name: str) -> type:
        """imports the named function's module, if it isn't already, and
        returns its class"""
        if name in cls._CLASSES:
            return cls._CLASSES[name]
        if cls._TABLE is None or name not in cls._TABLE:
            raise ValueError(f"{name} is not an internal function")
        module_name, class_name = cls._TABLE[name]
        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            cls.logger().exception("Cannot import %s for %s", module_name, name)
            raise InternalFunctionException(
                f"Cannot import {module_name} for function {name}: {e}"
            ) from e
        c = getattr(module, class_name, None)
        if c is None:
            cls._fail(f"{module_name} has no class {class_name} for function {name}")
        if not isinstance(c, type) or not issubclass(c, Function):
            cls._fail(f"{module_name}.{class_name} for {name} is not a Function")
        cls._CLASSES[name] = c
        return c

    @classmethod
    def reset(cls) -> None:
        """forgets the file and the loaded classes. for tests."""
        cls._TABLE = None
        cls._CLASSES = {}

    @classmethod
    def _parse(cls, *, line: str, path: str, number: int) -> tuple[str, str, str]:
        #
        # imported here to avoid a circular import; FunctionFactory imports us
        #
        from .function_factory import FunctionFactory

        cs = line.split()
        if not (
            len(cs) == 6 and cs[0] == "from" and cs[2] == "import" and cs[4] == "as"
        ):
            cls._fail(
                f"{path} line {number}: expected 'from module import Class as "
                f"function_name', not {line!r}"
            )
        name = cs[5]
        if not FunctionFactory.valid_function_name(name) or "." in name:
            cls._fail(f"{path} line {number}: {name!r} is not a valid function name")
        return cs[1], cs[3], name

    @classmethod
    def _fail(cls, msg: str) -> None:
        cls.logger().error(msg)
        raise InternalFunctionException(msg)
