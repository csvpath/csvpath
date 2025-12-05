import jsonlines
from .sftp_data_reader import SftpDataReader
from csvpath.util.json.json_reader_helper import JsonReaderHelper


class SftpJsonDataReader(SftpDataReader):
    def next(self) -> list[str]:
        with self as file:
            i = 0
            reader = jsonlines.Reader(file.source)
            for obj in reader.iter(skip_invalid=True):
                line = JsonReaderHelper.line_from_obj(obj, i)
                if isinstance(line, tuple):
                    headers = line[0]
                    line = line[1]
                    yield headers
                    yield line
                else:
                    yield line
                i += 1
