import logging
from typing import NoReturn

from .reference_exceptions_3 import ReferenceException3


#
# ReferenceExpressionParser3 turns a written reference expression into a
# tree of plain reference strings and operators -- issue #444. It knows
# nothing about CsvPaths or finders; ReferenceExpression3.from_tree()
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
# regex, with whitespace (the grammar's WS: space, tab, form feed, CR,
# LF), a grouping parenthesis or the end of the text on both sides. A
# reference's own function parentheses, STRING args and REGEX args (see
# reference_grammar_3.py) are skipped, so :regex("x UNION y") and
# :regex(/a (b/) never split. A function takes at most one arg, so a
# REGEX arg starts with a "/" right after a function's "("; any other
# "/" is a path separator.
#
# Operator words are reserved at the expression level (decision D26):
# the grammar ignores whitespace, so "$acme.files. union" is a valid
# plain reference to a name_one "union", but here it is an operator. Such
# text splits into sides that fail to parse as references, so it fails
# loudly, at the latest when the expression resolves.
#
# parse() returns either a plain reference string (no operator at the
# top level, e.g. "$a.files.:last()" or "($a.files.:last())") or a
# (left, op, right) tuple whose sides are themselves such trees. op is
# lowercase, matching ReferenceExpression3's own UNION/SUBTRACT/INTERSECT.
#
class ReferenceExpressionParser3:
    OPERATORS = ("union", "subtract", "intersect")
    WHITESPACE = " \t\f\r\n"

    @classmethod
    def parse(cls, expression: str) -> "str | tuple":
        cls._check_input(expression)
        return cls._parse(text=expression, whole=expression)

    @classmethod
    def is_expression(cls, expression: str) -> bool:
        return isinstance(cls.parse(expression), tuple)

    @classmethod
    def split(cls, expression: str) -> list[str]:
        """the top level of `expression` as [operand, op, operand, ...].
        Each operand is stripped text, which may be a group in
        parentheses; each op is lowercase. An empty operand raises."""
        cls._check_input(expression)
        return cls._split(text=expression, whole=expression)

    @classmethod
    def _parse(cls, *, text: str, whole: str) -> "str | tuple":
        parts = cls._split(text=text, whole=whole)
        if len(parts) == 1:
            return cls._operand(text=parts[0], whole=whole)
        if len(parts) > 3:
            cls._raise(f"Use parentheses to group more than one operator in {whole!r}")
        left, op, right = parts
        return (
            cls._operand(text=left, whole=whole),
            op,
            cls._operand(text=right, whole=whole),
        )

    @classmethod
    def _split(cls, *, text: str, whole: str) -> list[str]:
        parts = []
        start = 0
        depth = 0
        i = 0
        while i < len(text):
            c = text[i]
            if c == '"':
                i = cls._end_of_quoted(text=text, i=i, quote='"', whole=whole)
                continue
            if c == "/" and cls._starts_regex(text=text, i=i, depth=depth):
                i = cls._end_of_quoted(text=text, i=i, quote="/", whole=whole)
                continue
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth < 0:
                    cls._raise(f"Unbalanced ')' in {whole!r}")
            elif depth == 0:
                op = cls._operator_at(text=text, i=i)
                if op is not None:
                    parts.append(text[start:i].strip(cls.WHITESPACE))
                    parts.append(op)
                    i += len(op)
                    start = i
                    continue
            i += 1
        if depth != 0:
            cls._raise(f"Unbalanced '(' in {whole!r}")
        parts.append(text[start:].strip(cls.WHITESPACE))
        for k in range(0, len(parts), 2):
            if parts[k] == "":
                op = parts[k + 1] if k + 1 < len(parts) else parts[k - 1]
                cls._raise(
                    "A reference expression needs a reference on both sides "
                    f"of {op.upper()} in {whole!r}"
                )
        return parts

    @classmethod
    def _operand(cls, *, text: str, whole: str) -> "str | tuple":
        if not text.startswith("("):
            return text
        close = cls._matching_paren(text=text, whole=whole)
        if close != len(text) - 1:
            cls._raise(
                f"Unexpected text after a group in {whole!r}: "
                f"{text[close + 1 :].strip(cls.WHITESPACE)!r}"
            )
        inner = text[1:-1]
        if inner.strip(cls.WHITESPACE) == "":
            cls._raise(f"Empty parentheses in {whole!r}")
        return cls._parse(text=inner, whole=whole)

    @classmethod
    def _matching_paren(cls, *, text: str, whole: str) -> int:
        depth = 0
        i = 0
        while i < len(text):
            c = text[i]
            if c == '"':
                i = cls._end_of_quoted(text=text, i=i, quote='"', whole=whole)
                continue
            if c == "/" and cls._starts_regex(text=text, i=i, depth=depth):
                i = cls._end_of_quoted(text=text, i=i, quote="/", whole=whole)
                continue
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        cls._raise(f"Unbalanced '(' in {whole!r}")

    @classmethod
    def _operator_at(cls, *, text: str, i: int) -> str | None:
        if i > 0 and text[i - 1] not in cls.WHITESPACE and text[i - 1] != ")":
            return None
        for op in cls.OPERATORS:
            end = i + len(op)
            if text[i:end].lower() != op:
                continue
            if end == len(text) or text[end] in cls.WHITESPACE or text[end] == "(":
                return op
        return None

    @classmethod
    def _starts_regex(cls, *, text: str, i: int, depth: int) -> bool:
        if depth == 0:
            return False
        j = i - 1
        while j >= 0 and text[j] in cls.WHITESPACE:
            j -= 1
        return j >= 0 and text[j] == "("

    @classmethod
    def _end_of_quoted(cls, *, text: str, i: int, quote: str, whole: str) -> int:
        """the index just past the quote that closes the one at i.
        A backslash escapes the next character, as in the grammar's
        STRING and REGEX_INNER."""
        j = i + 1
        while j < len(text):
            if text[j] == "\\":
                j += 2
                continue
            if text[j] == quote:
                return j + 1
            j += 1
        what = "string" if quote == '"' else "regex"
        cls._raise(f"Unterminated {what} in {whole!r}")

    @classmethod
    def _check_input(cls, expression: str) -> None:
        logger = logging.getLogger(cls.__name__)
        if not isinstance(expression, str):
            msg = f"A reference expression must be a string, not {type(expression)}"
            logger.error(msg)
            raise TypeError(msg)
        if expression.strip(cls.WHITESPACE) == "":
            msg = "A reference expression cannot be empty"
            logger.error(msg)
            raise ValueError(msg)

    @classmethod
    def _raise(cls, msg: str) -> NoReturn:
        logging.getLogger(cls.__name__).error(msg)
        raise ReferenceException3(msg)
