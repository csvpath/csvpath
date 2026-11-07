import re


class LatLongDetector:
    """finds GPS coordinates in a cell, our stand-in for Macie's
    LATITUDE_LONGITUDE. Macie: a latitude and longitude stored as a pair in
    Decimal Degrees (DD), e.g. 41.948614,-87.655311; not Degrees Decimal
    Minutes (41°56.9168'N) or Degrees, Minutes, Seconds (41°56'55.0104"N).

    Ours: a latitude and a longitude, each with an optional sign and a
    decimal part, separated by a comma (spaces allowed around it) or by
    spaces. The latitude is within ±90 and the longitude within ±180. A
    pair must not touch other letters, digits or dots, and a degree sign
    after it makes it DDM or DMS, not DD."""

    NUMBER = r"[+-]?\d{1,3}\.\d+"
    CANDIDATES = re.compile(
        rf"(?<![A-Za-z0-9.+-])(?P<lat>{NUMBER})(?:[ \t]*,[ \t]*|[ \t]+)(?P<lon>{NUMBER})(?![A-Za-z0-9.°])",
        re.ASCII,
    )

    #
    # the catalog data keys this detector reads; a project rulesbase may
    # override these and no others
    #
    CONFIG_KEYS = ()

    def __init__(self, *, config: dict) -> None:
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dict, not {type(config)}")

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        found = []
        for m in self.CANDIDATES.finditer(cell):
            if abs(float(m.group("lat"))) <= 90 and abs(float(m.group("lon"))) <= 180:
                found.append((m.start(), m.end()))
        return found
