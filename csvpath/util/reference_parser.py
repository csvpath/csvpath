class ReferenceException(Exception):
    pass


class ReferenceParser:
    #
    # references are in the form:
    #    $named-paths.datatype.major[.minor]
    #    $.datatype.major[.minor]
    #    $named-paths#identity[.datatype.major.minor]
    # in the future probably also:
    #    $named-paths.datatype.:pointer[.minor]
    #
    # some or all of these may become possible with functions that take
    # references
    #
    # local is the $.type.name form used in print() to point to
    # the current csvpath runtime.
    LOCAL = "local"
    #
    # data types
    #
    VARIABLES = "variables"
    HEADERS = "headers"
    CSVPATHS = "csvpaths"
    CSVPATH = "csvpath"
    METADATA = "metadata"
    RESULTS = "results"

    def __init__(self, string: str = None) -> None:
        self._root_major = None
        self._root_minor = None
        self._datatype = None
        self._names = None
        if string is not None:
            self.parse(string)

    def __str__(self) -> str:
        return f"""
        root major:{self._root_major}
        root minor:{self._root_minor}
        datatype:{self._datatype}
        names:{self._names}
        """

    @property
    def root_major(self) -> str:
        return self._root_major

    @root_major.setter
    def root_major(self, r: str) -> None:
        self._root_major = r

    @property
    def root_minor(self) -> str:
        return self._root_minor

    @root_minor.setter
    def root_minor(self, r: str) -> None:
        self._root_minor = r

    def _set_root(self, r) -> None:
        if r is None:
            raise ReferenceException("Root cannot be none")
        t = self._names_from_name(r)
        self.root_minor = t[1]
        self.root_major = t[0]

    def _set_names(self, string) -> None:
        self._names = []
        t = self._names_from_name(string, ".")

        major = self._names_from_name(t[0])
        self._names.append(major[0])
        self._names.append(major[1])

        minor = self._names_from_name(t[1])
        self._names.append(minor[0])
        self._names.append(minor[1])

    def _names_from_name(self, r, marker: str = "#") -> list:
        names = []
        if r is not None:
            i = r.find(marker)
            if i > -1:
                m1 = r[i + 1 :]
                names.append(r[0:i])
                names.append(m1)
            else:
                names.append(r)
                names.append(None)
        else:
            names.append(None)
            names.append(None)
        return names

    @property
    def datatype(self) -> str:
        return self._datatype

    @datatype.setter
    def datatype(self, t: str) -> None:
        if t not in [
            ReferenceParser.VARIABLES,
            ReferenceParser.HEADERS,
            ReferenceParser.RESULTS,
            ReferenceParser.CSVPATHS,
            ReferenceParser.CSVPATH,
            ReferenceParser.METADATA,
        ]:
            raise ReferenceException(f"Unknown datatype {t} in {self}")
        self._datatype = t

    @property
    def name_one(self) -> str:
        return self._names[0]

    @property
    def name_two(self) -> str:
        return self._names[1]

    @property
    def name_three(self) -> str:
        return self._names[2]

    @property
    def name_four(self) -> str:
        return self._names[3]

    @property
    def names(self) -> list[str]:
        return self._names

    @names.setter
    def names(self, ns: str) -> None:
        self._names = ns

    def parse(self, string: str) -> None:
        if string is None:
            raise ReferenceException("Reference string cannot be None")
        if string[0] != "$":
            raise ReferenceException("Reference string must start with a root '$'")
        self._original = string
        root = None
        if string[1] == ".":
            root = ReferenceParser.LOCAL
            string = string[2:]
        else:
            dot = string.find(".")
            root = string[1:dot]
            string = string[dot + 1 :]
        self._set_root(root)

        dot = string.find(".")
        self.datatype = string[0:dot]

        string = string[dot + 1 :]
        self._set_names(string)
