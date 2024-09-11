# pylint: disable=C0114
from ply import lex


class ScanningLexer:
    """support for the scanner's Ply-based parser"""

    tokens = [
        "NUMBER",
        "PLUS",
        "MINUS",
        "LEFT_BRACKET",
        "RIGHT_BRACKET",
        "ANY",
        "NAME",
        "FILENAME",
        "ALL_LINES",
    ]

    t_ignore = " \t\n\r"
    t_PLUS = r"\+"
    t_MINUS = r"-"
    t_LEFT_BRACKET = r"\["
    t_RIGHT_BRACKET = r"\]"
    t_ANY = r"\*"
    t_NAME = r"[A-Z,a-z,0-9\._]+"
    t_ALL_LINES = r"\*"

    def t_NUMBER(self, t):  # pylint: disable=C0103
        r"\d+"
        t.value = int(t.value)
        return t

    def t_FILENAME(self, t):  # pylint: disable=C0103
        r"\$[A-Z,a-z,0-9\._/\-\\#& ]*"
        return t

    def t_error(self, t):  # pylint: disable=C0116
        print(f"Illegal character '{t.value[0]}'")  # pragma: no cover
        t.lexer.skip(1)  # pragma: no cover

    def __init__(self):
        self.lexer = lex.lex(module=self)

    def tokenize(self, data):  # pylint: disable=C0116
        self.lexer.input(data)  # pragma: no cover
        while True:  # pragma: no cover
            tok = self.lexer.token()
            if not tok:
                break
            yield tok
