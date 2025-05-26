class ExplainMode:
    EXPLAIN = "explain"
    NO_EXPLAIN = "no-explain"
    MODE = "explain-mode"

    def __init__(self, controller):
        self.controller = controller
        #
        # explain-mode: explain
        # turns on capturing match reasoning and dumps the captured decisions to INFO
        # at the end of a match. the reasoning is already present in the DEBUG but it
        # is harder to see amid all the noise. we don't want to dump explanations
        # all the time tho because it is very expensive -- potentially 25% worse
        # performance. the explanations could be improved. atm this is an experimental
        # feature.
        #
        self._explain: bool = None

    def update(self) -> None:
        self._explain = None
        self.value

    @property
    def value(self) -> bool:
        if self._explain is None:
            em = self.controller.get(ExplainMode.MODE)
            if em is None:
                self._explain = False
            else:
                self._explain = em.strip() == ExplainMode.EXPLAIN
        return self._explain

    @value.setter
    def value(self, em: bool) -> None:
        self.controller.set(
            ExplainMode.MODE,
            ExplainMode.NO_EXPLAIN
            if em is False or em is None
            else ExplainMode.EXPLAIN,
        )
        self._explain = em
