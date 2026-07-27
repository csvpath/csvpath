import re

from lark import Transformer, v_args

from .reference_3 import (
    FunctionCall3,
    NameOne3,
    NameThree3,
    Reference3,
    Regex3,
    Star3,
    Variable3,
)

#
# turns a references-v3 Lark parse tree (see reference_grammar_3.py) into
# a Reference3 object graph. one method per grammar rule, mirroring the
# established convention in csvpath/matching/lark_transformer.py -- in
# deliberate contrast to v1/v2's reference_transformer.py, which has one
# method per grammar-rule *combination* and mutates a shared flat object.
# see reference_grammar_3.py's module docstring for why v3's grammar
# doesn't need that.
#
# name_one and name_three each have two independently-optional trailing
# children (name_two/func_chain, and body/func_chain, respectively).
# with v_args(inline=True), an absent optional child just shortens the
# positional children list rather than leaving a None placeholder, so a
# fixed-position signature would silently misassign children whenever
# one of the two is missing but not the other. those two methods take
# *children and dispatch by type instead of by position; every other
# rule has at most one trailing optional child, which plain positional
# defaults handle safely (fewer children always means the rightmost
# param(s) are missing, never a reshuffle).
#


class _PathPrefixResult:
    """transform-internal marker distinguishing path_prefix's segment
    list from func_chain's function-call list. both are plain lists of
    values, so without a distinct wrapper type, name_one's *children
    dispatch couldn't tell them apart positionally when one of the two
    is absent."""

    def __init__(self, segments: list) -> None:
        self.segments = segments


class _FuncChainResult:
    """see _PathPrefixResult -- the func_chain counterpart."""

    def __init__(self, calls: list) -> None:
        self.calls = calls


@v_args(inline=True)
class Reference3Transformer(Transformer):
    def reference(self, root_major, datatype, name_one, name_three=None):
        return Reference3(
            root_major=root_major,
            datatype=datatype,
            name_one=name_one,
            name_three=name_three,
        )

    def root_major(self, value):
        return value

    def datatype(self, token) -> str:
        return str(token)

    def name_one(self, *children) -> NameOne3:
        path_prefix = None
        name_two = None
        func_chain = None
        for child in children:
            if isinstance(child, _PathPrefixResult):
                path_prefix = child
            elif isinstance(child, _FuncChainResult):
                func_chain = child
            else:
                name_two = child
        return NameOne3(
            path=path_prefix.segments,
            name_two=name_two,
            functions=func_chain.calls if func_chain else [],
        )

    def path_prefix(self, *segments) -> _PathPrefixResult:
        return _PathPrefixResult(list(segments))

    def segment(self, value):
        return value

    def name_two(self, token) -> str:
        return str(token)

    def name_three(self, *children) -> NameThree3:
        body = None
        func_chain = None
        for child in children:
            if isinstance(child, _FuncChainResult):
                func_chain = child
            else:
                body = child
        return NameThree3(
            body=body,
            functions=func_chain.calls if func_chain else [],
        )

    def func_chain(self, *functions) -> _FuncChainResult:
        return _FuncChainResult(list(functions))

    def function(self, fname, arg=None) -> FunctionCall3:
        return FunctionCall3(name=str(fname), arg=arg)

    def arg(self, value):
        return value

    # ----------------------------
    # terminals
    # ----------------------------

    def STAR(self, token) -> Star3:  # noqa: N802
        return Star3()

    def AT_VAR(self, token) -> Variable3:  # noqa: N802
        return Variable3(name=str(token)[1:])

    def PATH_SEGMENT(self, token) -> str:  # noqa: N802
        return str(token)

    def IDENTIFIER(self, token) -> str:  # noqa: N802
        return str(token)

    def STRING(self, token) -> str:  # noqa: N802
        # grammar's STRING allows "\." to escape any character (not just
        # quote/backslash) -- undo that generically rather than special
        # casing \" and \\.
        raw = str(token)[1:-1]
        return re.sub(r"\\(.)", r"\1", raw)

    def SIGNED_INT(self, token) -> int:  # noqa: N802
        return int(token)

    def REGEX(self, token) -> Regex3:  # noqa: N802
        return Regex3(pattern=str(token)[1:-1])

    def FNAME(self, token) -> str:  # noqa: N802
        return str(token)
