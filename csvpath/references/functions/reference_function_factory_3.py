from ..reference_3 import FunctionCall3
from ..reference_exceptions_3 import ReferenceException3
from .function_3 import Function3


class ReferenceFunctionFactory:
    #
    # name-keyed registry turning FunctionCall3 (parsed name+arg shape)
    # into real Function3 instances -- conceptually similar to
    # csvpath.matching.functions.function_factory.FunctionFactory, per
    # "requirements for functions.txt", but far smaller: references-v3
    # functions take at most 1 arg and have no argset overloads, so
    # there is no per-name construction complexity to speak of.
    #
    _FUNCTIONS: dict = {}

    @classmethod
    def _load(cls) -> None:
        from .all_3 import All3
        from .definition_3 import Definition3
        from .first_3 import First3
        from .index_3 import Index3
        from .last_3 import Last3
        from .manifest_3 import Manifest3
        from .name_3 import Name3

        cls._FUNCTIONS = {
            First3.NAME: First3,
            Last3.NAME: Last3,
            Index3.NAME: Index3,
            Name3.NAME: Name3,
            All3.NAME: All3,
            Manifest3.NAME: Manifest3,
            Definition3.NAME: Definition3,
        }

    @classmethod
    def add_function(cls, function_cls: type) -> None:
        """registers a function class at runtime -- e.g. for a custom,
        user-added function (see "requirements for functions.txt"'s
        possible-requirements section). overrides an existing name."""
        if function_cls is None:
            raise ValueError("function_cls cannot be None")
        if not cls._FUNCTIONS:
            cls._load()
        cls._FUNCTIONS[function_cls.NAME] = function_cls

    @classmethod
    def get_registered_class(cls, name: str) -> type | None:
        """the registered Function3 CLASS for `name`, or None if
        unknown -- for checking class-level metadata (e.g. ROLE)
        without constructing/validating an instance. Used by
        InterpolatedString3.check_valid() to reject non-VALUE
        functions inside a "{...}" interpolation without needing to
        evaluate them."""
        if not cls._FUNCTIONS:
            cls._load()
        return cls._FUNCTIONS.get(name)

    @classmethod
    def build(cls, call: FunctionCall3) -> Function3:
        """compiles one FunctionCall3 into a real, validated Function3.
        recurses first if call.arg is itself a FunctionCall3, so a
        nested function is always compiled (and check_valid()'d) before
        the function that takes it as an argument."""
        if call is None:
            raise ValueError("FunctionCall3 cannot be None")
        if not cls._FUNCTIONS:
            cls._load()
        arg = call.arg
        if isinstance(arg, FunctionCall3):
            arg = cls.build(arg)
        function_cls = cls._FUNCTIONS.get(call.name)
        if function_cls is None:
            raise ReferenceException3(f"Unknown reference function: {call.name}")
        instance = function_cls(arg=arg)
        instance.check_valid()
        return instance

    @classmethod
    def build_chain(cls, calls: list) -> list:
        """compiles a whole function chain (NameOne3/NameThree3's
        .functions list) and enforces "at most one pointer function per
        chain, per nesting level" -- see "requirements for
        functions.txt". a pointer nested inside another function's
        argument (already compiled by build() above) does not count
        here; only these direct siblings do."""
        built = [cls.build(call) for call in calls]
        pointers = [f for f in built if f.ROLE == Function3.POINTER]
        if len(pointers) > 1:
            names = ", ".join(f":{f.name}()" for f in pointers)
            raise ReferenceException3(
                f"At most one pointer function is allowed per function chain, "
                f"found {len(pointers)}: {names}"
            )
        return built
