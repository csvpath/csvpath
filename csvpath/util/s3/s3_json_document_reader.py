import json
from .s3_data_reader import S3DataReader


class S3JsonDocumentReader(S3DataReader):
    def next(self) -> list[str]:
        with self as file:
            yield json.load(file.source)
