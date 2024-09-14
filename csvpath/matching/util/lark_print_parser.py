from typing import List, Any
from lark import Lark
from lark.tree import Tree
from lark.lexer import Token
from lark import Transformer, v_args


class LarkPrintParser:

    GRAMMAR = r"""
        printed: (TEXT | reference | WS)+
        TEXT: /[^\$\s]+/
        reference: ROOT type name
        ROOT: /\$[^\.\$]*\./
        type: (VARIABLES|HEADERS|METADATA|CSVPATH)
        name: "." (SIMPLE_NAME | QUOTED_NAME) ("." (SIMPLE_NAME | QUOTED_NAME))? SENTINEL
        SENTINEL: /[^\.]|\.\./
        SIMPLE_NAME: /[^\.\$\s!\^\:\,;%\(\)\-\+@#\{\}\[\]&<>\/\|\?"']+/
        QUOTED_NAME: /'[^']+'/
        VARIABLES: "variables"
        HEADERS: "headers"
        METADATA: "metadata"
        CSVPATH: "csvpath"
        %import common.SIGNED_NUMBER
        %import common.WS
    """

    def __init__(self, csvpath=None):
        self.csvpath = csvpath
        self.parser = Lark(
            LarkPrintParser.GRAMMAR, start="printed", ambiguity="explicit"
        )
        self.tree = None

    def parse(self, printstr):
        #
        # BLANK is important. the grammar currently requires
        # a sentinel token at the end of a name. it can be anything except
        # a single period. (.. is the escape). if EOL w/o the char parsing
        # fails. the blank char fixes for that without changing the
        # language rules. obviously, there other ways to do it, but this is
        # practical for the moment.
        #
        BLANK = " "
        self.tree = self.parser.parse(f"{printstr}{BLANK}")
        return self.tree


@v_args(inline=True)
class LarkPrintTransformer(Transformer):
    def printed(self, *items) -> List[Any]:
        return items

    def __init__(self, csvpath=None):
        self.csvpath = csvpath
        self.pending_text = []

    def to_string(self, *items):
        res = ""
        for item in items:
            if isinstance(item, dict):
                res += self._reconstruct_references(item)
            else:
                res += item
            res += "\n"
        return res

    def _reconstruct_references(self, item):
        res = ""
        res += item["root"]
        res += item["data_type"]
        res += "."
        ls = item["name"]
        res += f"{ls}"
        return res

    def TEXT(self, token):
        if len(self.pending_text):
            for _ in self.pending_text:
                token.value = f"{_}{token.value}"
            self.pending_text = []
        return token.value

    def reference(self, root=None, datatype=None, name=None):
        return {"root": root, "data_type": datatype, "name": name}

    def WS(self, whitespace):
        if len(self.pending_text):
            for _ in self.pending_text:
                whitespace.value = f"{_}{whitespace.value}"
            self.pending_text = []
        return whitespace.value

    def ROOT(self, token):
        return token.value

    def name(self, simple, tracking=None, sentinel=None):
        name = simple.lstrip(".").strip()
        names = name.split(".")
        names_unquoted = []
        for aname in names:
            if aname[0] == "'" and aname[len(aname) - 1] == "'":
                aname = aname[1 : len(aname) - 1]
            names_unquoted.append(aname)
        if tracking is not None:
            names_unquoted.append(tracking)
        return names_unquoted

    def SIMPLE_NAME(self, token):
        return token.value

    def QUOTED_NAME(self, token):
        return token.value

    def type(self, atype):
        return atype

    def VARIABLES(self, token):
        return token.value

    def HEADERS(self, token):
        return token.value

    def METADATA(self, token):
        return token.value

    def CSVPATH(self, token):
        return token.value

    def SENTINEL(self, token):
        if token.value == "..":
            self.pending_text.append(".")
        else:
            self.pending_text.append(token.value)
        return ""
