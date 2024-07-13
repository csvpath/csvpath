from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
from csvpath.matching.expression_encoder import ExpressionEncoder
from csvpath.matching.productions.equality import Equality


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
    ]

    def to_value(self, *, skip=[]) -> Any:
        if self.value is None:
            if len(self.children) != 1:
                raise ChildrenException(
                    "must be 1 equality child with a match and print string"
                )
            string = self.children[0].right.to_value()
            self.value = self.make_string(string)
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return None  # is this the right return val for this situtation?
        if len(self.children) != 1:
            print(
                f"Error: json of expressions: {ExpressionEncoder().valued_list_to_json(self.matcher.expressions)}"
            )
            raise ChildrenException(
                "must be 1 equality child with a match and print string"
            )
        if self.children[0].left.matches(skip=skip):
            print(f"{self.to_value()}")
            return True
        else:
            return False

    def make_string(self, string: str) -> str:
        for token in Print.TOKENS:
            if token == Print.TOKENS[8]:
                string = self.handle_variables(string)
            else:
                string = string.replace(token, self.value_of_token(token))
        return string

    def handle_variables(self, string) -> str:
        ret = ""
        start = string.find(Print.TOKENS[8])
        while start > -1:
            varname = None
            for _ in string[start + len(Print.TOKENS[8]) :]:
                if _ in (" ", ",", ";", "?"):
                    break
                elif _ == ".":
                    varname = ""
                elif varname is not None:
                    varname += _
            if varname is None:
                print("varname is None!!!")
                ret = str(self.matcher.csvpath.variables)
                string = string.replace(f"{Print.TOKENS[8]}", ret)
            else:
                print(f"varname is $.variables.{varname}")
                ret = f"{self.matcher.csvpath.variables.get(varname)}"
                string = string.replace(f"{Print.TOKENS[8]}.{varname}", ret)
            start = string.find(Print.TOKENS[8])
        return string

    def value_of_token(self, token) -> str:
        ret = None
        if token == Print.TOKENS[0]:
            ret = self.matcher.csvpath.filename
        elif token == Print.TOKENS[1]:
            ret = self.matcher.csvpath.delimiter
        elif token == Print.TOKENS[2]:
            ret = self.matcher.csvpath.quotechar
        elif token == Print.TOKENS[3]:
            ret = self.matcher.csvpath.match_count
        elif token == Print.TOKENS[4]:
            ret = self.matcher.csvpath.line_number
        elif token == Print.TOKENS[5]:
            ret = self.matcher.csvpath.scan_count
        elif token == Print.TOKENS[6]:
            ret = self.matcher.line
        elif token == Print.TOKENS[7]:
            ret = ExpressionEncoder().valued_list_to_json(self.matcher.expressions)
        elif token == Print.TOKENS[9]:
            ret = str(self.matcher.expressions)
        elif token == Print.TOKENS[10]:
            ret = str(self.matcher.headers)
        elif token == Print.TOKENS[11]:
            ret = str(self.matcher.csvpath.scan)
        elif token == Print.TOKENS[12]:
            ret = str(self.matcher.csvpath.match)
        return f"{ret}"
