import re


class CookieDetector:
    """finds HTTP cookie headers in a cell, our stand-in for Macie's
    HTTP_COOKIE. Macie: no keyword, and a complete Cookie or Set-Cookie
    header with one or more name-value pairs, e.g. Set-Cookie: id=TWlrZQ
    and Cookie: session=3948; lang=en.

    Ours, from RFC 6265: the field name in any case, as HTTP allows, a
    colon, and a name=value pair. A Cookie header's further pairs follow
    after semicolons; a Set-Cookie header's attributes (Path=/, Secure)
    are part of the header. A name is a token, and a value is not empty:
    characters other than spaces, quotes, commas, semicolons and
    backslashes, or a quoted string. One header is one occurrence."""

    NAME = r"[!#$%&'*+.^_`|~0-9A-Za-z-]+"
    VALUE = r'(?:"[^";,\\\s]+"|[^";,\\\s]+)'
    PAIR = rf"{NAME}={VALUE}"
    #
    # an attribute value ends at a space or comma: Expires=Wed, 21 Oct
    # 2015 ... ends the occurrence at Wed. It is still one header
    #
    ATTRIBUTE = rf"{NAME}(?:=[^;\s,]*)?"
    CANDIDATES = re.compile(
        rf"(?<![A-Za-z0-9-])(?:Set-Cookie:[ \t]*{PAIR}(?:;[ \t]*{ATTRIBUTE})*"
        rf"|Cookie:[ \t]*{PAIR}(?:;[ \t]*{PAIR})*)",
        re.ASCII | re.IGNORECASE,
    )

    def __init__(self, *, config: dict) -> None:
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dict, not {type(config)}")

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        return [(m.start(), m.end()) for m in self.CANDIDATES.finditer(cell)]
