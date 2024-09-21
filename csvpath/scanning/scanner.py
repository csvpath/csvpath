# pylint: disable=C0114
from typing import List
from ply import yacc
from ply.yacc import YaccProduction
from .exceptions import ScanException, UnexpectedProductionException
from .scanning_lexer import ScanningLexer


class Scanner:  # pylint: disable=R0902
    """scanner is responsible for picking out what lines will be considered from a file"""

    # re: R0902: attributes all required. could pack
    # them up, but not worth it.
    tokens = ScanningLexer.tokens

    def __init__(self, csvpath=None):
        self.csvpath = csvpath
        self.lexer = ScanningLexer()
        self.parser = yacc.yacc(module=self, start="path")
        self.these: List = []
        self.all_lines = False
        self.filename = None
        self.from_line = None
        self.to_line = None
        self.path = None
        self.quiet = True
        if self.csvpath:
            self.csvpath.logger.info("initialized Scanner")

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

    def is_last(  # pylint: disable=R0913
        self,
        line: int,
        *,
        from_line: int = -1,
        to_line: int = -1,
        all_lines: bool = None,
        these: List[int] = None,
    ) -> bool:
        """identifies the last line to be scanned"""
        from_line = self.from_line if from_line == -1 else from_line
        to_line = self.to_line if to_line == -1 else to_line
        all_lines = self.all_lines if all_lines is None else all_lines
        these = self.these if these is None else these
        #
        # what if from is > to? shouldn't be but we originally wanted
        # to support that, way back, so we can do this swap.
        #
        if from_line and to_line and from_line > to_line:
            _ = from_line
            from_line = to_line
            to_line = _

        # end exp
        if all_lines:
            return (
                line == self.csvpath.line_monitor.physical_end_line_number
            )  # total_lines + 1
        if line == to_line:
            return True
        if len(these) > 0 and max(these) == line and not to_line and not all_lines:
            return True
        return False

    def includes(  # pylint: disable=R0913
        self,
        line: int,
        *,
        from_line: int = -1,
        to_line: int = -1,
        all_lines: bool = None,
        these: List[int] = None,
    ) -> bool:
        """determines if a line is included in scanning"""
        from_line = self.from_line if from_line == -1 else from_line
        to_line = self.to_line if to_line == -1 else to_line
        all_lines = self.all_lines if all_lines is None else all_lines
        these = self.these if these is None else these
        ret = None
        if line is None:
            ret = False
        elif from_line is None and all_lines:
            ret = True
        elif from_line is not None and all_lines:
            ret = line >= from_line
        elif from_line == line:
            ret = True
        elif from_line is not None and to_line is not None and from_line > to_line:
            ret = to_line <= line <= from_line
            # return line >= to_line and line <= from_line
        elif from_line is not None and to_line is not None:
            ret = from_line <= line <= to_line
            # return line >= from_line and line <= to_line
        elif line in these:
            ret = True
        elif to_line is not None:
            ret = line < to_line
        if ret is None:
            ret = False
        return ret

    # ===================
    # parse
    # ===================

    def parse(self, data):
        """loads the scanner and parses the scan part of the csvpath"""
        self.path = data
        self.parser.parse(data, lexer=self.lexer.lexer)
        return self.parser

    # ===================
    # productions
    # ===================

    def _error(self, parser, p: YaccProduction) -> None:
        if p:
            print(
                f"Syntax error at token {p.type}, line {p.lineno}, position {p.lexpos}"
            )
            print(f"Unexpected token: {p.value}")
            print("Symbol stack: ")
            stack = parser.symstack

            import inspect

            for _ in stack:
                print(f"  {_}")
            print("")
        else:
            print("syntax error at EOF")

    def p_error(self, p):  # pylint: disable=C0116
        if p:
            print(
                f"syntax error at token {p.type}, line {p.lineno}, position {p.lexpos}"
            )
            print(f"unexpected token: {p.value}")
            print("symbol stack: ")
            stack = self.parser.symstack

            import inspect

            for _ in stack:
                print(f"  {_}")
            print("")
        else:
            print("syntax error at EOF")
        raise ScanException(f"Halting for scanner parsing error on {self.path}")

    def p_path(self, p):  # pylint: disable=C0116
        "path : FILENAME LEFT_BRACKET expression RIGHT_BRACKET"
        filename = p[1].strip()
        if filename[0] != "$":
            raise ScanException("Filename must begin with '$'")  # pragma: no cover
        self.filename = filename[1:]
        p[0] = p[3]

    # ===================

    def p_expression(self, p):  # pylint: disable=C0116
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

    def p_term(self, p):  # pylint: disable=C0116
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

    def _add_two_lines(self, p):  # pylint: disable=C0116
        self._move_range_to_these()
        if p[1] and p[1][0] not in self.these:
            self.these.extend(p[1])
        if p[3] and p[3][0] not in self.these:
            self.these.extend(p[3])

    def _collect_a_line_range(self, p):  # pylint: disable=C0116
        if not isinstance(p[1], list):
            raise UnexpectedProductionException(
                "Non array in p[1]. You should fix this."
            )
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
                raise UnexpectedProductionException(
                    "Non array in p[1]. You should fix this."
                )
                # self.from_line = p[1]  # does this ever happen?
            if isinstance(p[3], list):
                self.to_line = p[3][0]
            else:
                raise UnexpectedProductionException(
                    "Non array in p[3]. You should fix this."
                )
                # self.to_line = p[3]  # does this ever happen?
            # if we have a multi-element list on the left we set a range
            # using the last item in the list as the from_line and
            # the right side in the to_line. then we clear the range into these
            if isinstance(p[1], list) and len(p[1]) > 1:
                self.from_line = p[1][len(p[1]) - 1]
                self._move_range_to_these()

    def _collect_a_line_number(self, p):  # pylint: disable=C0116
        if isinstance(p[1], list):
            if p[1] and p[1][0] not in self.these:
                self.these.extend(p[1])
        elif not self.from_line:
            self.from_line = p[1]

    def _move_range_to_these(self):  # pylint: disable=C0116
        if not self.from_line or not self.to_line:
            return
        for i in range(self.from_line, self.to_line + 1):
            if i not in self.these:
                self.these.append(i)
        self.from_line = None
        self.to_line = None

    def _add_range_to_these(self, fline, tline):  # pylint: disable=C0116
        for i in range(fline, tline + 1):
            if i not in self.these:
                self.these.append(i)
