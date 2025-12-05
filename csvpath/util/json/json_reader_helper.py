import datetime
from csvpath.util.class_loader import ClassLoader
from csvpath.matching.util.expression_utility import ExpressionUtility as exut


class JsonReaderHelper:
    @classmethod
    def _is_json(cls, path, filetype) -> bool:
        if filetype == "json":
            return True
        #
        # shouldn't we be looking to config.ini for extension types? or is that already
        # accounted for?
        #
        if path and (
            path.endswith("json") or path.endswith("jsonl") or path.endswith("ndjson")
        ):
            return True
        return False

    @classmethod
    def _json_if(
        cls, *, path: str, filetype: str, delimiter: str = ",", quotechar: str = '"'
    ):
        if not cls._is_json(path, filetype):
            return None
        if path.find("s3://") > -1:
            instance = ClassLoader.load(
                "from csvpath.util.s3.s3_json_data_reader import S3JsonDataReader",
                args=[path],
                kwargs={
                    "delimiter": delimiter,
                    "quotechar": quotechar,
                },
            )
            return instance
        if path.find("sftp://") > -1:
            instance = ClassLoader.load(
                "from csvpath.util.sftp.sftp_json_data_reader import SftpJsonDataReader",
                args=[path],
                kwargs={
                    "delimiter": delimiter,
                    "quotechar": quotechar,
                },
            )
            return instance
        if path.find("azure://") > -1:
            instance = ClassLoader.load(
                "from csvpath.util.azure.azure_json_data_reader import AzureJsonDataReader",
                args=[path],
                kwargs={
                    "delimiter": delimiter,
                    "quotechar": quotechar,
                },
            )
            return instance
        if path.find("gs://") > -1:
            instance = ClassLoader.load(
                "from csvpath.util.gcs.gcs_json_data_reader import GcsJsonDataReader",
                args=[path],
                kwargs={
                    "delimiter": delimiter,
                    "quotechar": quotechar,
                },
            )
            return instance
        instance = ClassLoader.load(
            "from csvpath.util.json.json_data_reader import JsonDataReader", args=[path]
        )
        return instance

    @classmethod
    def line_from_obj(cls, obj, line_number) -> list[str]:
        if isinstance(obj, (tuple, list)):
            return ["" if o is None else str(o) for o in obj]
        elif isinstance(obj, dict):
            obj = {key: obj[key] for key in sorted(obj)}
            keys = list(obj.keys())
            #
            # we sort because a dict does require a certain order of its keys.
            # unless there's a better idea, Jsonl cannot be sure of its header
            # order on any given line.
            #
            line = [cls.string_or_date_string(obj[k]) for k in keys]
            #
            # make a header row if line number is 0 else just a data row
            #
            #
            # check if we have headers for values. i.e. keys == values in first line
            #
            same = True
            if line_number == 0:
                for i, _ in enumerate(line):
                    if _ != keys[i]:
                        same = False
                        break
            if line_number == 0 and not same:
                return (keys, line)
            return line
        else:
            return cls.string_or_date_string(obj)

    @classmethod
    def string_or_date_string(cls, item) -> str:
        if exut.is_none(item):
            return ""
        dt = exut.to_datetime(item)
        if isinstance(dt, datetime.datetime):
            return dt.isoformat()
        return item
