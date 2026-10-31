from .macie_exceptions import MacieException


class SeverityLevels:
    """a custom data identifier's occurrence thresholds, e.g. LOW at 1,
    MEDIUM at 5, HIGH at 10. The severity for a count is that of the
    highest threshold the count reaches; below the lowest threshold there
    is no finding. Without levels, Macie reports MEDIUM from 1 occurrence.
    """

    ORDER = ["LOW", "MEDIUM", "HIGH"]
    DEFAULT = "1:MEDIUM"

    def __init__(self, *, levels: list[tuple[int, str]]) -> None:
        if not isinstance(levels, list) or len(levels) == 0:
            raise ValueError("levels must be a non-empty list")
        for level in levels:
            if (
                not isinstance(level, tuple)
                or len(level) != 2
                or not isinstance(level[0], int)
                or isinstance(level[0], bool)
                or level[0] < 1
                or level[1] not in self.ORDER
            ):
                raise MacieException(f"Bad severity level: {level!r}")
        thresholds = [t for t, _ in levels]
        severities = [self.ORDER.index(s) for _, s in levels]
        #
        # Macie requires both to ascend together, LOW to HIGH
        #
        if thresholds != sorted(set(thresholds)) or severities != sorted(
            set(severities)
        ):
            raise MacieException(
                f"Severity thresholds must ascend with severity, LOW to HIGH: {levels!r}"
            )
        self.levels = levels

    @classmethod
    def from_aws(cls, *, severity_levels: list) -> "SeverityLevels":
        """from a GetCustomDataIdentifier severityLevels list, which may be
        absent or empty"""
        if not severity_levels:
            return cls.parse(text=cls.DEFAULT)
        if not isinstance(severity_levels, list):
            raise TypeError(
                f"severity_levels must be a list, not {type(severity_levels)}"
            )
        levels = [(s["occurrencesThreshold"], s["severity"]) for s in severity_levels]
        return cls(levels=sorted(levels))

    @classmethod
    def parse(cls, *, text: str) -> "SeverityLevels":
        """from the CVL form, e.g. "1:LOW 5:MEDIUM 10:HIGH" """
        if not isinstance(text, str):
            raise TypeError(f"text must be a str, not {type(text)}")
        if text.strip() == "":
            raise ValueError("text cannot be empty")
        levels = []
        for item in text.split():
            threshold, sep, severity = item.partition(":")
            if sep == "" or not threshold.isdigit():
                raise MacieException(f"Bad severity level {item!r} in {text!r}")
            levels.append((int(threshold), severity))
        return cls(levels=levels)

    def to_text(self) -> str:
        return " ".join(f"{t}:{s}" for t, s in self.levels)

    def severity(self, *, count: int) -> str | None:
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ValueError(f"count must be a non-negative int, not {count!r}")
        found = None
        for threshold, severity in self.levels:
            if count >= threshold:
                found = severity
        return found

    def is_final(self, *, count: int) -> bool:
        """True once more occurrences can't change the severity"""
        return count >= self.levels[-1][0]
