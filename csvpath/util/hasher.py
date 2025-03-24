# pylint: disable=C0114
import hashlib
from .path_util import PathUtility as pathu


class Hasher:
    def hash(self, file_or_path, *, encode=True) -> str:
        #
        # some callers pass in a temp file object -- e.g. sftp.
        # we'll try for that first and fall back to the expected
        # string.
        #
        h = self._file_if(file_or_path)
        if h is None:
            try:
                h = self._post(file_or_path)
            except (IOError, AttributeError):
                h = self._pre(file_or_path)
            if h is None:
                raise RuntimeError("Cannot generate hashcode")
        #
        # we use fingerprints as names in some cases. that means that ':' and
        # '/' and '\' are problemmatic. all fingerprints come from this or any
        # subclasses' override, so if we hack on the fingerprint here it should
        # be fine. the exception would be that a forensic view would also
        # require the same escape, if checking for file mods. for matching not
        # a problem.
        #
        if encode:
            h = Hasher.percent_encode(h)
        return h

    @classmethod
    def percent_encode(cls, fingerprint: str) -> str:
        fingerprint = fingerprint.replace(":", "%3A")
        fingerprint = fingerprint.replace("/", "%2F")
        fingerprint = fingerprint.replace("\\", "%5C")
        return fingerprint

    def _post(self, path):
        path = pathu.resep(path)
        with open(path, "rb", buffering=0) as source:
            h = hashlib.file_digest(source, hashlib.sha256)
            h = h.hexdigest()
            return h

    def _file_if(self, f):
        if isinstance(f, str):
            return None
        f.seek(0)
        h = hashlib.file_digest(f, hashlib.sha256)
        h = h.hexdigest()
        return h

    def _pre(self, path):
        path = pathu.resep(path)
        h = None
        hl = hashlib.sha256()
        b = bytearray(128 * 1024)
        mv = memoryview(b)
        with open(path, "rb", buffering=0) as source:
            while n := source.readinto(mv):
                hl.update(mv[:n])
        h = hl.hexdigest()
        return h
