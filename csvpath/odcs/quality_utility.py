class QualityUtility:
    """small helpers for ODCS quality rules, shared by property and schema
    object conversion"""

    @classmethod
    def metric(cls, *, rule: dict) -> str | None:
        """the library metric. v3.0 used rule, v3.1 deprecated it for metric."""
        if not isinstance(rule, dict):
            raise TypeError(f"rule must be a dict, not {type(rule)}")
        return rule.get("metric") or rule.get("rule")

    @classmethod
    def skip_reason(cls, *, kind: str, rule: dict) -> str:
        """why a non-library quality rule is not translated"""
        if not isinstance(kind, str) or kind.strip() == "":
            raise ValueError("kind must be a non-empty str")
        if not isinstance(rule, dict):
            raise TypeError(f"rule must be a dict, not {type(rule)}")
        if kind == "sql":
            return "SQL quality rules need a database; CsvPath validates the file."
        if kind == "custom":
            engine = rule.get("engine", "unknown")
            return (
                f"Custom quality rules run on a vendor engine ({engine}), not CsvPath."
            )
        if kind == "text":
            return "Text quality rules are descriptions, not executable checks."
        return f"Quality type {kind} is not supported."
