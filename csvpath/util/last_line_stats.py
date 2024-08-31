from typing import List, Any


class LastLineStats:
    def __init__(self, *, line_monitor, last_line: List[List[Any]]) -> None:
        # how many headers
        self.last_line_length = 0
        # how many non-blank values
        self.last_line_nonblank = 0
        self.last_line_number = line_monitor.physical_line_number
        self.last_data_line_number = line_monitor.data_line_number
        if last_line is not None:
            self._ingest_line(last_line)

    def __str__(self) -> None:
        return f"""LastLineStats: line len: {self.last_line_length}, non-blanks: {self.last_line_nonblank}, physical line no: {self.last_line_number}"""

    def _ingest_line(self, line: List[List[Any]]) -> None:
        self._last_line_length = len(line)
        i = 0
        for h in line:
            if f"{h}".strip() == "":
                continue
            i += 1
        self.last_line_nonblank = i
