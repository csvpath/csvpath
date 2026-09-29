from csvpath.managers.metadata import Metadata
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.paths.paths_metadata import PathsMetadata


class MetadataUtility:
    @classmethod
    def type_of_job(self, mdata: Metadata) -> str:
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        if not hasattr(mdata, "method"):
            return "BATCH"
        method = mdata.method
        if method is None:
            raise ValueError("Metadata.method cannot be None")
        if method.strip() == "":
            raise ValueError("Metadata cannot be empty")
        #
        # we us SERVICE for collect_dynamic and fast_forward_dynamic.
        # otherwise for collect_paths and collect_by_line, etc. we use
        # BATCH. when we have shims to streaming messages we'll add
        # STREAMING in some way we could also provide a user controlled
        # way to select a type, but for now, this works.
        #
        if method.find("dynamic") >= 0:
            return "SERVICE"
        return "BATCH"

    @classmethod
    def file_location(self, mdata: Metadata) -> str:
        if isinstance(mdata, FileMetadata):
            return mdata.file_path
        elif isinstance(mdata, PathsMetadata):
            return mdata.group_file_path
        else:
            return mdata.run_home
