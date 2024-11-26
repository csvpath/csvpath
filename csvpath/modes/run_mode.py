from ..util.exceptions import InputException


class RunMode:
    #
    # run mode determines if a csvpath gets run or if it is skipped. the
    # main reasons to set run-mode: no-run vs. run are: you want to import
    # it into other csvpaths that are in the same named-paths group, or
    # you want to switch off a csvpath in a named-paths group for testing
    # a similar reason.
    #
    RUN = "run"
    NO_RUN = "no-run"
    MODE = "run-mode"

    def __init__(self, mode_controller) -> None:
        self.controller = mode_controller
        self._run_mode: bool = True

    def update(self) -> None:
        self._run_mode = None
        self.value

    @property
    def value(self) -> bool:
        if self._run_mode is None:
            rm = self.controller.get(RunMode.MODE)
            if rm is None:
                rm = RunMode.RUN
            rm = rm.strip()
            if rm not in [RunMode.RUN, RunMode.NO_RUN]:
                raise InputException("Unknown run mode: {rm}")
            if rm == RunMode.RUN:
                self._run_mode = True
            else:
                self._run_mode = False
        return self._run_mode

    @value.setter
    def value(self, rm: bool) -> None:
        self._run_mode = rm
        rm = RunMode.NO_RUN if rm is False else RunMode.RUN
        self.controller.set(RunMode.MODE, rm)
