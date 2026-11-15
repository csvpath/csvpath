"""Writes the files for the second live probe against Amazon Macie: the
three differences the first live check left open
(specs/macie/live-check-2026-11-11.md). One variant per row, so Macie's
cell locations say which variants it reports. Every value is made up.

    poetry run python tests/macie/live/make_probe_files.py <out dir>

writes <out dir>/probe/*.csv (to upload under probe/ in the bucket) and
<out dir>/expected_probe.json, what the Framework's stand-ins are
expected to find. As with make_live_files.py, the files are written, not
committed, and are deterministic.
"""

import json
import os
import random
import sys

import make_live_files as mlf
from csvpath.macie.util.checksum_utility import ChecksumUtility as chut

SEED = 20261111
#
# the value the first live check used, kept as a control
#
FIRST_DE_ID = "HCYFH089R5"
FIRST_CF = "RSSMRA85T10A562S"


def _cf(body: str) -> str:
    return body + chut.it_cf_check(code=body)


def phones(rng) -> mlf.LiveFile:
    #
    # is it the country-code rule, or the spaces? the first check's
    # "+1 212 555 0148" in a notes column was not reported
    #
    f = mlf.LiveFile(name="probe_phones.csv", headers=["id", "phone", "notes"])
    for value, note in [
        ("+1 212 555 0148", "control: the first check's value"),
        ("+12125550148", "country code, no separators"),
        ("+1-212-555-0148", "country code, dashes"),
        ("+1 (212) 555-0148", "country code, area code in parentheses"),
        ("+1.212.555.0148", "country code, dots"),
    ]:
        f.add(
            cells={"id": "r", "notes": f"call {value}"},
            expect=[("notes", "PHONE_NUMBER", 1, f"no keyword; {note}")],
        )
    #
    # our stand-in does not report these without a keyword
    #
    for value, note in [
        ("+44 20 7946 0958", "UK country code, spaces"),
        ("+49 30 12345678", "German country code, spaces"),
    ]:
        f.add(
            cells={"id": "r", "notes": f"call {value}"},
            expect=[("notes", "PHONE_NUMBER", 0, f"no keyword; {note} (ours: 0)")],
        )
    f.add(
        cells={"id": "r", "phone": "+1 212 555 0148"},
        expect=[("phone", "PHONE_NUMBER", 1, "header keyword, spaces")],
    )
    f.add(
        cells={"id": "r", "notes": "phone +1 212 555 0148"},
        expect=[("notes", "PHONE_NUMBER", 1, "keyword in the cell, spaces")],
    )
    f.add(
        cells={"id": "r", "notes": "phone 212 555 0149"},
        expect=[("notes", "PHONE_NUMBER", 1, "keyword in the cell, no country code")],
    )
    return f


def german_ids(rng) -> mlf.LiveFile:
    #
    # was HCYFH089R5 outside what Macie accepts, or was the header not
    # read as a keyword?
    #
    f = mlf.LiveFile(name="probe_de_id.csv", headers=["id", "personalausweis", "notes"])
    expect = "GERMANY_NATIONAL_IDENTIFICATION_NUMBER"
    f.add(
        cells={"id": "r", "personalausweis": FIRST_DE_ID},
        expect=[("personalausweis", expect, 1, "control: the first check's value")],
    )
    f.add(
        cells={"id": "r", "notes": f"personalausweis: {FIRST_DE_ID}"},
        expect=[("notes", expect, 1, "the same value, keyword in the cell")],
    )
    for _ in range(3):
        f.add(
            cells={"id": "r", "personalausweis": mlf.de_id(rng)},
            expect=[("personalausweis", expect, 1, "another 2010-format value")],
        )
    f.add(
        cells={"id": "r", "notes": f"ausweisnummer {mlf.de_id(rng)}"},
        expect=[("notes", expect, 1, "another keyword, in the cell")],
    )
    #
    # the pre-2010 card: ten digits, the last an ICAO check digit. Our
    # stand-in takes it; this asks whether Macie does
    #
    old = "122000129"
    f.add(
        cells={"id": "r", "personalausweis": old + chut.icao_check(text=old)},
        expect=[("personalausweis", expect, 1, "pre-2010 format, all digits")],
    )
    return f


def codici_fiscali(rng) -> mlf.LiveFile:
    #
    # a keyword problem (the underscore header) or a value check we do not
    # do (birth date, municipality code)?
    #
    f = mlf.LiveFile(
        name="probe_it_cf.csv",
        headers=["id", "codice_fiscale", "codice fiscale", "notes"],
    )
    expect = "ITALY_NATIONAL_IDENTIFICATION_NUMBER"
    f.add(
        cells={"id": "r", "codice_fiscale": FIRST_CF},
        expect=[("codice_fiscale", expect, 1, "control: the first check's value")],
    )
    f.add(
        cells={"id": "r", "codice fiscale": FIRST_CF},
        expect=[("codice fiscale", expect, 1, "header with a space")],
    )
    f.add(
        cells={"id": "r", "notes": f"codice fiscale: {FIRST_CF}"},
        expect=[("notes", expect, 1, "keyword in the cell")],
    )
    for body, note in [
        ("BNCLRA70A41H501", "a woman born in Rome"),
        ("VRDGPP80C15F205", "a man born in Milan"),
        ("MRTFNC92E22L219", "a man born in Turin"),
    ]:
        f.add(
            cells={"id": "r", "codice_fiscale": _cf(body)},
            expect=[("codice_fiscale", expect, 1, note)],
        )
    f.add(
        cells={"id": "r", "notes": f"tax code {_cf('BNCLRA70A41H501')}"},
        expect=[("notes", expect, 1, "another keyword, in the cell")],
    )
    return f


FILES = [phones, german_ids, codici_fiscali]

#
# the third probe (2026-11-15): do managed identifiers' keywords match as
# substrings, as we match them, or as words? The second probe found
# `codice fiscale` is not a keyword to Macie although it contains the
# documented `codice fiscal`. Also: the two phone forms Macie reported
# without a keyword, for other countries
#
SEED_2 = 20261115


def keywords(rng) -> mlf.LiveFile:
    f = mlf.LiveFile(
        name="probe2_keywords.csv",
        headers=[
            "id",
            "ssn",
            "ssnumber",
            "customer_ssn",
            "itin",
            "itinerary",
            "dob",
            "dobson",
            "codice fiscal",
            "tax code",
            "notes",
        ],
    )
    ssn, itin, cf = (
        "USA_SOCIAL_SECURITY_NUMBER",
        ("USA_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER"),
        "ITALY_NATIONAL_IDENTIFICATION_NUMBER",
    )
    for column, value, identifier, note in [
        ("ssn", mlf.ssn(rng), ssn, "control: the keyword is the header"),
        ("ssnumber", mlf.ssn(rng), ssn, "keyword at the start of a longer word"),
        ("customer_ssn", mlf.ssn(rng), ssn, "keyword after an underscore"),
        ("notes", f"ssn {mlf.ssn(rng)}", ssn, "control: keyword in the cell"),
        ("notes", f"myssn {mlf.ssn(rng)}", ssn, "keyword at the end of a word"),
        ("itin", mlf.itin(rng), itin, "control: the keyword is the header"),
        ("itinerary", mlf.itin(rng), itin, "keyword inside itinerary"),
        ("dob", "1985-11-05", "DATE_OF_BIRTH", "control: the keyword is the header"),
        ("dobson", "1985-11-06", "DATE_OF_BIRTH", "keyword inside dobson"),
        ("codice fiscal", FIRST_CF, cf, "the documented keyword, exactly"),
        ("tax code", FIRST_CF, cf, "control: a keyword Macie took in a cell"),
    ]:
        f.add(
            cells={"id": "r", column: value},
            expect=[(column, identifier, 1, note)],
        )
    return f


def phones_2(rng) -> mlf.LiveFile:
    f = mlf.LiveFile(name="probe2_phones.csv", headers=["id", "notes"])
    for value, n, note in [
        ("+12125550148", 1, "control: reported by Macie in the second probe"),
        ("+442079460958", 0, "UK, unbroken"),
        ("+44 (20) 7946 0958", 0, "UK, area code in parentheses"),
        ("+493012345678", 0, "Germany, unbroken"),
        ("+49 (30) 12345678", 0, "Germany, area code in parentheses"),
    ]:
        f.add(
            cells={"id": "r", "notes": f"call {value}"},
            expect=[("notes", "PHONE_NUMBER", n, f"no keyword; {note}")],
        )
    return f


FILES_2 = [keywords, phones_2]
#
# probe number -> seed, files, directory, expectations file
#
PROBES = {
    1: (SEED, FILES, "probe", "expected_probe.json"),
    2: (SEED_2, FILES_2, "probe2", "expected_probe2.json"),
}


def write_all(*, out: str, probe: int = 1) -> dict:
    if not isinstance(out, str) or out.strip() == "":
        raise ValueError("out must be a directory path")
    if probe not in PROBES:
        raise ValueError(f"probe must be one of {sorted(PROBES)}, not {probe!r}")
    seed, files, directory, expectations = PROBES[probe]
    rng = random.Random(seed)
    data = os.path.join(out, directory)
    os.makedirs(data, exist_ok=True)
    expected = []
    for make in files:
        f = make(rng)
        f.write(directory=data)
        expected.extend(f.expected)
    doc = {"seed": seed, "expected": expected}
    with open(os.path.join(out, expectations), "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
        fh.write("\n")
    return doc


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.stderr.write("usage: make_probe_files.py <out dir> [probe number]\n")
        sys.exit(2)
    n = int(sys.argv[2]) if len(sys.argv) == 3 else 1
    result = write_all(out=sys.argv[1], probe=n)
    sys.stdout.write(
        f"wrote probe {n}: {len(PROBES[n][1])} files and "
        f"{len(result['expected'])} expectations to {sys.argv[1]}\n"
    )
