# pylint: disable=C0114
from ..function_focus import SideEffect


class Track(SideEffect):
    """uses a match component value to set a tracking
    value, from another match component, on a variable."""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        left = self.children[0].children[0]
        right = self.children[0].children[1]
        varname = self.first_non_term_qualifier(self.name)
        tracking = f"{left.to_value(skip=skip)}".strip()
        v = right.to_value(skip=skip)
        if isinstance(v, str):
            v = f"{v}".strip()
        value = v
        self.matcher.set_variable(varname, tracking=tracking, value=value)
        self.value = True

    def _decide_match(self, skip=None) -> None:
        self._apply_default_match()
        self.to_value(skip=skip)
