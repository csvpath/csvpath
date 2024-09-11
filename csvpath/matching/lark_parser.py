# pylint: disable=C0114
from lark import Lark


class LarkParser:  # pylint: disable=R0903
    """LarkParser implements the match part of CsvPath. is the replacement for the
    original Ply parser. It offers easier control of the grammar and a more
    intuitative way of building the parse tree. until 1.0 all of the four parsers
    in CsvPath should be considered under active development."""

    GRAMMAR = r"""
        match: _LB (expression)* _RB
        expression: left (WHEN action)?
                  | REFERENCE (WHEN action)?
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
        REGEX_INNER: /([^\/\\\\]|\\\\.|\\.)*/
        _LB: "["
        _RB: "]"
        %import common.SIGNED_NUMBER
        %import common.WS
        %ignore WS

    """

    def __init__(self):  # pylint: disable=C0116
        self.parser = Lark(LarkParser.GRAMMAR, start="match", ambiguity="explicit")
        self.tree = None

    def parse(self, matchpart):  # pylint: disable=C0116
        self.tree = self.parser.parse(f"{matchpart}")
        return self.tree
