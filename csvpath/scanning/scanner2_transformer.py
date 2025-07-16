from lark import Transformer


class Scanner2Transformer(Transformer):
    def __init__(self, scanner) -> None:
        self.scanner = scanner
        self.stack = None
        self.is_wild = False

    def start(self, items):
        return items

    def instructions(self, inst):
        self.seek(inst)

    def seek(self, lst) -> None:
        if not isinstance(lst, list):
            raise ValueError("not a list: {lst}")
        if len(lst) >= 1:
            if lst[len(lst) - 1] == "*":
                lst.pop()
        if len(lst) == 1:
            if isinstance(lst[0], list):
                self.seek(lst[0])
            elif lst[0] == "*":
                return
            else:
                self.process(lst)
                return
        else:
            self.process(lst)
            return

    def process(self, line_nos) -> None:
        if not isinstance(line_nos, list):
            raise ValueError("not a list: {line_nos}")
        these = []
        op = None
        for num in line_nos:
            try:
                num = int(num)
            except Exception:
                ...
            if isinstance(num, int):
                if op == "-":
                    ffrom = these[len(these) - 1]
                    tto = num + 1
                    if ffrom > tto:
                        ffrom = num
                        tto = these[len(these) - 1] + 1
                    for _ in range(ffrom, tto):
                        if _ not in these:
                            these.append(_)
                    op = None
                elif isinstance(num, int) and op == "+":
                    these.append(num)
                    op = None
                elif isinstance(num, int) and op is None:
                    these.append(num)
            else:
                op = num
        these.sort()
        self.scanner.these = these

    def lines(self, these):
        return these

    def these(self, this):
        if len(this) == 3:
            _ = this.pop(2)
            for item in _:
                this.append(item)
        return this

    def this(self, an_int):
        return an_int[0]

    def alongwith(self, op):
        return op[0]

    def INTEGER(self, token):
        return token.value

    def PERCENT(self, token):
        #
        # percents are not currently used/supported. however, they
        # will make an excellent addition in the future when there is
        # time and demand for better sampling. building them into the
        # grammar keeps this direction open.
        #
        ...
        # return token.value

    def WILDCARD(self, token):
        self.scanner.wild_from_last = True
        return token.value

    def PLUS(self, token):
        return token.value

    def THROUGH(self, token):
        return token.value
