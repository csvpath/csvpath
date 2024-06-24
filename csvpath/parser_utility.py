from ply.yacc import YaccProduction

class ParserUtility:

    def __init__(self, quiet=True):
        self._quiet = quiet

    def error(self, parser, p:YaccProduction) -> None:
        if p:
            print(f"syntax error at token {p.type}, line {p.lineno}, position {p.lexpos}")
            print(f"unexpected token: {p.value}")
            stack = parser.symstack
            print(f"symbol stack: {stack}")
        else:
            print("syntax error at EOF")

    def print_production(self, p:YaccProduction, label:str=None, override=True) -> None:
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

    def get_id(self, thing):
        # gets a durable ID so funcs like count() can persist throughout the scan
        if not thing.id:
            id = str(self)
            p = thing.parent
            while not isinstance(p, Expression):
                id = id + str(p)
                p = p.parent
            id = id + str(p)
            import hashlib
            id = hashlib.sha256(id.encode('utf-8')).hexdigest()
            thing.id = id
        #print(f"!! func/att id = {self.id}")
        return thing.id



