from csvpath.managers.metadata import Metadata


class FileMetadata(Metadata):
    def __init__(self):
        super().__init__()
        self.named_file_name = None
        self.origin_path = None
        self.name_home = None
        self.file_path = None
        self.file_home = None
        self.file_name = None
        self.mark = None
        self.type = None
