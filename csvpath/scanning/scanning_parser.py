import ply.yacc as yacc
from ply.yacc import YaccProduction
from csvpath.scanning.scanning_lexer import ScanningLexer
from csvpath.scanning.scanner import Scanner
from csvpath.parser_utility import ParserUtility
from typing import List, Tuple

class UnexpectedException(Exception):
    pass

class CsvPath(object):
    tokens = ScanningLexer.tokens

    def __init__(self):
        self.lexer = ScanningLexer()
        self.parser = yacc.yacc(module=self, start='path' )
        self.these:List = []
        self.all_lines = False
        self.filename = None
        self.from_line = None
        self.to_line = None
        self.path = None
        self.scan = None
        self.matches = None
        self.modify = None
        self.quiet = True
        print(f"initialized CsvPath: {self}")

    def __str__(self):
        return f"""
            path: {self.path}
            parser: {self.parser}
            lexer: {self.lexer}
            scan: {self.scan}
            matches: {self.matches}
            modify: {self.modify}
            filename: {self.filename}
            from_line: {self.from_line}
            to_line: {self.to_line}
            all_lines: {self.all_lines}
            these: {self.these}
        """

    def print_production(self, p:YaccProduction, label:str=None, override=False):
        if self.quiet and not override:
            return
        if label:
            label = f" at {label}"
        print(f"production array{label} is:")
        for _ in p:
            print(f"\t{_} \t-> {_.__class__}")

    def parse(self, data):
        scan, matches, modify = self._find_scan_match_modify(data)
        self.scan = scan
        self.matches = matches
        self.modify = modify
        self.path = data
        value = self.parser.parse(data, lexer=self.lexer.lexer)
        scanner = Scanner(parser=self, filename=self.filename)
        return scanner

    def _find_scan_match_modify(self, data):
        scan = ""
        matches = ""
        modify = ""
        p = 0
        for i, c in enumerate(data):
            if p == 0:
                scan = scan + c
            elif p == 1:
                matches = matches + c
            else:
                modify = modify + c
            if c == "]":
                p = p+1
        scan = scan.strip()
        matches = matches.strip()
        modify = modify.strip()
        return scan if len(scan) > 0 else None, matches if len(matches) > 0 else None, modify if len(modify) > 0 else None

    #===================
    # productions
    #===================

    def p_error(self, p):
        ParserUtility().error(self.parser, p)


    def p_root(self, p):
        '''root : ROOT |
                  ROOT filename'''
        self.print_production(p, 'root')

    def p_root(self, p):
        'root : ROOT filename'
        self.print_production(p, 'root : filename')

    def p_filename(self, p):
        'filename : FILENAME'
        self.print_production(p, 'filename : FILENAME')
        self.filename = p[1]

    def p_path(self, p):
        'path : root LEFT_BRACKET expression RIGHT_BRACKET'
        self.print_production(p, 'path : ROOT LEFT_BRACKET expression RIGHT_BRACKET')
        p[0] = p[3]

    #===================

    def p_expression(self, p):
        '''expression : expression PLUS term
                      | expression MINUS term
                      | term'''
        self.print_production(p, '''expression : expression PLUS term
                      | expression MINUS term
                      | term''')
        if len(p) == 4:
            if p[2] == '+':
                self._add_two_lines(p)
            elif p[2] == '-':
                self._collect_a_line_range(p)
        else:
            self._collect_a_line_number(p)
        p[0] = self.these if self.these else [self.from_line]


    def p_term(self, p):
        '''term : NUMBER
                | NUMBER ALL_LINES
                | ALL_LINES'''
        self.print_production(p, '''term : NUMBER
                | NUMBER ALL_LINES
                | ALL_LINES''' )

        if len(p) == 3:
            self.from_line = p[1]

        if p[len(p)-1] == '*':
            self.all_lines = True
        else:
            p[0] = [p[1]]

    #===================

    def _add_two_lines(self, p):
        self._move_range_to_these()
        if p[1] and p[1][0] not in self.these:
            self.these.extend(p[1])
        if p[3] and p[3][0] not in self.these:
            self.these.extend(p[3])

    def _collect_a_line_range(self, p):
        if not isinstance(p[1], list):
            raise UnexpectedException("non array in p[1]")
        #
        # if we continue to not raise unexpected exception we should remove the array tests!
        #
        if (self.from_line and self.to_line):
            # we have a from and to range. we have to move the range into
            # these, then add this new range to these too
            self._move_range_to_these()
            fline = p[1][0] if isinstance(p[1], list) else p[1]
            tline = p[3][0] if isinstance(p[3], list) else p[3]
            self._add_range_to_these(fline,tline)
        else:
            if isinstance(p[1], list) and len(p[1]) == 1:
                self.from_line = p[1][0]
                if len(self.these) == 1 and self.these[0] == self.from_line:
                    self.these = []
            elif isinstance(p[1], list):
                pass # this is a list of several items -- i.e. it is self.these
            else:
                raise UnexpectedException("non array in p[1]")
                self.from_line = p[1] # does this ever happen?

            if isinstance(p[3], list):
                self.to_line = p[3][0]
            else:
                raise UnexpectedException("non array in p[3]")
                self.to_line = p[3] # does this ever happen?
            # if we have a multi-element list on the left we set a range
            # using the last item in the list as the from_line and
            # the right side in the to_line. then we clear the range into these
            if isinstance(p[1], list) and len(p[1]) > 1:
                self.from_line = p[1][len(p[1])-1]
                self._move_range_to_these()

    def _collect_a_line_number(self, p):
        if isinstance(p[1], list):
            if p[1] and p[1][0] not in self.these:
                self.these.extend(p[1])
        elif not self.from_line:
            self.from_line = p[1]

    def _move_range_to_these(self):
        if not self.from_line or not self.to_line:
            return
        for i in range(self.from_line, self.to_line+1):
            if i not in self.these:
                self.these.append(i)
        self.from_line = None
        self.to_line = None

    def _add_range_to_these(self, fline, tline):
        for i in range(fline, tline+1):
            if i not in self.these:
                self.these.append(i)


