import datetime


class JdkDateFormatUtility:
    """translates JDK DateTimeFormatter patterns, which ODCS uses for date,
    timestamp, and time formats, into Python strftime/strptime formats.

    Quoted literals ('T', and '' for a single quote) are honored. Letters
    that have no meaning in JDK patterns, such as the unquoted T in the ODCS
    docs' own "yyyy-MM-ddTHH:mm:ssZ", are treated as literals. JDK pattern
    letters with no strftime equivalent raise ValueError, so the caller can
    report the format as skipped.
    """

    ISO_DATE = "%Y-%m-%d"
    ISO_TIME = "%H:%M:%S"

    #
    # (letter, minimum run length) -> strftime. the longest matching run
    # length wins; e.g. MMM -> %b, MM -> %m.
    #
    _MAPPINGS = {
        "y": [(1, "%Y"), (2, "%y"), (3, "%Y")],
        "u": [(1, "%Y"), (2, "%y"), (3, "%Y")],
        "M": [(1, "%m"), (3, "%b"), (4, "%B")],
        "L": [(1, "%m"), (3, "%b"), (4, "%B")],
        "d": [(1, "%d")],
        "D": [(1, "%j")],
        "H": [(1, "%H")],
        "h": [(1, "%I")],
        "a": [(1, "%p")],
        "m": [(1, "%M")],
        "s": [(1, "%S")],
        "S": [(1, "%f")],
        "E": [(1, "%a"), (4, "%A")],
        "Z": [(1, "%z")],
        "X": [(1, "%z")],
        "x": [(1, "%z")],
        "z": [(1, "%Z")],
    }

    #
    # every JDK DateTimeFormatter pattern letter. letters here but not in
    # _MAPPINGS are real JDK fields we cannot translate.
    #
    _JDK_LETTERS = set("GuyDMLdQqYwWEecFahKkHmsSAnNVzOXxZp")
    _JDK_RESERVED = set("[]#{}")

    @classmethod
    def to_strftime(cls, *, pattern: str) -> str:
        if pattern is None:
            raise ValueError("pattern cannot be None")
        if not isinstance(pattern, str):
            raise TypeError(f"pattern must be a str, not {type(pattern)}")
        if pattern.strip() == "":
            raise ValueError("pattern cannot be empty")
        out = []
        i = 0
        while i < len(pattern):
            c = pattern[i]
            if c == "'":
                literal, i = cls._quoted(pattern=pattern, start=i)
                out.append(literal.replace("%", "%%"))
                continue
            if c in cls._JDK_RESERVED:
                raise ValueError(f"Unsupported JDK pattern character {c} in {pattern}")
            if not c.isalpha():
                out.append("%%" if c == "%" else c)
                i += 1
                continue
            run = 1
            while i + run < len(pattern) and pattern[i + run] == c:
                run += 1
            if c not in cls._JDK_LETTERS:
                out.append(c * run)
            elif c not in cls._MAPPINGS:
                raise ValueError(f"Unsupported JDK pattern letter {c} in {pattern}")
            else:
                out.append(cls._mapping(letter=c, run=run))
            i += run
        return "".join(out)

    @classmethod
    def _quoted(cls, *, pattern: str, start: int) -> tuple[str, int]:
        # '' is an escaped single quote, inside or outside a quoted section
        if pattern[start : start + 2] == "''":
            return "'", start + 2
        literal = []
        i = start + 1
        while i < len(pattern):
            if pattern[i] == "'":
                if pattern[i : i + 2] == "''":
                    literal.append("'")
                    i += 2
                    continue
                return "".join(literal), i + 1
            literal.append(pattern[i])
            i += 1
        raise ValueError(f"Unterminated quoted literal in {pattern}")

    @classmethod
    def _mapping(cls, *, letter: str, run: int) -> str:
        chosen = None
        for min_run, strf in cls._MAPPINGS[letter]:
            if run >= min_run:
                chosen = strf
        return chosen

    @classmethod
    def parsing_format(cls, *, value: str, formats: list[str]) -> str | None:
        """returns the first strptime format in formats that parses value,
        or None if none do"""
        if not isinstance(value, str):
            raise TypeError(f"value must be a str, not {type(value)}")
        if not isinstance(formats, list) or len(formats) == 0:
            raise ValueError("formats must be a non-empty list")
        for f in formats:
            try:
                datetime.datetime.strptime(value, f)
                return f
            except ValueError:
                continue
        return None
