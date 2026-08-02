import re

from lark import Lark, Transformer, v_args
from lark.exceptions import UnexpectedInput

from .reference_3 import (
    FunctionCall3,
    InterpolatedString3,
    NameOne3,
    NameThree3,
    Reference3,
    Regex3,
    Star3,
    Variable3,
)
from .reference_exceptions_3 import ReferenceException3

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


#
# String interpolation: a STRING argument may contain one or more
# "{...}" spans -- each a bare @variable or a call to a function whose
# role is VALUE (context setters/pointers are rejected -- see
# InterpolatedString3.check_valid()). "{{"/"}}" escape a literal brace,
# matching the convention already used by csvpath/util/var_utility.py's
# substitute().
#
# kept as a separate, small grammar rather than a REFERENCE_GRAMMAR_3
# change, so the main, LALR-clean reference grammar stays untouched --
# this one only ever parses the *content* of one already-found
# "{...}" span, reusing the exact same AT_VAR/FNAME/function/arg
# terminal definitions (kept textually identical to
# reference_grammar_3.py's on purpose, to avoid behavioral drift
# between the two).
#
_INTERPOLATION_GRAMMAR_3 = r"""
    ?start: AT_VAR
          | function

    function: ":" FNAME "(" arg? ")"

    arg: STRING
       | SIGNED_INT
       | AT_VAR
       | function
       | REGEX
       | STAR

    STAR: "*"
    AT_VAR: "@" IDENTIFIER
    FNAME: /[a-zA-Z_][a-zA-Z0-9_]*/
    IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_\-]*/
    STRING: /"(?:[^"\\]|\\.)*"/
    SIGNED_INT: /-?\d+/
    REGEX: "/" REGEX_INNER "/"
    REGEX_INNER: /([^\/\\]|\\.)*/

    %import common.WS
    %ignore WS
"""

_interpolation_parser = None


def _get_interpolation_parser() -> Lark:
    global _interpolation_parser
    if _interpolation_parser is None:
        _interpolation_parser = Lark(_INTERPOLATION_GRAMMAR_3, parser="lalr")
    return _interpolation_parser


def _parse_interpolation_span(inner: str):
    try:
        tree = _get_interpolation_parser().parse(inner)
    except UnexpectedInput as e:
        raise ReferenceException3(
            f"Invalid {{...}} interpolation content {inner!r}: {e}"
        ) from e
    return Reference3Transformer().transform(tree)


def _split_interpolated_parts(text: str) -> list:
    """splits `text` into literal string chunks and parsed @variable/
    function parts, honoring "{{"/"}}" as escapes for a literal brace.
    a plain string with no unescaped "{" comes back as a single-element
    list holding the original string, untouched -- callers use that to
    skip wrapping in InterpolatedString3 for the (overwhelmingly
    common) no-interpolation case.

    deliberately simple: finds each span by the next unescaped "}"
    after an unescaped "{", not by brace-depth/quote-aware balancing --
    sufficient for the interpolation shapes actually in use (a bare
    @variable or one function call), not a general nested-brace parser."""
    parts = []
    buf = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "{" and i + 1 < n and text[i + 1] == "{":
            buf.append("{")
            i += 2
            continue
        if ch == "}" and i + 1 < n and text[i + 1] == "}":
            buf.append("}")
            i += 2
            continue
        if ch == "{":
            end = text.find("}", i + 1)
            if end == -1:
                raise ReferenceException3(
                    f"Unescaped '{{' with no matching '}}' in string: {text!r}"
                )
            if buf:
                parts.append("".join(buf))
                buf = []
            parts.append(_parse_interpolation_span(text[i + 1 : end]))
            i = end + 1
            continue
        if ch == "}":
            raise ReferenceException3(
                f"Unescaped '}}' with no matching '{{' in string: {text!r}"
            )
        buf.append(ch)
        i += 1
    if buf or not parts:
        parts.append("".join(buf))
    return parts


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

    def STRING(self, token) -> str | InterpolatedString3:  # noqa: N802
        # grammar's STRING allows "\." to escape any character (not just
        # quote/backslash) -- undo that generically rather than special
        # casing \" and \\.
        raw = str(token)[1:-1]
        unescaped = re.sub(r"\\(.)", r"\1", raw)
        parts = _split_interpolated_parts(unescaped)
        if len(parts) == 1 and isinstance(parts[0], str):
            return parts[0]
        return InterpolatedString3(parts=parts)

    def SIGNED_INT(self, token) -> int:  # noqa: N802
        return int(token)

    def REGEX(self, token) -> Regex3:  # noqa: N802
        return Regex3(pattern=str(token)[1:-1])

    def FNAME(self, token) -> str:  # noqa: N802
        return str(token)
