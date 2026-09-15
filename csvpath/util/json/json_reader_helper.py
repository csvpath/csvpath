import datetime
from csvpath.util.class_loader import ClassLoader
from csvpath.matching.util.expression_utility import ExpressionUtility as exut


class JsonReaderHelper:
    @classmethod
    def _json_type(cls, path, filetype) -> bool:
        #
        # returns the "DocumentReader" if we're creating a reader for non-JSONL docs.
        #
        if (
            filetype == "json"
            or (path and path.endswith(".json"))
            or (path and path.endswith(".jsonschema"))
        ):
            return ("json_document_reader", "JsonDocumentReader")
        elif cls._is_json(path, filetype):
            return ("json_data_reader", "JsonDataReader")
        else:
            raise ValueError("Must be a JSON type, not {path}/{filetype}")

    @classmethod
    def _is_json(cls, path, filetype) -> bool:
        if filetype == "json":
            return True
        #
        # look to config.ini for extension types?
        #
        if path and (
            path.endswith("json")
            or path.endswith("jsonl")
            or path.endswith("ndjson")
            or path.endswith("jsonlines")
            or path.endswith("jsonschema")
        ):
            return True
        return False

    @classmethod
    def _json_if(
        cls, *, path: str, filetype: str, delimiter: str = ",", quotechar: str = '"'
    ):
        if not cls._is_json(path, filetype):
            return None
        clz, name = cls._json_type(path, filetype)
        if path.find("s3://") > -1:
            instance = ClassLoader.load(
                f"from csvpath.util.s3.s3_{clz} import S3{name}",
                args=[path],
                kwargs={
                    "delimiter": delimiter,
                    "quotechar": quotechar,
                },
            )
            return instance
        if path.find("sftp://") > -1:
            instance = ClassLoader.load(
                f"from csvpath.util.sftp.sftp_{clz} import Sftp{name}",
                args=[path],
                kwargs={
                    "delimiter": delimiter,
                    "quotechar": quotechar,
                },
            )
            return instance
        if path.find("azure://") > -1:
            instance = ClassLoader.load(
                f"from csvpath.util.azure.azure_{clz} import Azure{name}",
                args=[path],
                kwargs={
                    "delimiter": delimiter,
                    "quotechar": quotechar,
                },
            )
            return instance
        if path.find("gs://") > -1:
            instance = ClassLoader.load(
                f"from csvpath.util.gcs.gcs_{clz} import Gcs{name}",
                args=[path],
                kwargs={
                    "delimiter": delimiter,
                    "quotechar": quotechar,
                },
            )
            return instance
        instance = ClassLoader.load(
            f"from csvpath.util.json.{clz} import {name}", args=[path]
        )
        return instance

    @classmethod
    def line_from_obj(cls, obj, line_number) -> list[str]:
        if isinstance(obj, (tuple, list)):
            return ["" if o is None else str(o) for o in obj]
        elif isinstance(obj, dict):
            #
            # new theory is that we don't sort the keys because headers change on a row-by-row
            # so the positions in the header list don't have meaning and there is no other value
            # to the keys being sorted, and, moreover, if the key order had any meaning to the
            # data generator that information is lost if we sort.
            #
            # obj = {key: obj[key] for key in sorted(obj)}
            keys = list(obj.keys())
            #
            # we sort because a dict does require a certain order of its keys.
            # unless there's a better idea, Jsonl cannot be sure of its header
            # order on any given line.
            #
            line = [cls.string_or_date_string(obj[k]) for k in keys]
            return (keys, line)
            #
            # make a header row if line number is 0 else just a data row
            #
            #
            # check if we have headers for values. i.e. keys == values in first line
            #
            """
            same = True
            if line_number == 0:
                for i, _ in enumerate(line):
                    if _ != keys[i]:
                        same = False
                        break
            if line_number == 0 and not same:
                return (keys, line)
            return line
            """
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
