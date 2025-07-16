from .scanner2_parser import Scanner2Parser


class Scanner2:
    def __init__(self, csvpath=None):
        self.these: list = []
        self.wild_from_last = False

        self._filename = None
        self.path = None
        self.instructions = None
        self.parser = None
        self.csvpath = csvpath

    @property
    def filename(self) -> str:
        return self._filename

    @filename.setter
    def filename(self, f: str) -> None:
        if f is None:
            self._filename = None
            return
        if not isinstance(f, str):
            raise ValueError("Filename must be a string")
        f = f.strip()
        self._filename = f

    #
    # these next three properties match to the original scanner methods
    #
    @property
    def from_line(self) -> int:
        if self._these_first == -1 and self.wild_from_last:
            return 0
        return self._these_first

    @property
    def to_line(self) -> int:
        if self.wild_from_last:
            return self.csvpath.line_monitor.physical_end_line_number
        return self._these_last

    @property
    def all_lines(self) -> list:
        return self.wild_from_last

    def __eq__(self, o) -> bool:
        if (
            not hasattr(o, "these")
            or not hasattr(o, "all_lines")
            or not hasattr(o, "from_line")
            or not hasattr(o, "to_line")
            or not hasattr(o, "path")
        ):
            return False
        return (
            self.these == o.these
            and self.all_lines == o.all_lines
            and self.from_line == o.from_line
            and self.to_line == o.to_line
            and self.path == o.path
        )

    def __str__(self):
        ffrom = self.these[0] if len(self.these) > 0 else 0
        tto = self.these[len(self.these) - 1] if len(self.these) > 0 else 0
        return f"""
            path: {self.path}
            from_line: {ffrom}
            to_line: {tto}
            wild_from_last: {self.wild_from_last}
            these: {self.these}
        """

    def is_last(  # pylint: disable=R0913
        self,
        line: int,
        *,
        from_line: int = -1,
        to_line: int = -1,
        all_lines: bool = None,
        these: list[int] = None,
    ) -> bool:
        last = self._these_last
        if last == line and self.wild_from_last is False:
            return True
        elif (
            self.wild_from_last
            and self.csvpath.line_monitor.physical_end_line_number == line
        ):
            return True
        return False

    def includes(
        self,
        line: int,
        *,
        from_line: int = -1,
        to_line: int = -1,
        all_lines: bool = None,
        these: list[int] = None,
    ) -> bool:
        if self.wild_from_last is True and len(self.these) == 0:
            ret = True
        elif self.wild_from_last is True and line >= self._these_last:
            ret = True
        elif line < self._these_first:
            ret = False
        elif line > self._these_last:
            ret = False
        else:
            ret = line in self.these
        return ret

    @property
    def _these_last(self) -> int:
        return -1 if len(self.these) == 0 else self.these[len(self.these) - 1]

    @property
    def _these_first(self) -> int:
        return -1 if len(self.these) == 0 else self.these[0]

    # ===================
    # parsing
    # ===================

    def parse(self, data) -> bool:
        self.path = data
        if data:
            data = data.strip()
            if data[0] != "$":
                raise ValueError("Csvpaths start with '$'")
            self.filename = data[1 : data.find("[")]
            data = data[data.find("[") :]
            data = data[0 : data.find("]") + 1]
            self.instructions = data
        parsing_result = False
        if self.instructions:
            self.parser = Scanner2Parser(self)
            parsing_result = self.parser.parse_instructions(self.instructions)
        return parsing_result
