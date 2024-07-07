import ply.lex as lex


class ScanningLexer(object):
    tokens = [
        "NUMBER",
        "PLUS",
        "MINUS",
        "LEFT_BRACKET",
        "RIGHT_BRACKET",
        "ROOT",
        "ANY",
        "NAME",
        "FILENAME",
        "ALL_LINES",
    ]

    t_ignore = " \t\n\r"
    t_ROOT = r"\$"
    t_PLUS = r"\+"
    t_MINUS = r"-"
    t_LEFT_BRACKET = r"\["
    t_RIGHT_BRACKET = r"\]"
    t_ANY = r"\*"  # not yet used
    t_NAME = r"[A-Z,a-z,0-9\._]+"
    t_FILENAME = r"[A-Z,a-z,0-9\._/]+"
    t_ALL_LINES = r"\*"

    def t_NUMBER(self, t):
        r"\d+"
        t.value = int(t.value)
        return t

    def t_error(self, t):
        print(f"Illegal character '{t.value[0]}'")
        t.lexer.skip(1)

    def __init__(self):
        self.lexer = lex.lex(module=self)

    def tokenize(self, data):
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            yield tok
