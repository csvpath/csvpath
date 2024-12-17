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
        name: "." (SIMPLE_NAME | QUOTED_NAME) ("." (SIMPLE_NAME | QUOTED_NAME))? sentinel
        NON_SIMPLE_CHAR: /[\t\n\r \$!\^\:\,;%\(\)\-\+@#\{\}\[\]&<>\/\|\?"']/
        DOT_DOT: ".."
        sentinel: NON_SIMPLE_CHAR|DOT_DOT
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
    def __init__(self, csvpath=None):
        self.csvpath = csvpath
        self.pending_text = []

    # =================
    # productions
    # =================

    def printed(self, *items) -> List[Any]:
        return items

    def TEXT(self, token):
        #
        # 16 dec 2024: coverage indicated this and the
        # analogous in WS are never used. adding an exception
        # w/in the test never raises. leaving for now because
        # maybe there is some corner case we'd only spot
        # visually? if no indications in the next month or so
        # remove.
        #
        """
        if len(self.pending_text):
            for _ in self.pending_text:
                token.value = f"{_}{token.value}"
            self.pending_text = []
        """
        return token.value

    def reference(self, root=None, datatype=None, name=None):
        sentinel = ""
        if self.pending_text and len(self.pending_text):
            for _ in self.pending_text:
                sentinel = f"{sentinel}{_}"
            self.pending_text = []

        return {"root": root, "data_type": datatype, "name": name, "sentinel": sentinel}

    def WS(self, whitespace):
        #
        # 16 dec 2024: coverage indicated this and the
        # analogous in TEXT are never used. adding an exception
        # w/in the test never raises. leaving for now because
        # maybe there is some corner case we'd only spot
        # visually? if no indications in the next month or so
        # remove.
        #
        """
        if len(self.pending_text):
            for _ in self.pending_text:
                whitespace.value = f"{_}{whitespace.value}"
            self.pending_text = []
        """
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

    def DOT_DOT(self, token):
        if token and token.value is not None:
            self.pending_text.append(".")

    def NON_SIMPLE_CHAR(self, token):
        if token and token.value is not None:
            self.pending_text.append(token.value)

    def sentinel(self, non_simple_char=None, dot_dot=None):
        # the sentinel values go into pending_text and
        # are added to the reference under the "sentinel" key
        # when we reduce the ref to text in PrintParser we
        # append the sentinel.
        pass
