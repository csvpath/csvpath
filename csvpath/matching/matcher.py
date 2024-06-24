import ply.yacc as yacc
from ply.yacc import YaccProduction
from csvpath.matching.matching_lexer import MatchingLexer
from csvpath.parser_utility import ParserUtility
from csvpath.matching.expression import Expression, Function, Equality, Term, Variable, Header
from csvpath.matching.functions import Count, Regex
from csvpath.matching.function_factory import FunctionFactory

from typing import Any

class InputException(Exception):
    pass

class Matcher:
    tokens = MatchingLexer.tokens

    def __init__(self, *, csvpath=None, data=None, line=None, headers=None):
        if not headers:
            print("\nWARNING: no headers available. this is only Ok for unit testing.")
        if not data:
            raise InputException(f"need data input: data: {data}")
        self.csvpath = csvpath
        self.line = line
        self.headers = headers
        self.expressions = []
        self.lexer = MatchingLexer()
        self.parser = yacc.yacc(module=self, start='match_part' )
        value = self.parser.parse(data, lexer=self.lexer.lexer)



    def __str__(self):
        return f"""
            line: {self.line}
            csvpath: {self.csvpath}
            parser: {self.parser}
            lexer: {self.lexer}
        """

    def matches(self, *, syntax_only=False) -> bool:
        for i, e in enumerate( self.expressions ):
            #print(f" ...{i}: {e}")
            if not e.matches() and not syntax_only:
                return False
        return True

    def get_variable(self, name:str) -> Any:
        return self.csvpath.get_variable(name)

    def set_variable(self, name:str, value:Any) -> None:
        return self.csvpath.set_variable(name, value)


    #===================
    # productions
    #===================


    def p_error(self, p):
        ParserUtility().error(self.parser, p)
        raise InputException("halting for error")


    def p_match_part(self, p):
        '''match_part : LEFT_BRACKET expression RIGHT_BRACKET
                      | LEFT_BRACKET expressions RIGHT_BRACKET
        '''
        ParserUtility().print_production(p, '''match_part : LEFT_BRACKET expression RIGHT_BRACKET
                      | LEFT_BRACKET expressions RIGHT_BRACKET
        ''')
        p[0] = p[2]

    def p_expressions(self, p):
        '''expressions : expression
                       | expressions expression
        '''
        ParserUtility().print_production(p, '''expressions : expression
                       | expressions expression
        ''')
        p[0]

    def p_expression(self, p):
        '''expression : function
                        | equality
                        | header '''
        ParserUtility().print_production(p, '''expression : function
                        | equality
                        | header ''')
        ParserUtility.enumerate_p("IN p_expression", p)
        e = Expression(self, p[1])
        if p[1]:
            p[1].parent = e
        self.expressions.append(e)

    def p_function(self, p):
        '''function : NAME OPEN_PAREN CLOSE_PAREN
                    | NAME OPEN_PAREN equality CLOSE_PAREN
                    | NAME OPEN_PAREN function CLOSE_PAREN
        '''
        ParserUtility().print_production(p, '''function : NAME OPEN_PAREN CLOSE_PAREN
                    | NAME OPEN_PAREN equality CLOSE_PAREN
                    | NAME OPEN_PAREN function CLOSE_PAREN
        ''')
        # p[3] is the nested equality or function, if there is one
        f = FunctionFactory.get_function(self, p[1], p)
        ParserUtility.enumerate_p("IN p_function", p)
        if p[3] and isinstance( p[3], YaccProduction):
            p[3].parent = f
        p[0] = f

    def p_equality(self, p):
        '''equality : function EQUALS term
                    | var_or_header EQUALS term
                    | var_or_header EQUALS var_or_header
                    | term EQUALS var_or_header
                    | term EQUALS function
                    | var_or_header EQUALS function
                    | var EQUALS header
        '''
        ParserUtility().print_production(p,         '''equality : function EQUALS term
                    | var_or_header EQUALS term
                    | var_or_header EQUALS var_or_header
                    | term EQUALS var_or_header
                    | term EQUALS function
                    | var_or_header EQUALS function
                    | var EQUALS header
        ''')
        e = Equality(self, p[1], p[3])
        p[0] = e
        p[1].parent = e
        p[3].parent = e

    def p_term(self, p):
        '''term : QUOTE NAME QUOTE
                | NUMBER
                | REGEX
        '''
        ParserUtility().print_production(p, '''term : QUOTE NAME QUOTE
                | NUMBER | REGEX
        ''')
        if len(p) == 4:
            p[0] = Term(self, p[2])
        else:
            p[0] = Term(self, p[1])

    def p_var_or_header(self, p):
        '''var_or_header : header
                         | var
        '''
        ParserUtility().print_production(p, '''var_or_header : header
                         | var
        ''')
        p[0] = p[1]

    def p_var(self, p):
        '''var : VAR_SYM NAME '''
        ParserUtility().print_production(p, '''var : VAR_SYM NAME ''')
        v = Variable(self, p[2])
        p[0] = v

    def p_header(self, p):
        '''header : HEADER_SYM NAME
                  | HEADER_SYM NUMBER
        '''
        ParserUtility().print_production(p, '''header : HEADER_SYM NAME
                  | HEADER_SYM NUMBER
        ''')
        h = Header(self, p[2])
        p[0] = h




