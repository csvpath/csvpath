from ..util.exceptions import InputException


class ReturnMode:
    MODE = "return-mode"
    MATCHES = "matches"  # this is False
    NO_MATCHES = "no-matches"  # this is True

    def __init__(self, controller):
        self.controller = controller
        self._return_mode: bool = None

    def update(self) -> None:
        self._return_mode = None
        self.value

    @property
    def value(self) -> bool:
        """when True CsvPath returns the lines not matching the match components"""
        if self._return_mode is None:
            rm = self.controller.get(ReturnMode.MODE)
            if rm is None:
                rm = ReturnMode.MATCHES
            rm = rm.strip()
            if rm not in [ReturnMode.MATCHES, ReturnMode.NO_MATCHES]:
                raise InputException(f"Unknown return-mode: {rm}")
            self._return_mode = False if rm == ReturnMode.MATCHES else True
        return self._return_mode

    @value.setter
    def value(self, rm: bool) -> None:
        if rm is None:
            rm = False
        self._return_mode = rm
        self.controller.set(
            ReturnMode.MODE,
            ReturnMode.MATCHES if rm is False else ReturnMode.NO_MATCHES,
        )

    @property
    def collect_when_not_matched(self) -> bool:
        return self.value is True

    @collect_when_not_matched.setter
    def collect_when_not_matched(self, nm: bool) -> None:
        self.value = nm
