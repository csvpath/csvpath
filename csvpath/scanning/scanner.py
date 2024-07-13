import ply.yacc as yacc
from csvpath.scanning.scanning_lexer import ScanningLexer
from csvpath.parser_utility import ParserUtility
from typing import List


class UnexpectedException(Exception):
    pass


class Scanner(object):
    tokens = ScanningLexer.tokens

    def __init__(self):
        self.lexer = ScanningLexer()
        self.parser = yacc.yacc(module=self, start="path")
        self.these: List = []
        self.all_lines = False
        self.filename = None
        self.from_line = None
        self.to_line = None
        self.path = None
        self.quiet = True
        self.block_print = True
        self.print(f"initialized Scanner: {self}")

    def __str__(self):
        return f"""
            path: {self.path}
            parser: {self.parser}
            lexer: {self.lexer}
            filename: {self.filename}
            from_line: {self.from_line}
            to_line: {self.to_line}
            all_lines: {self.all_lines}
            these: {self.these}
        """

    def print(self, msg: str) -> None:
        if not self.block_print:
            print(msg)

    def includes(
        self,
        line: int,
        *,
        from_line: int = -1,
        to_line: int = -1,
        all_lines: bool = None,
        these: List[int] = None,
    ) -> bool:
        from_line = self.from_line if from_line == -1 else from_line
        to_line = self.to_line if to_line == -1 else to_line
        all_lines = self.all_lines if all_lines is None else all_lines
        these = self.these if these is None else these

        if line is None:
            return False
        elif from_line is None and all_lines:
            return True
        elif from_line is not None and all_lines:
            return line >= from_line
        elif from_line == line:
            return True
        elif from_line is not None and to_line is not None and from_line > to_line:
            return line >= to_line and line <= from_line
        elif from_line is not None and to_line is not None:
            return line >= from_line and line <= to_line
        elif line in these:
            return True
        elif to_line is not None:
            return line < to_line
        return False

    # ===================
    # parse
    # ===================

    def parse(self, data):
        self.path = data
        self.parser.parse(data, lexer=self.lexer.lexer)
        return self.parser

    # ===================
    # productions
    # ===================

    def p_error(self, p):
        ParserUtility().error(self.parser, p)

    # we'll want to use $name={ name: path} but for now we're treating filename as a file path
    def p_root(self, p):
        "root : ROOT filename"

    def p_filename(self, p):
        "filename : FILENAME"
        self.filename = p[1]

    def p_path(self, p):
        "path : root LEFT_BRACKET expression RIGHT_BRACKET"
        p[0] = p[3]

    # ===================

    def p_expression(self, p):
        """expression : expression PLUS term
        | expression MINUS term
        | term"""
        if len(p) == 4:
            if p[2] == "+":
                self._add_two_lines(p)
            elif p[2] == "-":
                self._collect_a_line_range(p)
        else:
            self._collect_a_line_number(p)
        p[0] = self.these if self.these else [self.from_line]

    def p_term(self, p):
        """term : NUMBER
        | NUMBER ALL_LINES
        | ALL_LINES"""

        if len(p) == 3:
            self.from_line = p[1]

        if p[len(p) - 1] == "*":
            self.all_lines = True
        else:
            p[0] = [p[1]]

    # ===================
    # production support
    # ===================

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
        if self.from_line and self.to_line:
            # we have a from and to range. we have to move the range into
            # these, then add this new range to these too
            self._move_range_to_these()
            fline = p[1][0] if isinstance(p[1], list) else p[1]
            tline = p[3][0] if isinstance(p[3], list) else p[3]
            self._add_range_to_these(fline, tline)
        else:
            if isinstance(p[1], list) and len(p[1]) == 1:
                self.from_line = p[1][0]
                if len(self.these) == 1 and self.these[0] == self.from_line:
                    self.these = []
            elif isinstance(p[1], list):
                pass  # this is a list of several items -- i.e. it is self.these
            else:
                raise UnexpectedException("non array in p[1]")
                self.from_line = p[1]  # does this ever happen?

            if isinstance(p[3], list):
                self.to_line = p[3][0]
            else:
                raise UnexpectedException("non array in p[3]")
                self.to_line = p[3]  # does this ever happen?
            # if we have a multi-element list on the left we set a range
            # using the last item in the list as the from_line and
            # the right side in the to_line. then we clear the range into these
            if isinstance(p[1], list) and len(p[1]) > 1:
                self.from_line = p[1][len(p[1]) - 1]
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
        for i in range(self.from_line, self.to_line + 1):
            if i not in self.these:
                self.these.append(i)
        self.from_line = None
        self.to_line = None

    def _add_range_to_these(self, fline, tline):
        for i in range(fline, tline + 1):
            if i not in self.these:
                self.these.append(i)
