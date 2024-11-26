from ..util.exceptions import InputException


class TransferMode:
    MODE = "transfer-mode"

    def __init__(self, controller):
        self.controller = controller
        #
        # transfers from transfer-mode: ((data | unmatched):var-name)(,*)
        # this setting tells CsvPaths to copy resulting data.csv and/or
        # unmatched.csv to one or more target locations below the config.ini's
        # transfer directory. the name "data" or "unmatched" is paired with
        # a var name that indicates the path to write the indicated file.
        #
        self._transfers = None

    @property
    def value(self) -> str:
        return self.controller.get(TransferMode.MODE)

    @value.setter
    def value(self, tm: str) -> None:
        self.controller.set(TransferMode.MODE, tm)
        self._transfers = None

    def update(self) -> None:
        pass

    @property
    def transfers(self) -> list[tuple[str, str]]:
        if self._transfers is None:
            tm = self.value
            if tm is not None:
                _ = [s.strip() for s in tm.split(",")]
                self._transfers = []
                for s in _:
                    i = s.find(">")
                    if i == -1:
                        raise InputException(
                            "Transfer mode must include a > directing a generated file to a location"
                        )
                    f = s[0:i].strip()
                    t = s[i + 1 :].strip()
                    self._transfers.append((f, t))
        return self._transfers
