from ..util.exceptions import InputException


class FilesMode:
    MODE = "files-mode"
    ALL = "all"
    MINIMUM = "errors, meta, vars"
    DATA = "data"
    UNMATCHED = "unmatched"
    PRINTOUTS = "printouts"
    VARS = "vars"
    ERRORS = "errors"
    META = "meta"

    ALL_TYPES = [VARS, ERRORS, META, DATA, UNMATCHED, PRINTOUTS]

    def __init__(self, controller):
        self.controller = controller
        self._all_expected_files = [FilesMode.VARS, FilesMode.ERRORS, FilesMode.META]

    @property
    def value(self) -> str:
        v = self.controller.get(FilesMode.MODE)
        if v is None:
            v = FilesMode.MINIMUM
        return v

    @value.setter
    def value(self, fm: str) -> None:
        self.controller.set(FilesMode.MODE)
        self.update_expected_files()

    def update(self) -> None:
        fm = self.value
        if fm and fm.strip() == FilesMode.ALL:
            self.all_expected_files = FilesMode.ALL_TYPES
            return
        fs = []
        if fm:
            fs = [s for s in fm.split(",")]
        _ = []
        for s in fs:
            s = s.strip()
            if s not in FilesMode.ALL_TYPES:
                raise InputException(f"Unknown files-mode: {s}")
            _.append(s)
        #
        # we include vars, meta, and errors regardless
        #
        if FilesMode.VARS not in self.all_expected_files:
            self.all_expected_files.append(FilesMode.VARS)
        if FilesMode.ERRORS not in self.all_expected_files:
            self.all_expected_files.append(FilesMode.ERRORS)
        if FilesMode.META not in self.all_expected_files:
            self.all_expected_files.append(FilesMode.META)
        self.all_expected_files = _

    @property
    def all_expected_files(self) -> list[str]:
        return self._all_expected_files

    @all_expected_files.setter
    def all_expected_files(self, efs: list[str]) -> None:
        self._all_expected_files = efs
