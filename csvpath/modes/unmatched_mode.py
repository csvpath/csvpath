class UnmatchedMode:
    KEEP = "keep"
    NO_KEEP = "no-keep"
    MODE = "unmatched-mode"

    def __init__(self, mode_controller):
        self.controller = mode_controller
        self._unmatched_mode: bool = None

    def update(self) -> None:
        self._unmatched_mode = None
        self.value

    @property
    def value(self) -> bool:
        if self._unmatched_mode is None:
            um = self.controller.get(UnmatchedMode.MODE)
            if um is None or um.find(UnmatchedMode.NO_KEEP) > -1:
                self._unmatched_mode = False
            else:
                self._unmatched_mode = True
        return self._unmatched_mode

    @value.setter
    def value(self, um: bool) -> None:
        self._unmatched_mode = um
        um = (
            UnmatchedMode.NO_KEEP if (um is False or um is None) else UnmatchedMode.KEEP
        )
        self.controller.set(UnmatchedMode.MODE, um)
