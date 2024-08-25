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
        assignment: VARIABLE ASSIGN (left|REFERENCE|term)
        equality: left EQUALS (left|REFERENCE|term)

        REFERENCE: /\$[a-zA-Z-0-9\_\.]+/
        HEADER: ( /#([a-zA-Z-0-9\._])+/ | /#"([a-zA-Z-0-9 \._])+"/ )
        VARIABLE: /@[a-zA-Z-0-9\_\.]+/
        function: /[a-zA-Z][a-zA-Z-0-9\._]*/ args
        args: LP RP
            | LP a (COMMA a)* RP
        a: term
         | VARIABLE
         | HEADER
         | function
         | equality
         | REFERENCE
        term: STRING | SIGNED_NUMBER | REGEX
        LP: "("
        RP: ")"
        _LS: "("
        _RS: ")"
        COMMA: ","
        STRING: /"[^"]*"/
        ASSIGN: "="
        WHEN: "->"
        EQUALS: "=="
        COMMENT: "~" /[^~]*/ "~"
        REGEX: "/" REGEX_INNER "/"
        REGEX_INNER: /([^\/\\\\]|\\\\.)*/
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
        self.tree = self.parser.parse(f"{matchpart}")
        return self.tree
