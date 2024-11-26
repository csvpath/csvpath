from ..util.exceptions import InputException
from ..util.printer import StdOutPrinter


class PrintMode:
    MODE = "print-mode"
    DEFAULT = "default"
    NO_DEFAULT = "no-default"

    def __init__(self, controller):
        self.controller = controller
        self._print_mode = None

    @property
    def value(self) -> bool:
        if self._print_mode is None:
            pm = self.controller.get(PrintMode.MODE)
            if pm is None:
                self.value = True
            else:
                self.update_printers()
        return self._print_mode

    @value.setter
    def value(self, pm: bool) -> None:
        if pm is None:
            pm = True
        self._print_mode = pm
        self.controller.set(
            PrintMode.MODE, PrintMode.DEFAULT if pm is True else PrintMode.NO_DEFAULT
        )
        self.update_printers()

    def update(self) -> None:
        self._print_mode = None
        self.value

    def update_printers(self) -> None:
        pm = self.controller.get(PrintMode.MODE)
        if f"{pm}".strip() == "no-default":
            remove = -1
            for i, p in enumerate(self.controller.csvpath.printers):
                if isinstance(p, StdOutPrinter):
                    remove = i
                    break
            if remove >= 0:
                del self.controller.csvpath.printers[remove]
        elif f"{pm}".strip() == "default":
            done = False
            for p in self.controller.csvpath.printers:
                if isinstance(p, StdOutPrinter):
                    done = True
                    break
            if not done:
                self.controller.csvpath.printers.append(StdOutPrinter())
        else:
            raise InputException("Unknown print-mode: {pm}")
