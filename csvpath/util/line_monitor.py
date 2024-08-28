from typing import List, Any


class LineMonitor:
    def __init__(self) -> None:
        self._physical_end_line_count: int = None
        self._physical_end_line_number: int = None
        self._physical_line_count: int = None
        self._physical_line_number: int = None

        self._data_end_line_count: int = None
        self._data_end_line_number: int = None
        self._data_line_count: int = None
        self._data_line_number: int = None

    def is_last_line(self) -> bool:
        return self._physical_end_line_number == self._physical_line_number

    def is_last_line_and_empty(self, line: List[Any]) -> bool:
        ret = True
        if self._physical_end_line_number is None or self._physical_line_number is None:
            ret = False
        if (
            self._physical_end_line_number == self._physical_line_number
            and line
            and len(line) == 0
        ):
            ret = True
        elif self._physical_end_line_number == self._physical_line_number and line:
            for d in line:
                if f"{d}".strip() != "":
                    ret = False
                    break
        else:
            ret = False
        return ret

    @property
    def physical_end_line_count(self) -> int:
        return self._physical_end_line_count

    @property
    def physical_end_line_number(self) -> int:
        return self._physical_end_line_number

    @property
    def physical_line_count(self) -> int:
        return self._physical_line_count

    @property
    def physical_line_number(self) -> int:
        return self._physical_line_number

    @property
    def data_end_line_count(self) -> int:
        return self._data_end_line_count

    @property
    def data_end_line_number(self) -> int:
        return self._data_end_line_number

    @property
    def data_line_count(self) -> int:
        return self._data_line_count

    @property
    def data_line_number(self) -> int:
        return self._data_line_number

    def next_line(self, *, data: List) -> None:
        has_data = data and len(data) > 0
        if self._physical_line_count is None:
            self._physical_line_count = 1
            self._physical_line_number = 0
            if has_data:
                self._data_line_count = 1
                self._data_line_number = 0
            else:
                self._data_line_count = -1
                self._data_line_number = -1
        else:
            self._physical_line_count += 1
            self._physical_line_number += 1
            if has_data:
                if self._data_line_count == -1:
                    self._data_line_count = 0
                self._data_line_count += 1
                self._data_line_number = self._physical_line_number

    def set_end_lines_and_reset(self) -> None:
        """sets the physical and data high watermarks and resets all
        other counts and numbers to starting points
        """
        self._physical_end_line_count = self._physical_line_count
        self._physical_end_line_number = self._physical_line_number
        self._data_end_line_count = self._data_line_count
        self._data_end_line_number = self._data_line_number

        self._physical_line_count = None
        self._physical_line_number = None
        self._data_line_count = None
        self._data_line_number = None

    def is_unset(self) -> bool:
        return not all(
            self._physical_end_line_number,
            self._physical_line_number,
            self._data_end_line_number,
            self._data_line_number,
        )

    def reset(self) -> None:
        self._physical_end_line_number = None
        self._physical_line_number = None
        self._data_end_line_number = None
        self._data_line_number = None

        self._physical_end_line_count = None
        self._physical_line_count = None
        self._data_end_line_count = None
        self._data_line_count = None
