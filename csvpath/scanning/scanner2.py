from .scanner2_parser import Scanner2Parser

from csvpath.util.references.reference_parser import ReferenceParser


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
        #
        # TODO: caution: there may not to be one place where we parse the whole of the
        # csvpath expression for correctness, as opposed to parsing the scan part
        # and the match part.
        #
        if data is None:
            raise ValueError("Data cannot be None")
        if not isinstance(data, str):
            raise ValueError("Data must be a string, not {type(data)}")
        data = data.strip()
        self.path = data
        if data[0] != "$":
            raise ValueError("Csvpaths start with '$'")
        self.filename = data[1 : data.find("[")]

        #
        # we need to check for a root minor
        #
        print(f"scanner2: self.filname 1: {self.filename}")
        self._add_root_minor_to_filename_if()
        print(f"scanner2: self.filname 2: {self.filename}")

        #
        #
        #
        data = data[data.find("[") :]
        data = data[0 : data.find("]") + 1]
        self.instructions = data
        parsing_result = False
        if self.instructions:
            self.parser = Scanner2Parser(self)
            parsing_result = self.parser.parse_instructions(self.instructions)
        return parsing_result

    def _add_root_minor_to_filename_if(self) -> None:
        #
        # a csvpath statement's path can take a "root minor" name. typically that points to a
        # tab in an excel file, but in principle there could be other uses. we capture that info
        # in the CsvPaths layer, but have to add it here in order for it to have an effect on
        # an individual csvpath run. at the same time, we cannot leave #... hanging on the end
        # of the filepath because #... will be seen as part of the filename by the OS making
        # paths incorrect. Cache is another example of a place we have to act to align the #
        # reference or path notation to what we're doing. Here we want #...; in Cache we need
        # it stripped off.
        #
        if not self.csvpath:
            return
        print(
            f"scanner2: _add_root_minor_to_filename_if 1: {self.csvpath.named_file_name}"
        )
        if self.csvpath.named_file_name is None:
            return
        if self.csvpath.named_file_name.find("#") == -1:
            return
        print(
            f"scanner2: _add_root_minor_to_filename_if 2: {self.csvpath.named_file_name}"
        )
        if not self.csvpath.named_file_name.strip().startswith("$"):
            #
            # non references can have a root_minor, but we don't expect them in
            # named-file names that are not references.
            #
            raise ValueError(
                f"Named-file name with # but not a reference is not supported: {self.csvpath.named_file_name}"
            )
        if self.filename.find("#") > -1:
            #
            # presumably we already added the root minor
            #
            return
        ref = ReferenceParser(self.csvpath.named_file_name)
        print(f"scanner2: _add_root_minor_to_filename_if 3: {ref}")
        if ref.root_minor is None:
            raise ValueError(
                "Root minor cannot be None when a named-file reference has a #"
            )
        self.filename = f"{self.filename}#{ref.root_minor}"
