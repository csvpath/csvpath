import logging

from .reference_exceptions_3 import ReferenceException3


#
# object graph built by Reference3Transformer (reference_transformer_3.py)
# from a references-v3 parse tree (see reference_grammar_3.py). these are
# plain value objects -- no execution/query context, no filesystem access.
# ReferenceParser3 (reference_parser_3.py) is the thing that pairs a
# Reference3 with a CsvPaths context; a ReferenceFinder3 (not yet built)
# is what actually runs a query against storage.
#


class Star3:
    """a bare "*" wildcard token. there is no state beyond "this position
    was a wildcard" so every instance is equal to every other."""

    def __eq__(self, other) -> bool:
        return isinstance(other, Star3)

    def __repr__(self) -> str:
        return "Star3()"

    def __str__(self) -> str:
        return "*"


class Variable3:
    """an "@name" runtime-bound variable reference."""

    def __init__(self, *, name: str) -> None:
        if not name:
            raise ValueError("Variable3 name cannot be None or empty")
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def __eq__(self, other) -> bool:
        return isinstance(other, Variable3) and other.name == self._name

    def __repr__(self) -> str:
        return f"Variable3(name={self._name!r})"

    def __str__(self) -> str:
        return f"@{self._name}"


class Regex3:
    """a slash-delimited regex literal, e.g. /^(?:Mon|Tue)day$/. pattern
    is held without the delimiting slashes."""

    def __init__(self, *, pattern: str) -> None:
        if pattern is None:
            raise ValueError("Regex3 pattern cannot be None")
        self._pattern = pattern

    @property
    def pattern(self) -> str:
        return self._pattern

    def __eq__(self, other) -> bool:
        return isinstance(other, Regex3) and other.pattern == self._pattern

    def __repr__(self) -> str:
        return f"Regex3(pattern={self._pattern!r})"

    def __str__(self) -> str:
        return f"/{self._pattern}/"


def _arg_to_string(value) -> str:
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return str(value)


class FunctionCall3:
    """a single ":name(arg)" function call. arg is None (no arg), a str,
    an int, a Star3, a Variable3, a Regex3, or a nested FunctionCall3 --
    whatever the arg rule's child transformed to. functions are looked up
    and validated at runtime by a registry, not here -- see
    "requirements for functions.txt"; this class only holds the parsed
    shape, it does not know what functions exist."""

    def __init__(self, *, name: str, arg=None) -> None:
        if not name:
            raise ValueError("FunctionCall3 name cannot be None or empty")
        self._name = name
        self._arg = arg

    @property
    def name(self) -> str:
        return self._name

    @property
    def arg(self):
        return self._arg

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, FunctionCall3)
            and other.name == self._name
            and other.arg == self._arg
        )

    def __repr__(self) -> str:
        return f"FunctionCall3(name={self._name!r}, arg={self._arg!r})"

    def __str__(self) -> str:
        arg = "" if self._arg is None else _arg_to_string(self._arg)
        return f":{self._name}({arg})"

    def contains_function_named(self, name: str) -> bool:
        """true if this function, or any function nested in its
        argument chain, is named `name`. a purely structural query --
        no function-registry knowledge involved. see Reference3.
        resolves_to_data for what this is used for."""
        if self._name == name:
            return True
        if isinstance(self._arg, FunctionCall3):
            return self._arg.contains_function_named(name)
        return False


class NameOne3:
    """name_one: a "/"-joined path (literal names, "*", and/or functions
    each occupying a whole segment), an optional "#name_two" worksheet
    marker, and a trailing function chain. a path-less, function(s)-only
    name_one (e.g. ":all()") still has a non-empty path -- see
    reference_grammar_3.py's module docstring -- its single segment is
    just a FunctionCall3 rather than a literal or Star3."""

    def __init__(
        self,
        *,
        path: list,
        name_two: str | None = None,
        functions: list | None = None,
    ) -> None:
        if not path:
            raise ValueError("NameOne3 path cannot be None or empty")
        self._path = path
        self._name_two = name_two
        self._functions = functions or []

    @property
    def path(self) -> list:
        return self._path

    @property
    def name_two(self) -> str | None:
        return self._name_two

    @property
    def functions(self) -> list:
        return self._functions

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, NameOne3)
            and other.path == self._path
            and other.name_two == self._name_two
            and other.functions == self._functions
        )

    def __repr__(self) -> str:
        return (
            f"NameOne3(path={self._path!r}, name_two={self._name_two!r}, "
            f"functions={self._functions!r})"
        )

    def __str__(self) -> str:
        s = "/".join(str(p) for p in self._path)
        if self._name_two is not None:
            s = f"{s}#{self._name_two}"
        for f in self._functions:
            s = f"{s}{f}"
        return s


class NameThree3:
    """name_three: an optional single body (a literal name or "*", no
    path building), plus a trailing function chain. body and functions
    can't both be absent -- the grammar requires at least one."""

    def __init__(self, *, body=None, functions: list | None = None) -> None:
        self._body = body
        self._functions = functions or []
        if self._body is None and not self._functions:
            raise ValueError("NameThree3 must have a body, functions, or both")

    @property
    def body(self):
        return self._body

    @property
    def functions(self) -> list:
        return self._functions

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, NameThree3)
            and other.body == self._body
            and other.functions == self._functions
        )

    def __repr__(self) -> str:
        return f"NameThree3(body={self._body!r}, functions={self._functions!r})"

    def __str__(self) -> str:
        s = "" if self._body is None else str(self._body)
        for f in self._functions:
            s = f"{s}{f}"
        return s


#
# PLACEHOLDER pending the real function registry (see "requirements for
# functions.txt" -- functions are looked up/validated at runtime by a
# registry that does not exist yet). Once it does, this belongs on
# Function3 itself as self-description metadata (each function will
# self-report whether it is a "context setter" or a "pointer" -- see
# that doc), not here as a bare name list.
#
# there is no separate "value extracting" category of function: a
# pointer resolves the current scope to exactly 0 or 1 item, full stop.
# in name_one that item is a physical file/version/run; in name_three
# it is a well-known file (e.g. :errors()) UNLESS that pointer itself
# takes another pointer as its argument, in which case the outer
# pointer resolves to a specific value inside the file rather than the
# file as a whole (e.g. :errors(:idchain("add[0]string[2]"))). so what
# this constant actually names is: pointer functions currently known to
# be used this way -- nested inside another function, in name_three,
# meaning "a value" rather than "a file." it is deliberately NOT "any
# pointer nested inside another function" -- name_one already nests
# pointers inside functions all the time for ordinary version/range
# selection (e.g. :from(:index(0)) is still picking a file/version, not
# extracting a value), and name_three may end up doing the same for its
# own result-file listing once more functions exist. this list will be
# replaced by real trait lookups once Function3 exists; treat it as
# provisional, not as a general rule for "nested pointer means value."
#
_CONTENT_POINTER_FUNCTIONS = ("idchain",)


class Reference3:
    """the parsed object graph for one references-v3 reference. holds no
    execution context (see ReferenceParser3 for that) -- just the parsed
    shape, validated against the datatype-dependent name_three
    requirement the grammar deliberately leaves out (see
    reference_grammar_3.py's module docstring)."""

    FILES = "files"
    CSVPATHS = "csvpaths"
    RESULTS = "results"

    def __init__(
        self,
        *,
        root_major,
        datatype: str,
        name_one: NameOne3,
        name_three: NameThree3 | None = None,
    ) -> None:
        if root_major is None:
            raise ValueError("Reference3 root_major cannot be None")
        if datatype not in (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS):
            raise ValueError(f"Unknown datatype: {datatype}")
        if name_one is None:
            raise ValueError("Reference3 name_one cannot be None")
        self._root_major = root_major
        self._datatype = datatype
        self._name_one = name_one
        self._name_three = name_three

    def check_valid(self) -> None:
        """structural check deferred out of the grammar (see
        reference_grammar_3.py's module docstring): name_three is
        required for files/csvpaths, optional for results. called
        explicitly by ReferenceParser3 right after the transformer
        builds this object -- not from __init__, so that a violation
        raises ReferenceException3 as itself rather than being wrapped
        in lark's VisitError (which is what happens to any exception
        raised from inside a Transformer rule method)."""
        if self._name_three is None and self._datatype in (
            Reference3.FILES,
            Reference3.CSVPATHS,
        ):
            logger = logging.getLogger(self.__class__.__name__)
            msg = f"name_three is required for datatype '{self._datatype}'"
            logger.error(msg)
            raise ReferenceException3(msg)

    @property
    def root_major(self):
        return self._root_major

    @property
    def datatype(self) -> str:
        return self._datatype

    @property
    def name_one(self) -> NameOne3:
        return self._name_one

    @property
    def name_three(self) -> NameThree3 | None:
        return self._name_three

    @property
    def resolves_to_data(self) -> bool:
        """does this reference ask for a specific value inside a
        well-known file (True), or the file/thing as-is (False)? see
        the _CONTENT_POINTER_FUNCTIONS placeholder comment above -- this
        is a stand-in for a trait the future function registry will
        own (a pointer nested inside another pointer, in name_three)."""
        if self._name_three is None:
            return False
        return any(
            f.contains_function_named(name)
            for f in self._name_three.functions
            for name in _CONTENT_POINTER_FUNCTIONS
        )

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, Reference3)
            and other.root_major == self._root_major
            and other.datatype == self._datatype
            and other.name_one == self._name_one
            and other.name_three == self._name_three
        )

    def __repr__(self) -> str:
        return (
            f"Reference3(root_major={self._root_major!r}, datatype={self._datatype!r}, "
            f"name_one={self._name_one!r}, name_three={self._name_three!r})"
        )

    def __str__(self) -> str:
        s = f"${self._root_major}.{self._datatype}.{self._name_one}"
        if self._name_three is not None:
            s = f"{s}.{self._name_three}"
        return s
