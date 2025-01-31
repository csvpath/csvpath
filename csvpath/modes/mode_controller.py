from .explain_mode import ExplainMode
from .files_mode import FilesMode
from .logic_mode import LogicMode
from .print_mode import PrintMode
from .return_mode import ReturnMode
from .run_mode import RunMode
from .source_mode import SourceMode
from .error_mode import ErrorMode
from .transfer_mode import TransferMode
from .unmatched_mode import UnmatchedMode
from .validation_mode import ValidationMode
from ..util.exceptions import InputException


class ModeController:

    MODES = [
        ExplainMode.MODE,
        FilesMode.MODE,
        LogicMode.MODE,
        PrintMode.MODE,
        ReturnMode.MODE,
        RunMode.MODE,
        SourceMode.MODE,
        ErrorMode.MODE,
        TransferMode.MODE,
        UnmatchedMode.MODE,
        ValidationMode.MODE,
    ]

    def __init__(self, csvpath):
        self.csvpath = csvpath
        self.explain_mode = ExplainMode(self)
        self.files_mode = FilesMode(self)
        self.logic_mode = LogicMode(self)
        self.print_mode = PrintMode(self)
        self.return_mode = ReturnMode(self)
        self.run_mode = RunMode(self)
        self.source_mode = SourceMode(self)
        self.error_mode = ErrorMode(self)
        self.transfer_mode = TransferMode(self)
        self.unmatched_mode = UnmatchedMode(self)
        self.validation_mode = ValidationMode(self)

    def update(self) -> None:
        self.explain_mode.update()
        self.files_mode.update()
        self.logic_mode.update()
        self.print_mode.update()
        self.return_mode.update()
        self.run_mode.update()
        self.source_mode.update()
        self.error_mode.update()
        self.transfer_mode.update()
        self.unmatched_mode.update()
        self.validation_mode.update()

    def get(self, mode: str) -> str:
        if mode is None:
            raise InputException("Mode cannot be None")
        if mode not in ModeController.MODES:
            raise InputException(f"Unknown mode {mode}")
        ret = None
        if mode in ModeController.MODES:
            ret = self.csvpath.metadata.get(mode)
        return ret

    def set(self, mode: str, setting: str) -> None:
        if mode is None:
            raise InputException("Mode cannot be None")
        if mode not in ModeController.MODES:
            raise InputException(f"Unknown mode {mode}")
        if mode in ModeController.MODES:
            self.csvpath.metadata[mode] = setting
