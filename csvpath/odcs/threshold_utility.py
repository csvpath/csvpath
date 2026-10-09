from .csvpath_text_utility import CsvPathTextUtility as csut


class ThresholdUtility:
    """translates ODCS quality operators (mustBe, mustBeLessThan, ...) into
    CsvPath "fail when" conditions.

    Conditions are emitted directly, never wrapped in not(), and never with
    lt()/below()/before(), which behave as lte() (issue #301). gt(), gte(),
    lte(), eq(), and neq() are correct.
    """

    OPERATORS = [
        "mustBe",
        "mustNotBe",
        "mustBeGreaterThan",
        "mustBeGreaterOrEqualTo",
        "mustBeLessThan",
        "mustBeLessOrEqualTo",
        "mustBeBetween",
        "mustNotBeBetween",
    ]

    @classmethod
    def operator(cls, *, rule: dict) -> tuple[str, object]:
        """returns (operator, value). raises ValueError unless the rule has
        exactly one operator."""
        if not isinstance(rule, dict):
            raise TypeError(f"rule must be a dict, not {type(rule)}")
        found = [op for op in cls.OPERATORS if op in rule]
        if len(found) != 1:
            raise ValueError(f"Expected exactly one operator, found {found}")
        return found[0], rule[found[0]]

    @classmethod
    def is_zero_tolerance(cls, *, rule: dict) -> bool:
        """True when a count-of-bad-values rule allows no bad values at all,
        which makes it a per-line constraint"""
        op, value = cls.operator(rule=rule)
        if op == "mustBe":
            return value == 0
        if op == "mustBeLessThan":
            return value == 1
        if op == "mustBeLessOrEqualTo":
            return value == 0
        return False

    @classmethod
    def fail_when(cls, *, value: str, rule: dict) -> str:
        """the condition under which the rule is broken. value is CsvPath
        text, e.g. "@currency_invalid" or "subtract(total_lines(), 1)"."""
        if not isinstance(value, str) or value.strip() == "":
            raise ValueError("value must be a non-empty str")
        op, x = cls.operator(rule=rule)
        if op in ["mustBeBetween", "mustNotBeBetween"]:
            if not isinstance(x, list) or len(x) != 2:
                raise ValueError(f"{op} needs a list of two numbers, not {x}")
            a = csut.number(value=x[0])
            b = csut.number(value=x[1])
            if op == "mustBeBetween":
                return f"or( gt( {a}, {value} ), gt( {value}, {b} ) )"
            return f"and( gte( {value}, {a} ), gte( {b}, {value} ) )"
        n = csut.number(value=x)
        if op == "mustBe":
            return f"neq( {value}, {n} )"
        if op == "mustNotBe":
            return f"eq( {value}, {n} )"
        if op == "mustBeGreaterThan":
            return f"lte( {value}, {n} )"
        if op == "mustBeGreaterOrEqualTo":
            return f"gt( {n}, {value} )"
        if op == "mustBeLessThan":
            return f"gte( {value}, {n} )"
        # mustBeLessOrEqualTo
        return f"gt( {value}, {n} )"
