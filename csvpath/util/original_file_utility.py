from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos


class OriginalFileUtility:
    """copies a run's registered data file into a result's instance
    directory as the well-known file original.<ext>, byte for byte."""

    NAME = "original"

    @staticmethod
    def source_path(path: str) -> str:
        """strips a worksheet selector, e.g. orders.xlsx#Sheet1"""
        if path is None or str(path).strip() == "":
            raise ValueError("Source path cannot be None or empty")
        i = path.find("#")
        return path if i == -1 else path[0:i]

    @staticmethod
    def file_name(source: str) -> str:
        """original.<ext>, taking the extension from the source"""
        source = OriginalFileUtility.source_path(source)
        name = source.replace("\\", "/").rsplit("/", 1)[-1]
        i = name.rfind(".")
        if i == -1 or i == len(name) - 1:
            return OriginalFileUtility.NAME
        return f"{OriginalFileUtility.NAME}{name[i:].lower()}"

    @staticmethod
    def copy_original(*, source: str, instance_dir: str) -> str:
        """returns the path of the copy"""
        if instance_dir is None or str(instance_dir).strip() == "":
            raise ValueError("Instance dir cannot be None or empty")
        source = OriginalFileUtility.source_path(source)
        dest = Nos(instance_dir).join(OriginalFileUtility.file_name(source))
        nos = Nos(source)
        if nos.is_local and Nos(dest).is_local:
            nos.copy(dest)
        else:
            #
            # as FileManager._copy_down(): stream raw bytes, which works for
            # xlsx and the remote backends
            #
            with DataFileReader(source) as reader:
                with DataFileWriter(path=dest, mode="wb") as writer:
                    for line in reader.next_raw():
                        writer.append(line)
        return dest
