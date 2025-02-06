class ErrorMode:
    BARE = "bare"
    FULL = "full"
    DEFAULT = BARE
    MODE = "error-mode"
    CONFIG_KEY = "use_format"

    def __init__(self, controller):
        self.controller = controller
        self._error_mode = False

    def update(self) -> None:
        self._error_mode = None
        self.value

    @property
    def value(self) -> bool:
        if self._error_mode is None:
            self._error_mode = self.controller.get(ErrorMode.MODE) == ErrorMode.DEFAULT
        return self._error_mode

    @value.setter
    def value(self, em: bool) -> None:
        m = ErrorMode.FULL if em is True else ErrorMode.DEFAULT
        self.controller.set(ErrorMode.MODE, m)
        self.error_mode = em
