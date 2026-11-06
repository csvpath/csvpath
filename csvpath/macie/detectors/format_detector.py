import re

from ..macie_exceptions import MacieException


class FormatDetector:
    """finds identifiers that have a shape but no check digit, our
    stand-in for Macie's group B managed identifiers (format plus keyword).
    The shapes are catalog data, written in a small notation, so adding an
    identifier or a country is a catalog edit, not code (David,
    2026-11-05). The catalog detector's data:

        formats           a list of formats. Each is a string, or an object
                          {"format": "...", "used_by": [...]} saying which
                          issuers use it, e.g. the states of a US driver's
                          license
        exclusions        values never reported, compared without
                          separators and in upper case (optional)
        exclude_prefixes  value prefixes never reported, compared the same
                          way (optional)

    The notation:

        #        a digit
        A        a letter, either case
        X        a letter or a digit
        [...]    one of a set of letters and digits; ranges such as A-C
                 are allowed; letters match either case
        {n}      after a symbol or set: n of them; {m,n}: m to n
        0-9      a digit stands for itself
        other    a space or punctuation stands for itself

    Any other letter must be written as a set, e.g. [L], so that a format
    never reads as both a symbol and a literal. The formats are compiled
    into one regex when the detector is created, identical formats once.
    An occurrence must not touch other letters or digits."""

    SYMBOLS = {"#": "[0-9]", "A": "[A-Za-z]", "X": "[A-Za-z0-9]"}

    def __init__(self, *, config: dict) -> None:
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dict, not {type(config)}")
        formats = config.get("formats")
        if not isinstance(formats, list) or len(formats) == 0:
            raise MacieException("formats must be a non-empty list")
        patterns = []
        for f in formats:
            text = self._format_text(entry=f)
            pattern = self.compile_format(text=text)
            if pattern not in patterns:
                patterns.append(pattern)
        self.candidates = re.compile(
            r"(?<![A-Za-z0-9])(?:" + "|".join(patterns) + r")(?![A-Za-z0-9])"
        )
        self.exclusions = self._values(config=config, key="exclusions")
        self.exclude_prefixes = self._values(config=config, key="exclude_prefixes")

    @classmethod
    def _format_text(cls, *, entry) -> str:
        if isinstance(entry, str):
            return entry
        if isinstance(entry, dict):
            extra = set(entry) - {"format", "used_by"}
            if extra:
                raise MacieException(f"Format entry has unknown keys {sorted(extra)}")
            used_by = entry.get("used_by", [])
            if not isinstance(used_by, list) or not all(
                isinstance(u, str) and u.strip() != "" for u in used_by
            ):
                raise MacieException("used_by must be a list of non-empty strings")
            if isinstance(entry.get("format"), str):
                return entry["format"]
        raise MacieException(
            f"A format must be a string or {{format, used_by}}, not {entry!r}"
        )

    @classmethod
    def _values(cls, *, config: dict, key: str) -> frozenset:
        values = config.get(key) or []
        if not isinstance(values, list) or not all(
            isinstance(v, str) and v.strip() != "" for v in values
        ):
            raise MacieException(f"{key} must be a list of non-empty strings")
        return frozenset(cls.compact(text=v) for v in values)

    @classmethod
    def compact(cls, *, text: str) -> str:
        return re.sub(r"[^A-Za-z0-9]", "", text).upper()

    @classmethod
    def compile_format(cls, *, text: str) -> str:
        """the regex, without boundaries, for one format in the notation"""
        if not isinstance(text, str) or text.strip() == "":
            raise MacieException("A format must be a non-empty string")
        out = []
        i = 0
        while i < len(text):
            c = text[i]
            if c in cls.SYMBOLS:
                out.append(cls.SYMBOLS[c])
            elif c == "[":
                end = text.find("]", i)
                if end == -1:
                    raise MacieException(f"Format {text!r} has an unclosed [")
                out.append(cls._set(text=text, body=text[i + 1 : end]))
                i = end
            elif c == "{":
                end = text.find("}", i)
                if end == -1 or not out:
                    raise MacieException(f"Format {text!r} has a misplaced {{")
                out[-1] = out[-1] + cls._count(text=text, body=text[i + 1 : end])
                i = end
            elif c.isascii() and c.isdigit():
                out.append(c)
            elif c.isascii() and c.isalpha():
                raise MacieException(
                    f"Format {text!r}: the letter {c!r} must be in a set, e.g. [{c}]"
                )
            elif c in "]}":
                raise MacieException(f"Format {text!r} has an unmatched {c!r}")
            else:
                out.append(re.escape(c))
            i += 1
        return "".join(out)

    @classmethod
    def _set(cls, *, text: str, body: str) -> str:
        if body == "" or not re.fullmatch(r"(?:[A-Za-z0-9](?:-[A-Za-z0-9])?)+", body):
            raise MacieException(
                f"Format {text!r}: a set holds letters, digits and ranges, not {body!r}"
            )
        members = []
        for start, end in re.findall(r"([A-Za-z0-9])(?:-([A-Za-z0-9]))?", body):
            if end and not (start <= end and start.isdigit() == end.isdigit()):
                raise MacieException(f"Format {text!r} has a bad range {start}-{end}")
            span = f"{start}-{end}" if end else start
            members.append(span.upper())
            if start.isalpha():
                members.append(span.lower())
        return "[" + "".join(members) + "]"

    @classmethod
    def _count(cls, *, text: str, body: str) -> str:
        m = re.fullmatch(r"(\d+)(?:,(\d+))?", body)
        if m is None:
            raise MacieException(f"Format {text!r} has a bad count {{{body}}}")
        low, high = int(m.group(1)), m.group(2)
        if low < 1 or (high is not None and int(high) < low):
            raise MacieException(f"Format {text!r} has a bad count {{{body}}}")
        return "{" + body + "}"

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        found = []
        for m in self.candidates.finditer(cell):
            value = self.compact(text=m.group(0))
            if value in self.exclusions:
                continue
            if any(value.startswith(p) for p in self.exclude_prefixes):
                continue
            found.append((m.start(), m.end()))
        return found
