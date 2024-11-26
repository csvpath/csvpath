from ..util.exceptions import InputException


class LogicMode:
    MODE = "logic-mode"
    AND = "and"
    OR = "or"

    def __init__(self, controller):
        self.controller = controller
        #
        # when AND is True we do a logical AND of the match components
        # to see if there is a match. this is the default. when AND is
        # False (or set OR to True) the match components are ORed to
        # determine if a line matches. in the former case all the match
        # components must agree for a line to match. in the latter case,
        # if any one match component votes True the line is matched.
        # technically you can switch from AND to OR, or vice versa, in
        # the middle of iterating a file using next(). probably not a
        # good idea, tho.
        #
        self._AND = True

    def update(self) -> None:
        self._AND = None
        self.value

    @property
    def value(self) -> bool:
        if self._AND is None:
            lm = self.controller.get(LogicMode.MODE)
            if lm is None:
                lm = LogicMode.AND
            lm = lm.strip().lower()
            if lm not in [LogicMode.AND, LogicMode.OR]:
                raise InputException(f"Unknown logic mode: {lm}")
            self._AND = True if lm == LogicMode.AND else False
        return self._AND

    @value.setter
    def value(self, m: bool) -> None:
        self.controller.set(
            LogicMode.MODE, LogicMode.AND if m is True else LogicMode.OR
        )
        self._AND = m

    """
    # should we have these here or would it be better to leave them on CsvPath?
    # if we have them here we shouldn't use AND and OR as names on the class too.
    @property
    def AND(self) -> bool:  # pylint: disable=C0103
        return self._AND

    @AND.setter
    def AND(self, a: bool) -> bool:  # pylint: disable=C0103
        self._AND = a

    @property
    def OR(self) -> bool:  # pylint: disable=C0103
        return not self._AND

    @OR.setter
    def OR(self, a: bool) -> bool:  # pylint: disable=C0103
        self._AND = not a

    """
