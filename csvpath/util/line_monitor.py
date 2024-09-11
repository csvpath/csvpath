from typing import List, Any

from .last_line_stats import LastLineStats


class LineMonitor:
    """
    #
    # physical_total_lines == the total number of lines including blanks
    # data_total_lines == the number of lines that have at least one header
    #
    # physical line count == count at the current line being processed including blanks
    # data line count == count at the current line being processed of all lines
    # containing data
    #
    # physical line number is a pointer to a line in the file
    # data line number is a pointer to a line that is being/has been processed
    #
    # the end_line_count and end_line_number are the max lines/counts sentinels. we
    # get them from the first file open that pulls headers and line numbers. once we
    # iterate to get the line count call set_end_lines_and_reset(). that will keep
    # the totals but zero out the others so we're ready to process.
    #
    # pointers are 0-based; they may be used as indexes into lists
    #
    """

    def __init__(self) -> None:
        self._physical_end_line_count: int = None
        self._physical_end_line_number: int = None
        self._physical_line_count: int = None
        self._physical_line_number: int = None

        self._data_end_line_count: int = None
        self._data_end_line_number: int = None
        self._data_line_count: int = None
        self._data_line_number: int = None

        self._last_line_stats = None
        # self.last_line = None

    def __str__(self) -> str:
        return f"""
        physical_end_line_count: {self._physical_end_line_count}
        physical_end_line_number: {self._physical_end_line_number}
        physical_line_count: {self._physical_line_count}
        physical_line_number: {self._physical_line_number}
        data_end_line_count: {self._data_end_line_count}
        data_end_line_number: {self._data_end_line_number}
        data_line_count: {self._data_line_count}
        data_line_number: {self._data_line_number}
        """  # pragma: no cover

    def is_last_line(self) -> bool:
        return self._physical_end_line_number == self._physical_line_number

    def is_last_line_and_blank(self, line: List[Any]) -> bool:
        ret = True
        if self._physical_end_line_number is None or self._physical_line_number is None:
            ret = False
        same = self._physical_end_line_number == self._physical_line_number
        if same and line is not None and len(line) == 0:
            ret = True
        else:
            ret = False
        return ret

    def is_last_line_and_empty(self, line: List[Any]) -> bool:
        ret = True
        if self._physical_end_line_number is None or self._physical_line_number is None:
            ret = False
        same = self._physical_end_line_number == self._physical_line_number
        if same and line is not None and len(line) == 0:
            return True
        if same and line:
            for d in line:
                if f"{d}".strip() != "":
                    ret = False
                    break
        else:
            ret = False
        return ret

    @property  # pragma: no cover
    def physical_end_line_count(self) -> int:
        return self._physical_end_line_count

    @property  # pragma: no cover
    def physical_end_line_number(self) -> int:
        return self._physical_end_line_number

    @property  # pragma: no cover
    def physical_line_count(self) -> int:
        return self._physical_line_count

    @property  # pragma: no cover
    def physical_line_number(self) -> int:
        return self._physical_line_number

    @property  # pragma: no cover
    def data_end_line_count(self) -> int:
        return self._data_end_line_count

    @property  # pragma: no cover
    def data_end_line_number(self) -> int:
        return self._data_end_line_number

    @property  # pragma: no cover
    def data_line_count(self) -> int:
        return self._data_line_count

    @property  # pragma: no cover
    def data_line_number(self) -> int:
        return self._data_line_number

    @property  # pragma: no cover
    def last_line(self) -> LastLineStats:
        return self._last_line_stats

    def next_line(self, *, last_line: List, data: List) -> None:
        self._last_line_stats = LastLineStats(line_monitor=self, last_line=last_line)
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
