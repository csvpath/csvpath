from lark import Transformer, v_args
from lark.tree import Tree
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
from .functions.function import Function
from .functions.function_factory import FunctionFactory


@v_args(inline=True)
class LarkTransformer(Transformer):
    def __init__(self, matcher):
        self.matcher = matcher

    def match(self, *expressions):
        return list(expressions)

    # left (WHEN action)?
    # equality (WHEN action)?
    # assignment
    # COMMENT
    def expression(self, acted_on, when=None, action=None):
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
    def action(self, arg):
        return arg

    # VARIABLE ASSIGN (left|TERM)
    def assignment(self, variable, equals, value):
        e = Equality(self.matcher)
        e.left = variable
        e.right = value
        e.op = equals
        return e

    # HEADER|VARIABLE|function
    def left(self, arg):
        return arg

    # left EQUALS (left|TERM)
    def equality(self, left, op, right):
        e = Equality(self.matcher)
        e.op = "=="
        e.left = left
        e.right = right
        return e

    # token
    def HEADER(self, token):
        h = Header(self.matcher, name=token.value[1:])
        return h

    # token
    def VARIABLE(self, token):
        v = Variable(self.matcher, name=token.value[1:])
        return v

    # token
    def REFERENCE(self, token):
        v = Reference(self.matcher, name=token.value[1:])
        return v

    # function: /[a-zA-Z][a-zA-Z-0-9\._]*/ args
    def function(self, name, args):
        f = FunctionFactory.get_function(self.matcher, name=f"{name}", child=args)
        return f

    def term(self, aterm):
        return aterm

    # LP RP
    # | LP a (COMMA a)* RP
    def args(self, *args):
        if len(args) == 3:
            return args[1]
        e = Equality(self.matcher)
        for _ in args:
            if isinstance(_, Matchable):
                e.children.append(_)
        if len(e.children) == 1:
            return e.children[0]
        elif len(e.children) > 1:
            e.op = ","
            return e
        else:
            return None

    # TERM
    # VARIABLE
    # HEADER
    # function
    # equality
    def a(self, arg):
        return arg

    def TERM(self, token):
        t = None
        if isinstance(token, Token):
            t = token.value
        elif isinstance(token, Tree):
            t = token
        if isinstance(token, Token):
            t = token.value
            if t[0] == "@" or t[0] == "#":
                t = token.value[1:-1]
            return Term(self.matcher, value=t)
        elif isinstance(token, Tree):
            raise Exception("Cannot make a Term from a Tree")

    # token
    def STRING(self, token):
        return Term(self.matcher, value=token.value[1:-1])

    # token
    def SIGNED_NUMBER(self, token):
        t = token.value
        if isinstance(token.value, int) or isinstance(token.value, float):
            pass
        elif f"{token.value}".find(".") > -1:
            t = float(token.value)
        else:
            t = int(token.value)
        return Term(self.matcher, value=t)

    # token
    def REGEX(self, token):
        return Term(self.matcher, value=token.value)

    # token
    def COMMENT(self, token):
        return None
