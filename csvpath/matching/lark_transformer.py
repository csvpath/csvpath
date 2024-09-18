""" implements the transformer that receives trees and tokens from Lark
    and turns them into the match components Matcher uses """

from lark import Transformer, v_args
from lark.lexer import Token

from .productions import (
    Matchable,
    Equality,
    Variable,
    Term,
    Expression,
    Header,
    Reference,
)
from .functions.function_factory import FunctionFactory
from ..util.exceptions import ParsingException


@v_args(inline=True)
class LarkTransformer(Transformer):  # pylint: disable=C0115
    def __init__(self, matcher):
        self.matcher = matcher
        super().__init__()

    def match(self, *expressions):  # pylint: disable=C0116
        return [e for e in list(expressions) if e is not None]

    # left (WHEN action)?
    # equality (WHEN action)?
    # assignment
    # COMMENT
    def expression(self, acted_on, when=None, action=None):  # pylint: disable=C0116
        # print(f"expression: acted_on: {acted_on}, when: {when}, action: {action}")
        if acted_on is None and when is None and action is None:
            # this is a comment
            return None
        #
        #
        #
        e = Expression(self.matcher)
        if when is None:
            e.add_child(acted_on)
        else:
            eq = Equality(self.matcher)
            eq.left = acted_on
            eq.right = action
            eq.op = "->"
            e.add_child(eq)
        return e

    # (function|assignment)
    def action(self, arg):  # pylint: disable=C0116
        return arg

    # VARIABLE ASSIGN (left|TERM)
    def assignment(self, variable, equals, value):  # pylint: disable=C0116
        e = Equality(self.matcher)
        e.left = variable
        e.right = value
        e.op = equals
        return e

    # HEADER|VARIABLE|function
    def left(self, arg):  # pylint: disable=C0116
        return arg

    # left EQUALS (left|TERM)
    def equality(self, left, op, right):  # pylint: disable=W0613, C0116
        # re: W0613: in this case we don't care because we need the placeholder
        e = Equality(self.matcher)
        e.op = "=="
        e.left = left
        e.right = right
        return e

    # token
    def HEADER(self, token):  # pylint: disable=C0116, C0103
        h = Header(self.matcher, name=token.value[1:])
        return h

    # token
    def VARIABLE(self, token):  # pylint: disable=C0116, C0103
        v = Variable(self.matcher, name=token.value[1:])
        return v

    # token
    def REFERENCE(self, token):  # pylint: disable=C0116, C0103
        v = Reference(self.matcher, name=token.value[1:])
        return v

    # function: /[a-zA-Z][a-zA-Z-0-9\._]*/ args
    def function(self, name, args):  # pylint: disable=C0116
        f = FunctionFactory.get_function(self.matcher, name=f"{name}", child=args)
        return f

    def term(self, aterm):  # pylint: disable=C0116
        return aterm

    # LP RP
    # | LP a (COMMA a)* RP
    def args(self, *args):  # pylint: disable=C0116
        if len(args) == 3:
            return args[1]
        e = Equality(self.matcher)
        for _ in args:
            if isinstance(_, Matchable):
                e.children.append(_)
                _.parent = e
        if len(e.children) == 1:
            return e.children[0]
        if len(e.children) > 1:
            e.op = ","
            return e
        return None

    # TERM
    # VARIABLE
    # HEADER
    # function
    # equality
    def a(self, arg):  # pylint: disable=C0116
        return arg

    def TERM(self, token):  # pylint: disable=C0116, C0103
        t = None
        if isinstance(token, Token):
            t = token.value
            t = token.value
            if t[0] == "@" or t[0] == "#":
                t = token.value[1:-1]
            return Term(self.matcher, value=t)
        raise ParsingException(f"Cannot make a Term from a {type(token)}")

    # token
    def STRING(self, token):  # pylint: disable=C0116, C0103
        return Term(self.matcher, value=token.value[1:-1])

    # token
    def SIGNED_NUMBER(self, token):  # pylint: disable=C0116, C0103
        t = token.value
        if isinstance(token.value, (int, float)):
            pass
        elif f"{token.value}".find(".") > -1:
            t = float(token.value)
        else:
            t = int(token.value)
        return Term(self.matcher, value=t)

    # token
    def REGEX(self, token):  # pylint: disable=C0116, C0103
        return Term(self.matcher, value=token.value)

    # token
    def COMMENT(self, token):  # pylint: disable=C0116, C0103, W0613
        return None
