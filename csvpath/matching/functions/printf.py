from typing import Any
from .function import Function, ChildrenException
from ..productions import Equality, Term
from csvpath.matching.expression_encoder import ExpressionEncoder


class Print(Function):
    TOKENS = [
        "$.name",
        "$.delimiter",
        "$.quotechar",
        "$.match_count",
        "$.line_count",
        "$.scan_count",
        "$.line",
        "$.match_json",
        "$.variables",
        "$.expressions",
        "$.headers",
        "$.scan_part",
        "$.match_part",
        "$.last_row_time",
        "$.rows_time",
        "$.total_lines",
    ]

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return self._noop_value()
        if self.value is None:
            if len(self.children) != 1:
                raise ChildrenException("must be 1 term child")
            string = self.children[0].to_value()
            self.value = self.make_string(string)
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return self._noop_match()
        if len(self.children) != 1:
            raise ChildrenException("must be 1 child, equality or print string")
        if self.match is None:
            om = self.has_onmatch()
            if om:
                lm = self.line_matches()
                if lm:
                    print(f"{self.to_value()}")
                    self.match = True
            else:
                print(f"{self.to_value()}")
                self.match = True
        return self.match

    def make_string(self, string: str) -> str:
        for token in Print.TOKENS:
            if token == Print.TOKENS[8]:
                tstring = self.handle_variables(string)
                while tstring != string:
                    string = tstring
                    tstring = self.handle_variables(tstring)
                string = tstring
            elif token == Print.TOKENS[10]:
                tstring = self.handle_headers(string)
                while tstring != string:
                    string = tstring
                    tstring = self.handle_headers(tstring)
                string = tstring
            else:
                string = string.replace(
                    token, Print.value_of_token(self.matcher, token)
                )
        return string

    def handle_variables(self, string) -> str:
        ret = ""
        start = string.find(Print.TOKENS[8])
        if start > -1:
            varname = None
            i = start + len(Print.TOKENS[8])
            for _ in string[i:]:
                if _ in (" ", ",", ";", "?") or ord(_) in (10, 13, 9):
                    break
                elif _ == "." and varname is not None:
                    break
                elif _ == ".":
                    varname = ""
                elif varname is not None:
                    varname += _
            if varname is None:
                ret = str(self.matcher.csvpath.variables)
                string = string.replace(f"{Print.TOKENS[8]}", ret, 1)
            else:
                ret = f"{self.matcher.csvpath.variables.get(varname)}"
                string = string.replace(f"{Print.TOKENS[8]}.{varname}", ret, 1)
        return string

    def handle_headers(self, string) -> str:
        ret = ""
        start = string.find(Print.TOKENS[10])
        if start > -1:
            hname = None
            i = start + len(Print.TOKENS[10])
            for _ in string[i:]:
                if _ in (" ", ",", ";", "?") or ord(_) in (10, 13, 9):
                    break
                elif _ == "." and hname is not None:
                    break
                elif _ == ".":
                    hname = ""
                elif hname is not None:
                    hname += _
            if hname is None:
                retlist = []
                for h in self.matcher.csvpath.headers:
                    retlist.append(h)
                ret = f"{retlist}"
                string = string.replace(f"{Print.TOKENS[10]}", ret, 1)
            else:
                ret = f"{self.matcher.header_value(hname)}"
                string = string.replace(f"{Print.TOKENS[10]}.{hname}", ret, 1)
        return string

    @classmethod
    def tokens(self, matcher) -> list:
        ts = {}
        for t in Print.TOKENS:
            ts[t] = self.value_of_token(matcher, t)
        return ts

    @classmethod
    def value_of_token(self, matcher, token) -> str:
        ret = None
        if token == Print.TOKENS[0]:
            ret = matcher.csvpath.scanner.filename
        elif token == Print.TOKENS[1]:
            ret = matcher.csvpath.delimiter
        elif token == Print.TOKENS[2]:
            ret = matcher.csvpath.quotechar
        elif token == Print.TOKENS[3]:
            ret = matcher.csvpath.match_count
        elif token == Print.TOKENS[4]:
            ret = matcher.csvpath.line_number
        elif token == Print.TOKENS[5]:
            ret = matcher.csvpath.scan_count
        elif token == Print.TOKENS[6]:
            ret = matcher.line
        elif token == Print.TOKENS[7]:
            ret = ExpressionEncoder().valued_list_to_json(matcher.expressions)
        elif token == Print.TOKENS[9]:
            ret = str(matcher.expressions)
        elif token == Print.TOKENS[10]:
            ret = str(matcher.headers)
        elif token == Print.TOKENS[11]:
            ret = str(matcher.csvpath.scan)
        elif token == Print.TOKENS[12]:
            ret = str(matcher.csvpath.match)
        elif token == Print.TOKENS[13]:
            ret = str(matcher.csvpath.last_row_time)
        elif token == Print.TOKENS[14]:
            ret = str(matcher.csvpath.rows_time)
        elif token == Print.TOKENS[15]:
            ret = str(matcher.csvpath.total_lines)
        return f"{ret}"
