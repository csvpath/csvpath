import re


class CsvPathTextUtility:
    """builds small pieces of CsvPath Validation Language text: header
    references, string and regex literals, numbers, and variable names.
    Raises ValueError for values the language cannot express, so callers
    can report them as skipped rather than emit a broken csvpath."""

    #
    # from the HEADER token in csvpath/matching/lark_parser.py
    #
    _PLAIN_HEADER = re.compile(r"[a-zA-Z0-9\-\._]+")
    _QUOTED_HEADER = re.compile(r"[a-zA-Z0-9\- \._]+")

    @classmethod
    def header(cls, *, name: str, index: int) -> str:
        """a header reference by name when the language can express the
        name, otherwise by column index"""
        if not isinstance(name, str) or name.strip() == "":
            raise ValueError("name must be a non-empty str")
        if not isinstance(index, int) or isinstance(index, bool) or index < 0:
            raise ValueError(f"index must be an int >= 0, not {index}")
        #
        # an all-digit name would read as a column index, by name or quoted
        #
        if name.isdigit():
            return f"#{index}"
        if cls._PLAIN_HEADER.fullmatch(name):
            return f"#{name}"
        if cls._QUOTED_HEADER.fullmatch(name):
            return f'#"{name}"'
        return f"#{index}"

    @classmethod
    def string(cls, *, value: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"value must be a str, not {type(value)}")
        if '"' in value:
            raise ValueError(f"A CsvPath string cannot contain a double quote: {value}")
        return f'"{value}"'

    @classmethod
    def in_values(cls, *, values: list) -> str:
        """the pipe-delimited string literal in() takes"""
        if not isinstance(values, list) or len(values) == 0:
            raise ValueError("values must be a non-empty list")
        strs = []
        for v in values:
            if v is None or isinstance(v, (list, dict)):
                raise ValueError(f"Cannot use {v} as an in() value")
            s = cls._scalar(value=v)
            if "|" in s:
                raise ValueError(f"An in() value cannot contain a pipe: {s}")
            strs.append(s)
        return cls.string(value="|".join(strs))

    @classmethod
    def _scalar(cls, *, value) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        return f"{value}"

    @classmethod
    def regex(cls, *, pattern: str) -> str:
        """a /.../ regex literal. raises ValueError if Python re cannot
        compile the pattern."""
        if not isinstance(pattern, str) or pattern == "":
            raise ValueError("pattern must be a non-empty str")
        try:
            re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Pattern does not compile in Python re: {e}") from e
        escaped = cls._escape_slashes(pattern=pattern)
        #
        # regex() strips every leading and trailing / from the literal, so an
        # escaped slash at either end would be lost. a non-capturing group
        # protects it.
        #
        if escaped.startswith("\\/") or escaped.endswith("\\/"):
            escaped = f"(?:{escaped})"
        return f"/{escaped}/"

    @classmethod
    def _escape_slashes(cls, *, pattern: str) -> str:
        out = []
        i = 0
        while i < len(pattern):
            c = pattern[i]
            if c == "\\" and i + 1 < len(pattern):
                out.append(pattern[i : i + 2])
                i += 2
                continue
            out.append("\\/" if c == "/" else c)
            i += 1
        return "".join(out)

    @classmethod
    def number(cls, *, value) -> str:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"value must be an int or float, not {type(value)}")
        if isinstance(value, float) and value.is_integer():
            return f"{int(value)}"
        return f"{value}"

    @classmethod
    def variable(cls, *, name: str, suffix: str) -> str:
        """a variable name, without the @, built from a header name"""
        if not isinstance(name, str) or name.strip() == "":
            raise ValueError("name must be a non-empty str")
        if not isinstance(suffix, str) or suffix.strip() == "":
            raise ValueError("suffix must be a non-empty str")
        base = re.sub(r"[^a-z0-9_]", "_", name.lower())
        return f"{base}_{suffix}"
