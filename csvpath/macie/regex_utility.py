import logging
import re

from .macie_exceptions import MacieException


class RegexUtility:
    """turns a Macie regex (a subset of PCRE) into a compiled Python regex.

    Two differences matter:

    - Macie's docs recommend `(?i)` part way through a pattern. In PCRE an
      inline flag applies from where it appears to the end of its group,
      including later alternatives in that group. Python only accepts
      inline flags at the very start. We rewrite each mid-pattern flag as
      a scoped group, `(?i:...)`, covering the same text.
    - PCRE's `\\d`, `\\w` and `\\s` are ASCII-only by default; Python's
      match any Unicode digit, word or space character. We compile with
      re.ASCII.
    """

    #
    # an inline-flag-only group, e.g. (?i) or (?i-m). PCRE flag letters
    # that Python also has.
    #
    INLINE_FLAGS = re.compile(r"\(\?([imsx]*(?:-[imsx]+)?)\)")
    #
    # a scoped-flag group opening, e.g. (?i: or (?-i:
    #
    SCOPED_FLAGS = re.compile(r"\(\?([imsx]*(?:-[imsx]+)?):")

    @classmethod
    def logger(cls) -> logging.Logger:
        return logging.getLogger(cls.__name__)

    @classmethod
    def compile(cls, *, pattern: str) -> re.Pattern:
        if not isinstance(pattern, str):
            raise TypeError(f"pattern must be a str, not {type(pattern)}")
        if pattern == "":
            raise ValueError("pattern cannot be empty")
        python_pattern = cls.to_python(pattern=pattern)
        try:
            return re.compile(python_pattern, re.ASCII)
        except re.error as e:
            msg = f"Cannot compile Macie regex {pattern!r} as {python_pattern!r}: {e}"
            cls.logger().error(msg)
            raise MacieException(msg) from e

    @classmethod
    def to_python(cls, *, pattern: str) -> str:
        if not isinstance(pattern, str):
            raise TypeError(f"pattern must be a str, not {type(pattern)}")
        text, i = cls._group_body(pattern=pattern, i=0)
        if i != len(pattern):
            msg = f"Unbalanced ) at position {i} in Macie regex {pattern!r}"
            cls.logger().error(msg)
            raise MacieException(msg)
        return text

    @classmethod
    def _group_body(cls, *, pattern: str, i: int) -> tuple[str, int]:
        #
        # reads from i to the end of the current group (an unescaped ")"
        # or the end of the pattern) and returns the rewritten body and
        # the index of that ")" (or len(pattern)).
        #
        # alternatives: each is a list of parts. a part is either plain
        # text or the start of a flag scope. carried holds the flags set
        # by earlier alternatives in this group, which in PCRE carry on.
        #
        alternatives = []
        carried = []
        parts = []
        while i < len(pattern):
            c = pattern[i]
            if c == "\\":
                parts.append(pattern[i : i + 2])
                i += 2
            elif c == "[":
                end = cls._class_end(pattern=pattern, i=i)
                parts.append(pattern[i:end])
                i = end
            elif c == "|":
                alternatives.append((carried, parts))
                carried = carried + cls._flags_in(parts=parts)
                parts = []
                i += 1
            elif c == ")":
                break
            elif c == "(":
                m = cls.INLINE_FLAGS.match(pattern, i)
                if m is not None:
                    parts.append(("flags", m.group(1)))
                    i = m.end()
                    continue
                opening = cls._group_opening(pattern=pattern, i=i)
                inner, close = cls._group_body(pattern=pattern, i=i + len(opening))
                if close >= len(pattern):
                    msg = f"Unclosed ( at position {i} in Macie regex {pattern!r}"
                    cls.logger().error(msg)
                    raise MacieException(msg)
                parts.append(f"{opening}{inner})")
                i = close + 1
            else:
                parts.append(c)
                i += 1
        alternatives.append((carried, parts))
        rendered = [cls._render(flags=f, parts=p) for f, p in alternatives]
        return "|".join(rendered), i

    @classmethod
    def _render(cls, *, flags: list, parts: list) -> str:
        #
        # a flag part wraps everything after it in this alternative:
        # ab(?i)cd(?m)ef -> ab(?i:cd(?m:ef))
        #
        text = ""
        for part in reversed(parts):
            if isinstance(part, tuple):
                text = f"(?{part[1]}:{text})"
            else:
                text = part + text
        for f in reversed(flags):
            text = f"(?{f}:{text})"
        return text

    @classmethod
    def _flags_in(cls, *, parts: list) -> list:
        return [p[1] for p in parts if isinstance(p, tuple)]

    @classmethod
    def _group_opening(cls, *, pattern: str, i: int) -> str:
        #
        # returns the opening of the group at i, e.g. "(", "(?:", "(?i:",
        # "(?=". its body is rewritten separately.
        #
        m = cls.SCOPED_FLAGS.match(pattern, i)
        if m is not None:
            return m.group(0)
        for opening in ["(?:", "(?=", "(?!", "(?<=", "(?<!", "(?>"]:
            if pattern.startswith(opening, i):
                return opening
        if pattern.startswith("(?", i):
            msg = f"Unsupported group at position {i} in Macie regex {pattern!r}"
            cls.logger().error(msg)
            raise MacieException(msg)
        return "("

    @classmethod
    def _class_end(cls, *, pattern: str, i: int) -> int:
        #
        # i is at "[". returns the index just after the matching "]". a "]"
        # straight after "[" or "[^" is a literal, as in PCRE.
        #
        j = i + 1
        if j < len(pattern) and pattern[j] == "^":
            j += 1
        if j < len(pattern) and pattern[j] == "]":
            j += 1
        while j < len(pattern):
            if pattern[j] == "\\":
                j += 2
            elif pattern[j] == "]":
                return j + 1
            else:
                j += 1
        msg = f"Unclosed [ at position {i} in Macie regex {pattern!r}"
        cls.logger().error(msg)
        raise MacieException(msg)
