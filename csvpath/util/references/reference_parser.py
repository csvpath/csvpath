from csvpath.util.path_util import PathUtility as pathu


class ReferenceException(Exception):
    pass


class ReferenceParser:
    #
    # references are in the form:
    #    $named-paths.datatype.major[.minor]
    #    $.datatype.major[.minor]
    #    $named-paths#identity[.datatype.major.minor]
    #
    # the # and . characters are the main stops. # is used (rarely) to
    # reduce the scope of the component (a.k.a. name) it is on. the '.'
    # is used to separate components. typically the same thing you may
    # be able to do with # is better doable in adding the last component
    # to the reference.
    #
    # depending on the usage, most references can take pointers or filters
    # in the form of colon-name. E.g.:
    #     $named-paths.datatype.[major][:pointer][.minor][:pointer]
    # in some cases the major component could be empty, but a pointer on
    # be present. for e.g. you might want to reference the 3rd version
    # of a named-file without specifying the underlying path, fingerprint,
    # etc.
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
    FILES = "files"

    def __init__(self, string: str = None) -> None:
        self._root_major = None
        self._root_minor = None
        self._datatype = None
        self._names = None
        self._marker = None
        self._separator = None
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
    def ref_string(self) -> str:
        marker = self.marker
        if marker is None:
            marker = "#"
        separator = self.separator
        if separator is None:
            separator = "."
        ret = f"${self.root_major}"
        if self.root_minor is not None:
            ret = f"{ret}{marker}{self.root_minor}"
        ret = f"{ret}{separator}{self.datatype}{separator}{self.name_one}"
        if self.name_two is not None:
            ret = f"{ret}{marker}{self.name_two}"
        if self.name_three is not None:
            ret = f"{ret}{separator}{self.name_three}"
        if self.name_four is not None:
            ret = f"{ret}{marker}{self.name_four}"
        return ret

    @property
    def root_major(self) -> str:
        return self._root_major

    @root_major.setter
    def root_major(self, r: str) -> None:
        self._root_major = r

    @property
    def root_minor(self) -> str:
        return self._root_minor

    @property
    def marker(self) -> str:
        return self._marker

    @property
    def separator(self) -> str:
        return self._separator

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
        t = self._separate_names(string, separator=".")

        major = self._names_from_name(t[0])
        self._names.append(major[0])
        self._names.append(major[1])

        minor = self._names_from_name(t[1])
        self._names.append(minor[0])
        self._names.append(minor[1])

    def _separate_names(self, r, separator: str = ".") -> list:
        if self._separator is not None and self._separator != separator:
            raise ValueError(
                f"Separator is already set to {self._separator} so {separator} is not valid"
            )
        self._separator = separator
        return self._split(r, marker=separator)

    def _names_from_name(self, r, marker: str = "#") -> list:
        if self._marker is not None and self._marker != marker:
            raise ValueError(
                f"Marker is already set to {self._marker} so {marker} is not valid"
            )
        self._marker = marker
        return self._split(r, marker=marker)

    def _split(self, r, marker: str = "#") -> list:
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
            #
            # these are for run-generated metadata
            #
            ReferenceParser.VARIABLES,
            ReferenceParser.HEADERS,
            ReferenceParser.CSVPATH,
            ReferenceParser.METADATA,
            #
            # this are for inputs files and results
            #
            ReferenceParser.RESULTS,
            ReferenceParser.CSVPATHS,
            ReferenceParser.FILES,
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
        string = pathu.resep(string)
        self._original = string
        root = None
        #
        # TODO: use self.separator
        #
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
