# pylint: disable=C0114
import hashlib


class Hasher:
    def hash(self, path, *, encode=True) -> str:
        h = None
        try:
            h = self._post(path)
        except AttributeError:
            h = self._pre(path)
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
        with open(path, "rb", buffering=0) as source:
            h = hashlib.file_digest(source, hashlib.sha256)
            h = h.hexdigest()
            return h

    def _pre(self, path):
        h = None
        hl = hashlib.sha256()
        b = bytearray(128 * 1024)
        mv = memoryview(b)
        with open(path, "rb", buffering=0) as source:
            while n := source.readinto(mv):
                hl.update(mv[:n])
        h = hl.hexdigest()
        return h
