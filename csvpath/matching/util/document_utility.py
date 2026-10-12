from csvpath.util.file_readers import DataFileReader
from csvpath.matching.util.exceptions import MatchException


class DocumentUtility:
    """support for functions that evaluate the whole data file as one
    document, rather than line by line: the one-argument forms of xpath()
    and jsonpath().

    a whole-document function evaluates the document on one line only.
    the usual way to get that is to scan [*] and make stop() the last match
    component, which runs on the first line with data. [0] also works when
    the file does not start with a blank line.
    """

    @staticmethod
    def assert_one_line(*, function, first_line: int | None) -> int:
        """returns the current line number. if the function already
        evaluated the document on a different line, stops the run and
        raises a MatchException."""
        if function is None:
            raise ValueError("Function cannot be None")
        csvpath = function.matcher.csvpath
        line = csvpath.line_monitor.physical_line_number
        if first_line is not None and first_line != line:
            msg = (
                f"{function.name}() evaluates the whole document, so it must run on "
                f"one line only. It ran on line {first_line} and again on line {line}. "
                "Scan [*] with stop() as the last match component, or scan [0]"
            )
            csvpath.logger.error(msg)
            csvpath.stop()
            raise MatchException(msg)
        return line

    @staticmethod
    def read_document(*, function) -> str:
        """returns the text of the data file the run is scanning"""
        if function is None:
            raise ValueError("Function cannot be None")
        path = function.matcher.csvpath.scanner.filename
        if path is None or str(path).strip() == "":
            msg = f"{function.name}() cannot find the document: no data file path"
            function.matcher.csvpath.logger.error(msg)
            raise MatchException(msg)
        with DataFileReader(path) as reader:
            return reader.read()
