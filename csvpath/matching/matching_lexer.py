import ply.lex as lex

class MatchingLexer(object):
    tokens = [
                'NUMBER',
                'EQUALS',
                'LEFT_BRACKET',
                'RIGHT_BRACKET',
                'OPEN_PAREN',
                'CLOSE_PAREN',
                'HEADER_SYM',
                'VAR_SYM',
                'NAME',
                'REGEX',
                'QUOTE'
             ]

    t_ignore = ' \t\n\r'
    t_QUOTE = r'"'
    t_OPEN_PAREN = r'\('
    t_CLOSE_PAREN = r'\)'
    t_HEADER_SYM = r'\#'
    t_EQUALS = r'[=><,\*\+\-]'
    t_VAR_SYM = r'@'
    t_LEFT_BRACKET = r'\['
    t_RIGHT_BRACKET = r'\]'
    t_NAME = r'[A-Za-z0-9\.%_|]+'
    #t_NAME = r'[A-Za-z0-9][A-Za-z0-9\.%_]*'
    t_REGEX = r'/(?:[^/\\]|\\.)*/'


    def t_NUMBER(self, t):
        r'\d+'
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
