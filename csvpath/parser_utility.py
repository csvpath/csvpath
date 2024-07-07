from ply.yacc import YaccProduction


class ParserUtility:
    def __init__(self, quiet=True):
        self._quiet = quiet

    def error(self, parser, p: YaccProduction) -> None:
        if self._quiet and False:
            return
        # print(f"ParserUtility.error: {p}")
        if p:
            print(
                f"syntax error at token {p.type}, line {p.lineno}, position {p.lexpos}"
            )
            print(f"unexpected token: {p.value}")
            stack = parser.symstack
            print(f"symbol stack: {stack}")
        else:
            print("syntax error at EOF")

    def print_production(
        self, p: YaccProduction, label: str = None, override=True
    ) -> None:
        if self._quiet and not override:
            return
        if label:
            label = f" at {label}"
        print(f"production array{label} is:")
        for _ in p:
            print(f"\t{_} \t-> {_.__class__}")

    @classmethod
    def enumerate_p(self, message, p, quiet=True):
        if quiet:
            return
        print(f"Enumerate {p}: {message}:")
        for i, _ in enumerate(p):
            print(f"   p[{i}]: {_}")
