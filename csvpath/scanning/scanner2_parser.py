from lark import Lark
from lark.visitors import Transformer
from .scanner2_transformer import Scanner2Transformer


class Scanner2Parser(Transformer):

    GRAMMAR = r"""
        ?start: instructions

        instructions: "[" (WILDCARD | lines) "]"

        lines: these WILDCARD?
        these: this (alongwith these)?
        this: INTEGER PERCENT?
        alongwith: (PLUS|THROUGH)

        INTEGER: /\d+/
        WILDCARD: "*"
        PLUS: "+"
        THROUGH: "-"
        PERCENT: "%"

        %import common.WS
        %ignore WS
    """

    def __init__(self, scanner) -> None:
        self.scanner = scanner

    #
    # instr is just the [...] containing the scanning instructions. the rest of
    # the csvpath must already be stripped away.
    #
    def parse_instructions(self, instr: str) -> bool:
        parser = Lark(
            Scanner2Parser.GRAMMAR,
            parser="lalr",
            start="start",
            transformer=Scanner2Transformer(self.scanner),
        )
        try:
            parser.parse(instr)
            return True
        except Exception as e:
            print(f"Scanner2: error for instructions {instr}: {e}")
            raise
