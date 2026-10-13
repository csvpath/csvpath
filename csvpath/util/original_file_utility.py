import base64
import binascii
import hashlib
import logging
import re

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
        """returns the path of the copy. the source is read completely
        before anything is written, so a failed read leaves no file."""
        if instance_dir is None or str(instance_dir).strip() == "":
            raise ValueError("Instance dir cannot be None or empty")
        source = OriginalFileUtility.source_path(source)
        dest = Nos(instance_dir).join(OriginalFileUtility.file_name(source))
        nos = Nos(source)
        if nos.is_local and Nos(dest).is_local:
            nos.copy(dest)
            return dest
        data = OriginalFileUtility.read_bytes(source)
        with DataFileWriter(path=dest, mode="wb") as writer:
            writer.write(data)
        return dest

    @staticmethod
    def read_bytes(source: str) -> bytes:
        """the source's bytes, from the local filesystem or a remote
        backend. remote readers are opened binary; xlsx readers always
        are. a reader that cannot open binary falls back to its raw
        lines, which may not be byte-exact: verify() reports that."""
        source = OriginalFileUtility.source_path(source)
        if Nos(source).is_local:
            with open(source, "rb") as f:
                return f.read()
        is_xlsx = OriginalFileUtility.file_name(source).endswith((".xlsx", ".xls"))
        reader = DataFileReader(source)
        try:
            reader.mode = "rb"
            reader.load_if()
            data = reader.source.read()
        except Exception:
            #
            # xlsx readers are always binary and have no line-by-line read,
            # so a failure here is the real error
            #
            if is_xlsx:
                raise
            reader.close()
            reader = DataFileReader(source)
            data = b"".join(
                line if isinstance(line, bytes) else line.encode("utf-8")
                for line in reader.next_raw()
            )
        finally:
            reader.close()
        if isinstance(data, str):
            data = data.encode("utf-8")
        return data

    @staticmethod
    def canonical_digest(fingerprint: str | bytes) -> bytes | None:
        """the raw SHA-256 digest a fingerprint represents, or None if it is
        not one we can read. backends write the same digest differently:
        hex (local, GCS, Azure), base64 (S3's ChecksumSHA256, with / percent-
        encoded), or raw bytes (SFTP's server-side hash, when supported).
        S3's checksum of a multipart upload is a composite, not the digest of
        the bytes, so it gives None."""
        if fingerprint is None:
            raise ValueError("Fingerprint cannot be None")
        if isinstance(fingerprint, (bytes, bytearray)):
            return bytes(fingerprint) if len(fingerprint) == 32 else None
        if not isinstance(fingerprint, str):
            raise TypeError(
                f"Fingerprint must be str or bytes, not {type(fingerprint)}"
            )
        fp = fingerprint.strip()
        #
        # undo Hasher.percent_encode()
        #
        fp = fp.replace("%3A", ":").replace("%2F", "/").replace("%5C", "\\")
        if re.fullmatch(r"[0-9a-fA-F]{64}", fp):
            return bytes.fromhex(fp)
        try:
            raw = base64.b64decode(fp, validate=True)
        except (binascii.Error, ValueError):
            return None
        return raw if len(raw) == 32 else None

    @staticmethod
    def verify(*, source: str, copy: str) -> tuple[bool, str, str]:
        """compares the source's fingerprint with the copy's, as digests, not
        strings, so the same SHA-256 in hex and in base64 match. returns
        (matches, source fingerprint, copy fingerprint). if either
        fingerprint is not a readable digest (e.g. an S3 multipart checksum),
        hashes the bytes of both instead and says so in the fingerprints."""
        if copy is None or str(copy).strip() == "":
            raise ValueError("Copy path cannot be None or empty")
        source = OriginalFileUtility.source_path(source)
        expected = DataFileReader(source).fingerprint()
        actual = DataFileReader(copy).fingerprint()
        e = OriginalFileUtility.canonical_digest(expected)
        a = OriginalFileUtility.canonical_digest(actual)
        if e is not None and a is not None:
            return (e == a, f"{expected}", f"{actual}")
        logging.getLogger(OriginalFileUtility.__name__).warning(
            "Fingerprints %s and %s are not both readable SHA-256 digests; "
            "comparing SHA-256 of the bytes instead",
            expected,
            actual,
        )
        e = hashlib.sha256(OriginalFileUtility.read_bytes(source)).hexdigest()
        a = hashlib.sha256(OriginalFileUtility.read_bytes(copy)).hexdigest()
        return (e == a, f"sha256:{e}", f"sha256:{a}")
