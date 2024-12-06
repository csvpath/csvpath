class SourceMode:
    PRECEDING = "preceding"
    DEFAULT = "default"
    MODE = "source-mode"

    def __init__(self, controller):
        self.controller = controller
        self._source_mode = False

    def update(self) -> None:
        self._source_mode = None
        self.value

    @property
    def value(self) -> bool:
        if self._source_mode is None:
            self._source_mode = (
                self.controller.get(SourceMode.MODE) == SourceMode.PRECEDING
            )
        return self._source_mode

    @value.setter
    def value(self, sm: bool) -> None:
        m = SourceMode.PRECEDING if sm is True else SourceMode.DEFAULT
        self.controller.set(SourceMode.MODE, m)
        self.source_mode = sm
