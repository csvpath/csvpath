import uuid
from abc import ABC, abstractmethod
from datetime import datetime


class Metadata(ABC):
    def __init__(self):
        self.time = datetime.now()
        self.uuid = uuid.uuid4()
        self.fingerprint: str = None
        self.manifest_path: str = None
