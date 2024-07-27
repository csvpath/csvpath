import ply.lex as lex
from csvpath.matching.expression_utility import ExpressionUtility


class MatchingLexer(object):
    tokens = [
        "DATE",
        "DO",
        "LT",
        "GT",
        "STAR",
        "PLUS",
        "MINUS",
        "COMMA",
        "NUMBER",
        "EQUALS",
        "ASSIGNMENT",
        "LEFT_BRACKET",
        "RIGHT_BRACKET",
        "OPEN_PAREN",
        "CLOSE_PAREN",
        "HEADER_SYM",
        "VAR_SYM",
        "REGEX",
        "QUOTE",
        "NAME",
        "QUOTED",
        "NAME_LINE",
        "SIMPLE_NAME",
    ]

    t_ignore = " \t\n\r"
    t_QUOTE = r'"'
    t_OPEN_PAREN = r"\("
    t_CLOSE_PAREN = r"\)"
    t_HEADER_SYM = r"\#"
    t_EQUALS = r"=="
    t_DO = "->"
    t_LT = r"<"
    t_GT = r">"
    t_STAR = r"\*"
    t_PLUS = r"\+"
    t_MINUS = "-"
    t_COMMA = ","
    t_ASSIGNMENT = r"="
    t_VAR_SYM = r"@"
    t_LEFT_BRACKET = r"\["
    t_RIGHT_BRACKET = r"\]"
    t_NAME_LINE = r"[\$A-Za-z0-9\.%_|\s, :]+\n"
    #   t_SIMPLE_NAME = r"[A-Za-z]+"

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

    def t_REGEX(self, t):
        r"/(?:[^/\\]|\\.)*/"
        return t

    def t_QUOTED(self, t):
        r'"[\$A-Za-z0-9\.%_|\s :\\/,]+"'
        return t

    def t_SIMPLE_NAME(self, t):
        r"[A-Za-z0-9_\.]+\n?"
        t.value = t.value.strip()
        return t

    def t_NAME(self, t):
        r'"?[\$A-Za-z0-9\.%_|\s :\\/]+"?'
        s = str(t.value).strip()
        # print(f">>> t: {t.type}: {t.value}: alpha: {s.isalpha()}, numeric: {s.isdigit()} >>{s}<<")
        if ExpressionUtility.is_simple_name(s):
            t.type = "SIMPLE_NAME"
        elif s[0] == "/" and s[len(s) - 1] == "/":
            t.type = "REGEX"
        elif s[0] == '"' and s[len(s) - 1] == '"':
            t.type = "QUOTED"
        else:
            n = False
            try:
                float(s)
                n = True
            except Exception:
                pass
            if n:
                t.type = "NUMBER"
                # probably we should pass to t_NUMBER(), but for now is working
                if s.find(".") > -1:
                    t.value = float(s)
                else:
                    t.value = int(s)
        return t

    def t_DATE(self, t):
        r"\d+[/-]\d+[/-]\d+"
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
            print(f"MatchingLexer.tokenize: tok: {tok}")
            if not tok:
                break
            yield tok
