import ply.yacc as yacc
from ply.yacc import YaccProduction
from csvpath.matching.matching_lexer import MatchingLexer
from csvpath.parser_utility import ParserUtility
from csvpath.matching.productions.expression import Expression
from csvpath.matching.productions.equality import Equality
from csvpath.matching.productions.term import Term
from csvpath.matching.productions.variable import Variable
from csvpath.matching.productions.header import Header
from csvpath.matching.functions.function_factory import FunctionFactory
from csvpath.matching.functions.function import Function
from typing import Any

class InputException(Exception):
    pass

class Matcher:
    tokens = MatchingLexer.tokens

    def __init__(self, *, csvpath=None, data=None, line=None, headers=None):
        if not headers:
            #raise Exception("no headers!")
            print("\nWARNING: no headers available. this is only Ok for unit testing.")
        if not data:
            raise InputException(f"need data input: data: {data}")
        self.path = data
        self.csvpath = csvpath
        self.line = line
        self.headers = headers
        self.expressions = []
        self.lexer = MatchingLexer()
        self.block_print = csvpath.block_print if csvpath else True
        self.parser = yacc.yacc(module=self, start='match_part' )
        value = self.parser.parse(data, lexer=self.lexer.lexer)

    def __str__(self):
        return f"""
            line: {self.line}
            csvpath: {self.csvpath}
            parser: {self.parser}
            lexer: {self.lexer}
        """

    def print(self, msg:str) -> None:
        if self.csvpath:
            self.csvpath.print(msg)

    def header_index(self, name:str) -> int:
        if not self.headers:
            return None
        for i, n in enumerate(self.headers):
            self.print(f" ...header {i} = {n} ?= {name}")
            if n == name:
                return i
        return None

    def matches(self, *, syntax_only=False) -> bool:
        ret = True
        for i, et in enumerate( self.expressions ):
            if et[1] is True:
                ret = True
            elif et[1] is False:
                ret = False
            elif not et[0].matches(skip=[]) and not syntax_only:
                et[1] = False
                ret = False
            else:
                et[1] = True
                ret = True
            if not ret:
                break
        return ret

    def get_variable(self, name:str,*, tracking=None, set_if_none=None) -> Any:
        return self.csvpath.get_variable(name, tracking=tracking, set_if_none=set_if_none)

    def set_variable(self, name:str, *, value:Any, tracking=None) -> None:
        self.print(f"Matcher.set_variable: {name} = {value} for {tracking}")
        return self.csvpath.set_variable(name, value=value, tracking=tracking)


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

    def p_expressions(self, p):
        '''expressions : expression
                       | expressions expression
        '''

    def p_expression(self, p):
        '''expression : function
                        | equality
                        | header '''
        e = Expression(self)
        e.add_child(p[1])
        self.expressions.append([e,None])
        p[0] = e

    def p_function(self, p):
        '''function : NAME OPEN_PAREN CLOSE_PAREN
                    | NAME OPEN_PAREN equality CLOSE_PAREN
                    | NAME OPEN_PAREN function CLOSE_PAREN
                    | NAME OPEN_PAREN var_or_header CLOSE_PAREN
                    | NAME OPEN_PAREN term CLOSE_PAREN
        '''
        name = p[1]
        child = p[3] if p and len(p)==5 else None
        f = FunctionFactory.get_function(self, name=name, child=child)
        ParserUtility.enumerate_p("IN p_function", p)
        p[0] = f

    def p_equality(self, p):
        '''equality : function EQUALS term
                    | function EQUALS var_or_header
                    | var_or_header EQUALS function
                    | var_or_header EQUALS term
                    | var_or_header EQUALS var_or_header
                    | term EQUALS var_or_header
                    | term EQUALS term
                    | term EQUALS function
                    | equality EQUALS equality
                    | equality EQUALS term
        '''
        e = Equality(self)
        e.set_left(p[1])
        e.set_operation(p[2])
        e.set_right(p[3])
        p[0] = e

        """
        if isinstance(p[1], Variable):
            self.csvpath.set_variable(p[1].name, value=p[3].to_value())

        if isinstance(p[3],Variable):
            self.csvpath.set_variable(p[3].name, value=p[1].to_value())
        """

    def p_term(self, p):
        '''term : QUOTE NAME QUOTE
                | QUOTE DATE QUOTE
                | QUOTE NUMBER QUOTE
                | NUMBER
                | REGEX
        '''
        if len(p) == 4:
            p[0] = Term(self, value=p[2])
        else:
            p[0] = Term(self, value=p[1])

    def p_var_or_header(self, p):
        '''var_or_header : header
                         | var
        '''
        p[0] = p[1]

    def p_var(self, p):
        '''var : VAR_SYM NAME '''
        v = Variable(self, name=p[2])
        p[0] = v

    def p_header(self, p):
        '''header : HEADER_SYM NAME
                  | HEADER_SYM NUMBER
        '''
        h = Header(self, name=p[2])
        p[0] = h




