import logging

from .reference_exceptions_3 import ReferenceException3


#
# ReferenceExpressionParser3 turns a written reference expression into a
# tree of plain reference strings and operators -- issue #444. It knows
# nothing about CsvPaths or finders; ReferenceExpression3.from_string()
# builds the expression objects from the tree it returns.
#
# Written form (David, 2026-11-15):
#   - a side is a plain reference or a parenthesized expression:
#       $a.files.:last() UNION $b.files.:last()
#       ($a... UNION $b...) SUBTRACT $c...
#       $a... UNION ($b... INTERSECT $c...)
#   - operators are case-insensitive: UNION, union, Union
#   - more than one operator at one level raises: there is no precedence
#     yet, so grouping parentheses are required. Defining a precedence
#     later is non-breaking.
#
# An operator is a whole word at depth 0, outside a quoted string and a
# regex, with whitespace, a grouping parenthesis or the end of the text
# on both sides. A
# reference's own function parentheses, STRING args and REGEX args (see
# reference_grammar_3.py) are skipped, so :regex("x UNION y") and
# :regex(/a (b/) never split. A REGEX arg starts with a "/" right after
# a function's "(" or ","; any other "/" is a path separator.
#
# parse() returns either a plain reference string (no operator at the
# top level, e.g. "$a.files.:last()" or "($a.files.:last())") or a
# (left, op, right) tuple whose sides are themselves such trees. op is
# lowercase, matching ReferenceExpression3's own UNION/SUBTRACT/INTERSECT.
#
class ReferenceExpressionParser3:
    OPERATORS = ("union", "subtract", "intersect")

    @classmethod
    def parse(cls, expression: str) -> "str | tuple":
        if not isinstance(expression, str):
            raise TypeError("A reference expression must be a string")
        if expression.strip() == "":
            raise ValueError("A reference expression cannot be empty")
        parts = cls.split(expression)
        if len(parts) == 1:
            return cls._operand(parts[0], expression=expression)
        if len(parts) > 3:
            cls._raise(
                f"Use parentheses to group more than one operator: {expression!r}"
            )
        left, op, right = parts
        return (
            cls._operand(left, expression=expression),
            op,
            cls._operand(right, expression=expression),
        )

    @classmethod
    def is_expression(cls, expression: str) -> bool:
        return isinstance(cls.parse(expression), tuple)

    @classmethod
    def split(cls, expression: str) -> list[str]:
        """the top level of `expression` as [operand, op, operand, ...].
        Each operand is stripped text, which may be a group in
        parentheses; each op is lowercase. An empty operand raises."""
        if not isinstance(expression, str):
            raise TypeError("A reference expression must be a string")
        parts = []
        start = 0
        depth = 0
        i = 0
        n = len(expression)
        while i < n:
            c = expression[i]
            if c == '"':
                i = cls._end_of_quoted(expression, i, quote='"')
                continue
            if c == "/" and depth > 0 and cls._previous_char(expression, i) in "(,":
                i = cls._end_of_quoted(expression, i, quote="/")
                continue
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth < 0:
                    cls._raise(f"Unbalanced ')' at {i}: {expression!r}")
            elif depth == 0:
                op = cls._operator_at(expression, i)
                if op is not None:
                    parts.append(expression[start:i].strip())
                    parts.append(op)
                    i += len(op)
                    start = i
                    continue
            i += 1
        if depth != 0:
            cls._raise(f"Unbalanced '(': {expression!r}")
        parts.append(expression[start:].strip())
        for k in range(0, len(parts), 2):
            if parts[k] == "":
                op = parts[k + 1] if k + 1 < len(parts) else parts[k - 1]
                cls._raise(
                    "A reference expression needs a reference on both sides "
                    f"of {op.upper()}: {expression!r}"
                )
        return parts

    @classmethod
    def _operand(cls, text: str, *, expression: str) -> "str | tuple":
        if not text.startswith("("):
            return text
        close = cls._matching_paren(text)
        if close != len(text) - 1:
            cls._raise(
                f"Unexpected text after a group in {expression!r}: "
                f"{text[close + 1 :].strip()!r}"
            )
        inner = text[1:-1]
        if inner.strip() == "":
            cls._raise(f"Empty parentheses in {expression!r}")
        return cls.parse(inner)

    @classmethod
    def _matching_paren(cls, text: str) -> int:
        depth = 0
        i = 0
        while i < len(text):
            c = text[i]
            if c == '"':
                i = cls._end_of_quoted(text, i, quote='"')
                continue
            if c == "/" and depth > 0 and cls._previous_char(text, i) in "(,":
                i = cls._end_of_quoted(text, i, quote="/")
                continue
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        cls._raise(f"Unbalanced '(': {text!r}")

    @classmethod
    def _operator_at(cls, expression: str, i: int) -> str | None:
        if i > 0 and not (expression[i - 1].isspace() or expression[i - 1] == ")"):
            return None
        for op in cls.OPERATORS:
            end = i + len(op)
            if expression[i:end].lower() != op:
                continue
            if (
                end == len(expression)
                or expression[end].isspace()
                or expression[end] == "("
            ):
                return op
        return None

    @staticmethod
    def _previous_char(expression: str, i: int) -> str:
        j = i - 1
        while j >= 0 and expression[j].isspace():
            j -= 1
        return expression[j] if j >= 0 else ""

    @classmethod
    def _end_of_quoted(cls, expression: str, i: int, *, quote: str) -> int:
        """the index just past the quote that closes the one at i.
        A backslash escapes the next character, as in the grammar's
        STRING and REGEX_INNER."""
        j = i + 1
        while j < len(expression):
            if expression[j] == "\\":
                j += 2
                continue
            if expression[j] == quote:
                return j + 1
            j += 1
        what = "string" if quote == '"' else "regex"
        cls._raise(f"Unterminated {what} at {i}: {expression!r}")

    @classmethod
    def _raise(cls, msg: str) -> None:
        logging.getLogger(cls.__name__).error(msg)
        raise ReferenceException3(msg)
