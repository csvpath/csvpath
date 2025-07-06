import os
from csvpath.util.path_util import PathUtility as pathu
from .reference_grammar import QueryParser
from .reference_exceptions import ReferenceException


class ReferenceParser:
    #
    # references are in the form:
    #    $named-paths.datatype.major[.minor]
    #    $.datatype.major[.minor]
    #    $named-paths#identity[.datatype.major.minor]
    #
    # see the reference_grammar.py and test_ref_grammar.py
    #
    # the # and . characters are the main stops. # is used (rarely) to
    # reduce the scope of the component (a.k.a. name) it is on. the '.'
    # is used to separate components. typically the same thing you may
    # be able to do with # is better doable in adding the last component
    # to the reference.
    #
    # depending on the usage, references can take pointers or filters
    # on names one, two, three, and four. they are in the form of
    # colon-name. e.g.:
    #     $named-paths.datatype.[major][:pointer][.minor][:pointer]
    # in some cases the major component could be empty, but a pointer on
    # be present. for e.g. you might want to reference the 3rd version
    # of a named-file without specifying the underlying path, fingerprint,
    # etc.
    #
    # local is the $.type.name form used in print() to point to the current
    # csvpath runtime.
    #
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

    def __init__(self, string: str = None, *, csvpaths=None) -> None:
        self._csvpaths = csvpaths
        self._root_major = None
        self._root_minor = None
        self._datatype = None
        self._name_one = None
        self._name_two = None
        self._name_three = None
        self._name_four = None
        
        self._name_one_is_fingerprint = False
        self._name_one_tokens = []
        self._name_two_tokens = []
        self._name_three_tokens = []
        self._name_four_tokens = []
        #
        # self.next holds hints for what more you could do with this query
        # e.g. $agroup.results.2025-01:after would return:
        #   :index, :first, :last
        #   .datetime
        # if the query changed to $agroup.results.2025-01:after:10 the return would be:
        #   .csvpath name
        #
        self._next = []
        #
        #
        #
        self._marker = "#"
        self._name_separator = "."
        self._sep = None
        self._reference = string
        self.parser = None
        self.sequence = []
        if string is not None:
            self.parser = QueryParser(ref=self)
            self.parser.parse(self._reference)
        
    def __str__(self) -> str:
        return f"""
        root major:{self._root_major}
        root minor:{self._root_minor}
        datatype:{self._datatype}
        name one: {self._name_one}
        name two: {self._name_two}
        name three: {self._name_three}
        name four: {self._name_four}
        name one tokens: {self._name_one_tokens}
        name two tokens: {self._name_two_tokens}
        name three tokens: {self._name_three_tokens}
        name four tokens: {self._name_four_tokens}
        """

    @property
    def csvpaths(self):
        return self._csvpaths
        
    @csvpaths.setter
    def csvpaths(self, csvpaths) -> None:
        self._csvpaths = csvpaths

    @property
    def next(self) -> list[str]:
        return self._next

    @next.setter
    def next(self, ns: list[str]) -> None:
        self._next = ns

    @property
    def reference(self) -> str:
        return self._reference

    @property
    def ref_string(self) -> str:
        marker = self.marker
        if marker is None:
            marker = "#"
        separator = self.name_separator
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
    def name_one_is_fingerprint(self) -> bool:
        return self._name_one_is_fingerprint

    @name_one_is_fingerprint.setter
    def name_one_is_fingerprint(self, t: bool) -> None:
        self._name_one_is_fingerprint = t

    @property
    def root_major(self) -> str:
        return self._root_major

    @root_major.setter
    def root_major(self, r: str) -> None:
        self._root_major = r

    @property
    def root_name(self) -> str:
        if self.root_minor:
            return f"{self.root_major}#{self.root_minor}"
        return self._root_major

    @root_name.setter
    def root_name(self, name: str) -> str:
        i = name.find("#")
        if i > -1:
            self._root_major = name[0:i]
            self._root_minor = name[i + 1 :]
        else:
            self._root_major = name

    @root_major.setter
    def root_major(self, r: str) -> None:
        self._root_major = r

    @property
    def root_minor(self) -> str:
        return self._root_minor

    @property
    def marker(self) -> str:
        return self._marker

    #
    # name_separator is the character that goes between root_major/root_minor and datatype 
    # and between data type and name_one/name_two and between that and name_three/name_four.
    # i.e. typically the ".". we no longer expect name_separator will change, but if it
    # did that would happen here.
    #
    @property
    def name_separator(self) -> str:
        return self._name_separator

    @name_separator.setter
    def name_separator(self, s:str) -> None:
        self._name_separator = s

    @property
    def sep(self) -> str:
        if self._sep is None:
            #
            # this is unlikely today. we would not expect an absolute path in a reference
            #
            #self.sep = os.sep if self.reference is None or self.reference.find("://") > -1 else "/"
            #
            if self.datatype is not None and self.csvpaths is not None:
                uri = None
                if self.datatype == "files" or self.datatype == "csvpaths":
                    uri = self.csvpaths.config.get(section="inputs", name=self.datatype)
                elif self.datatype == "results":
                    uri = self.csvpaths.config.get(section="results", name="archive")
                if uri is None:
                    uri = self.name_one
                if uri is not None:
                    if uri.find("://") > -1:
                        self._sep = "/"
                    elif uri.find("\\") > -1: 
                        self._sep = "\\"
                    else:
                        self._sep = os.sep
                else:
                    self._sep = os.sep
            else:
                if self.name_one is not None and self.name_one.find("\\") > -1: 
                    self._sep = "\\"
                else:
                    self._sep = os.sep
        return self._sep

    @sep.setter
    def sep(self, s:str) -> None:
        self._sep = s

    @root_minor.setter
    def root_minor(self, r: str) -> None:
        self._root_minor = r

    def _set_root(self, r) -> None:
        if r is None:
            raise ReferenceException("Root cannot be none")
        t = self._split(r)
        self.root_minor = t[1]
        self.root_major = t[0]
    
    def _split(self, r) -> list:
        #
        # splits a name into two parts. the value passed in is either root_major/root_minor
        # or name_one/name_two or name_three/name_four
        #
        names = []
        if r is not None:
            i = r.find(self.marker)
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
        return self._name_one

    @name_one.setter
    def name_one(self, n: str) -> str:
        if not n:
            self._name_one = None
            self._name_two = None
            return
        i = n.find(self.marker)
        if i > -1:
            self._name_one = n[0:i]
            self._name_two = n[i + 1 :]
            return
        self._name_one = n
        
    @property
    def name_two(self) -> str:
        return self._name_two

    @property
    def name_three(self) -> str:
        return self._name_three

    @name_three.setter
    def name_three(self, n: str) -> str:
        #self._assure_names()
        if not n:
            self._name_three = None
            self._name_four = None
            return
        i = n.find(self.marker)
        if i > -1:
            self._name_three = n[0:i]
            self._name_four = n[i + 1 :]
        else:
            self._name_three = n
            self._name_four = None

    @property
    def name_four(self) -> str:
        return self._name_four

    @classmethod
    def find_int_token(cls, tokens: list) -> int | None:
        if tokens is None:
            raise ValueError("Tokens cannot be None")
        for t in tokens:
            try:
                return int(t)
            except Exception:
                ...
        return None

    def get_range_from_tokens(self, tokens) -> str:
        range = None
        range = "today" if "today" in tokens else None
        range = "yesterday" if "yesterday" in tokens else range
        range = "all" if "all" in tokens else range
        range = "from" if "from" in tokens else range
        range = "to" if "to" in tokens else range
        range = "after" if "after" in tokens else range
        range = "before" if "before" in tokens else range
        return range

    #
    # adds a string or a list[str] of tokens. each string will
    # be parsed for additional tokens. i.e. all:yesterday:first
    # would become three tokens. (three tokens are not expected,
    # tho)
    #
    def _add_tokens(self, ts: list, t: str | list) -> None:
        if t is None:
            return
        if isinstance(t, str):
            t = t.strip()
        if t == "":
            return
        if not isinstance(t, list):
            t = [t]
        for s in t:
            if not isinstance(s, str):
                raise ValueError(f"Cannot add token {s}")
            s = s.lstrip(":")
            i = s.find(":")
            if i == -1:
                ts.append(s)
            else:
                ts.append(t[0:i])
                self._add_tokens(ts, s[i + 1])

    @property
    def name_one_tokens(self) -> list:
        return self._name_one_tokens

    @name_one_tokens.setter
    def name_one_tokens(self, t: str | list) -> None:
        if self._name_one_tokens is None:
            self._name_one_tokens = []
        self._add_tokens(self._name_one_tokens, t)

    def append_name_one_token(self, t: str) -> None:
        self._add_tokens(self.name_one_tokens, t)

    def append_name_two_token(self, t: str) -> None:
        self._add_tokens(self.name_two_tokens, t)

    def append_name_three_token(self, t: str) -> None:
        self._add_tokens(self.name_three_tokens, t)

    def append_name_four_token(self, t: str) -> None:
        self._add_tokens(self.name_four_tokens, t)

    @property
    def name_two_tokens(self) -> list:
        return self._name_two_tokens

    @name_two_tokens.setter
    def name_two_tokens(self, t: str | list) -> None:
        if self._name_two_tokens is None:
            self._name_two_tokens = []
        self._add_tokens(self._name_two_tokens, t)

    @property
    def name_three_tokens(self) -> list:
        return self._name_three_tokens

    @name_three_tokens.setter
    def name_three_tokens(self, t: str | list) -> None:
        if self._name_three_tokens is None:
            self._name_three_tokens = []
        self._add_tokens(self._name_three_tokens, t)

    @property
    def name_four_tokens(self) -> list:
        return self._name_four_tokens

    @name_four_tokens.setter
    def name_four_tokens(self, t: str | list) -> None:
        if self._name_four_tokens is None:
            self._name_four_tokens = []
        self._add_tokens(self._name_four_tokens, t)
    
    def parse(self, string: str) -> None:
        self.parser = QueryParser(ref=self)
        self.parser.parse(string)

