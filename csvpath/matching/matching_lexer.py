import ply.lex as lex


class MatchingLexer(object):
    tokens = [
        "DATE",
        "NAME",
        "NUMBER",
        "EQUALS",
        "OPERATION",
        "ASSIGNMENT",
        "LEFT_BRACKET",
        "RIGHT_BRACKET",
        "OPEN_PAREN",
        "CLOSE_PAREN",
        "HEADER_SYM",
        "VAR_SYM",
        "REGEX",
        "QUOTE",
    ]

    t_ignore = " \t\n\r"
    t_QUOTE = r'"'
    t_OPEN_PAREN = r"\("
    t_CLOSE_PAREN = r"\)"
    t_HEADER_SYM = r"\#"
    t_EQUALS = r"=="
    t_OPERATION = r"[><,\*\+\-]"
    t_ASSIGNMENT = r"="
    t_VAR_SYM = r"@"
    t_LEFT_BRACKET = r"\["
    t_RIGHT_BRACKET = r"\]"
    t_NAME = r"[\$A-Za-z0-9\.%_|\s \-:]+"
    t_REGEX = r"/(?:[^/\\]|\\.)*/"

    def t_DATE(self, t):
        r"\d+[/-]\d+[/-]\d+"
        return t

    def t_NUMBER(self, t):
        r"\d*\.?\d+"
        try:
            t.value = int(t.value)
        except ValueError:
            try:
                t.value = float(t.value)
            except ValueError:
                raise Exception(
                    f"matching_lexer.t_NUMBER: cannot convert {t}: {t.value}"
                )
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
