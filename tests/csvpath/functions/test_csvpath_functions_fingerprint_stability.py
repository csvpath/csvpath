"""Determinism and sensitivity tests for line_fingerprint(), store_line_fingerprint() and file_fingerprint().

docs/functions/fingerprint.md says the fingerprint functions take a sha256
digest of a file or its lines "for future reference ... finding duplicates,
and ascertaining a file has not changed". That needs two things:

- determinism: the same input gives the same hash on every run
- sensitivity: a changed input gives a different hash

The two fixtures differ by exactly one byte, the last letter of the last row:

    fingerprint_a.csv   id,name / 1,alpha / 2,beta
    fingerprint_b.csv   id,name / 1,alpha / 2,betb

The tests use name qualifiers for the metadata keys. The default key for
file_fingerprint() differs between the docs ("fingerprint") and the code
("file_fingerprint"), which is reported as a finding and not asserted here.
"""

import hashlib
import os

from csvpath import CsvPath

RESOURCES = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}"
FILE_A = f"{RESOURCES}fingerprint_a.csv"
FILE_B = f"{RESOURCES}fingerprint_b.csv"

LINES_CSVPATH = "[*][ line_fingerprint.lines() last() -> store_line_fingerprint.lines() ]"
FILE_CSVPATH = "[*][ last() -> file_fingerprint.whole() ]"


def _metadata(*, file: str, csvpath: str) -> dict:
    path = CsvPath()
    path.parse(f"${file}{csvpath}")
    path.fast_forward()
    return path.metadata


def _line_hash(*, file: str) -> str:
    return _metadata(file=file, csvpath=LINES_CSVPATH)["lines"]


def _file_hash(*, file: str) -> str:
    return _metadata(file=file, csvpath=FILE_CSVPATH)["whole"]


def _sha256_of(*, file: str) -> str:
    with open(file, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def test_fixtures_differ_by_one_byte():
    # guards the sensitivity tests: if the fixtures drift apart they would
    # no longer test a single-byte change
    with open(FILE_A, "rb") as a, open(FILE_B, "rb") as b:
        bytes_a = a.read()
        bytes_b = b.read()
    assert len(bytes_a) == len(bytes_b)
    assert sum(1 for x, y in zip(bytes_a, bytes_b) if x != y) == 1


# ---------------------------------------------------------------------------
# line_fingerprint() + store_line_fingerprint()
# ---------------------------------------------------------------------------


def test_line_fingerprint_is_deterministic():
    first = _line_hash(file=FILE_A)
    second = _line_hash(file=FILE_A)
    assert first == second
    # a sha256 hex digest is 64 hex characters
    assert len(first) == 64
    int(first, 16)


def test_line_fingerprint_changes_with_one_byte():
    assert _line_hash(file=FILE_A) != _line_hash(file=FILE_B)


def test_store_line_fingerprint_moves_the_hash_to_metadata():
    # the docs: store_line_fingerprint() migrates the by-line fingerprint from
    # its variable into metadata, under the same name, with the algorithm
    path = CsvPath()
    path.parse(f"${FILE_A}{LINES_CSVPATH}")
    path.fast_forward()
    assert "lines" in path.metadata
    assert "lines" not in path.variables
    assert path.metadata["hash_algorithm"] == "sha256"


def test_line_fingerprint_depends_on_the_lines_scanned():
    # the hash is built line by line, so scanning fewer lines of the same
    # file gives a different hash. Lines 0-1 are the same in both fixtures,
    # so those hashes must also match each other.
    partial = "[0-1][ line_fingerprint.lines() last() -> store_line_fingerprint.lines() ]"
    a_partial = _metadata(file=FILE_A, csvpath=partial)["lines"]
    b_partial = _metadata(file=FILE_B, csvpath=partial)["lines"]
    assert a_partial == b_partial
    assert a_partial != _line_hash(file=FILE_A)


def test_line_fingerprint_names_are_independent():
    # two differently named line fingerprints over the same lines agree
    csvpath = """[*][
        line_fingerprint.one()
        line_fingerprint.two()
        last() -> store_line_fingerprint.one()
        last() -> store_line_fingerprint.two()
    ]"""
    metadata = _metadata(file=FILE_A, csvpath=csvpath)
    assert metadata["one"] == metadata["two"] == _line_hash(file=FILE_A)


# ---------------------------------------------------------------------------
# file_fingerprint()
# ---------------------------------------------------------------------------


def test_file_fingerprint_is_deterministic():
    assert _file_hash(file=FILE_A) == _file_hash(file=FILE_A)


def test_file_fingerprint_is_the_sha256_of_the_file():
    # the docs: "Enters the SHA256 hash of the current data file into metadata"
    metadata = _metadata(file=FILE_A, csvpath=FILE_CSVPATH)
    assert metadata["whole"] == _sha256_of(file=FILE_A)
    assert metadata["hash_algorithm"] == "sha256"


def test_file_fingerprint_changes_with_one_byte():
    assert _file_hash(file=FILE_A) != _file_hash(file=FILE_B)
    assert _file_hash(file=FILE_B) == _sha256_of(file=FILE_B)


def test_file_fingerprint_does_not_depend_on_the_lines_scanned():
    # unlike the line fingerprint, the file hash covers the whole file
    # however much of it the csvpath scans
    one_line = _metadata(file=FILE_A, csvpath="[1][ file_fingerprint.whole() ]")
    assert one_line["whole"] == _file_hash(file=FILE_A)
