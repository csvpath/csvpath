from csvpath.managers.metadata import Metadata


class FileMetadata(Metadata):
    """@private"""

    def __init__(self, config):
        super().__init__(config)
        # like aname
        self.named_file_name = None
        # any reachable path
        self.origin_path = None
        # like inputs/named_files/aname
        self.name_home = None
        # like inputs/named_files/aname/afile.csv
        self.file_home = None
        # like inputs/named_files/aname/afile.csv/ab12cd546.csv
        self.file_path = None
        # like ab12cd546.csv
        self.file_name = None
        # a name after a '#' char
        self.mark = None
        # like csv
        self.type = None
        self.file_size = 0
        self.template = None
