from lark import Lark
from lark.tree import Tree
from lark.lexer import Token
import os
from .productions import *


class LarkParser:

    GRAMMAR = r"""
        match: _LB (expression)* _RB
        expression: left (WHEN action)?
                  | equality (WHEN action)?
                  | assignment
                  | COMMENT

        action: (function|assignment)
        left: HEADER|VARIABLE|function
        assignment: VARIABLE ASSIGN (left|(STRING | SIGNED_NUMBER | REGEX))
        equality: left EQUALS (left|(STRING | SIGNED_NUMBER | REGEX))

        HEADER: ( /#([a-zA-Z-0-9\.])+/ | /#"([a-zA-Z-0-9 \.])+"/ )
        VARIABLE: /@[a-zA-Z-0-9\_\.]+/
        function: /[a-zA-Z][a-zA-Z-0-9\._]*/ args
        args: LP RP
            | LP a (COMMA a)* RP
        a: (STRING | SIGNED_NUMBER | REGEX)
         | VARIABLE
         | HEADER
         | function
         | equality

        LP: "("
        RP: ")"
        COMMA: ","
        STRING: /"[^"]*"/
        ASSIGN: "="
        WHEN: "->"
        EQUALS: "=="
        COMMENT: "~" /[^~]*/ "~"
        REGEX: /\/(?!\/)(\\\/|\\\\|[^\/])*?\/[imslux]*/
        _LB: "["
        _RB: "]"
        %import common.SIGNED_NUMBER
        %import common.WS
        %ignore WS

    """

    def __init__(self):
        self.parser = Lark(LarkParser.GRAMMAR, start="match", ambiguity="explicit")
        self.tree = None

    def parse(self, matchpart):
        self.tree = self.parser.parse(matchpart)
        return self.tree