from ply.yacc import YaccProduction
from typing import List


class ParserUtility:
    def __init__(self, quiet=False):  # pragma: no cover
        self._quiet = False  # TODO: remove me

    def error(self, parser, p: YaccProduction) -> None:
        if p:
            print(
                f"syntax error at token {p.type}, line {p.lineno}, position {p.lexpos}"
            )
            print(f"unexpected token: {p.value}")
            print("symbol stack: ")
            stack = parser.symstack

            import inspect

            for _ in stack:
                print(f"  {_}")
            print("")
        else:
            print("syntax error at EOF")

    def print_production(
        self, p: List[YaccProduction], label: str = None, override=True
    ) -> None:
        if self._quiet and not override:
            return
        print("Productions:")
        try:
            for _ in p:
                print(f"     {_}")
        except Exception:
            pass
        print("")

    @classmethod
    def enumerate_p(self, message, p, quiet=True):
        if quiet:
            return
        print(f"Enumerate {p}: {message}:")
        for i, _ in enumerate(p):
            print(f"   p[{i}]: {_}")
