import uuid
from datetime import datetime


class FileMetadata:
    def __init__(self):
        self.time = datetime.now()
        self.uuid = uuid.uuid4()
        self.named_file_name = None
        self.origin_path = None
        self.archive_path = None
        self.name_home = None
        self.file_home = None
        self.file_name = None
        self.fingerprint = None
        self.mark = None
        self.type = None
        self.manifest_path = None
