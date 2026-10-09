from dataclasses import dataclass, field


@dataclass(frozen=True)
class SkippedItem:
    """one validation-relevant ODCS feature the converter did not translate.

    object:   the schema object name
    location: path within the schema object, e.g.
              "properties.order_id.relationships[0]". "properties.<name>"
              selects a property by name.
    feature:  a short, stable label, e.g. "quality.sql" or "format.ipv4"
    reason:   human-readable explanation
    """

    object: str
    location: str
    feature: str
    reason: str

    def __post_init__(self) -> None:
        for name in ["object", "location", "feature", "reason"]:
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"SkippedItem {name} must be a str, not {type(value)}")
            if value.strip() == "":
                raise ValueError(f"SkippedItem {name} cannot be empty")


@dataclass
class ConversionReport:
    """everything the converter skipped, in contract document order"""

    skipped: list[SkippedItem] = field(default_factory=list)

    def skip(self, *, obj: str, location: str, feature: str, reason: str) -> None:
        self.skipped.append(
            SkippedItem(object=obj, location=location, feature=feature, reason=reason)
        )

    def for_object(self, *, obj: str) -> list[SkippedItem]:
        if not isinstance(obj, str) or obj.strip() == "":
            raise ValueError("obj must be a non-empty str")
        return [s for s in self.skipped if s.object == obj]
