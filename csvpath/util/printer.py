from abc import ABC, abstractmethod
import sys


class Printer(ABC):
    ERROR = "stderr"
    DEFAULT = "default"

    @abstractmethod
    def print(self, string: str) -> None:
        """prints string with a newline. same as print_to(None, string)."""
        pass

    @abstractmethod
    def print_to(self, name: str, string: str) -> None:
        """name is a file, stream, or string collection indicator.
        string is the value to be printed/stored with the addition
        of a newline."""
        pass


class StdOutPrinter(Printer):
    def print(self, string: str) -> None:
        self.print_to(None, string)

    def print_to(self, name: str, string: str) -> None:
        if name == Printer.ERROR:
            print(string, file=sys.stderr)
        elif name:
            print(string, file=name)
        else:
            print(string)
