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

import csv
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
    #
    # the counts are what Macie reported (2026-11-14), which our rule now
    # follows: unbroken, or with a group in parentheses
    #
    for value, n, note in [
        ("+1 212 555 0148", 0, "control: the first check's value"),
        ("+12125550148", 1, "country code, no separators"),
        ("+1-212-555-0148", 0, "country code, dashes"),
        ("+1 (212) 555-0148", 1, "country code, area code in parentheses"),
        ("+1.212.555.0148", 0, "country code, dots"),
    ]:
        f.add(
            cells={"id": "r", "notes": f"call {value}"},
            expect=[("notes", "PHONE_NUMBER", n, f"no keyword; {note}")],
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
    #
    # "codice fiscale" is a longer word than the keyword "codice fiscal",
    # so none of these is reported (Macie, 2026-11-14; ours since the
    # whole-word rule). "tax code" is a keyword
    #
    f.add(
        cells={"id": "r", "codice_fiscale": FIRST_CF},
        expect=[("codice_fiscale", expect, 0, "control: the first check's value")],
    )
    f.add(
        cells={"id": "r", "codice fiscale": FIRST_CF},
        expect=[("codice fiscale", expect, 0, "header with a space")],
    )
    f.add(
        cells={"id": "r", "notes": f"codice fiscale: {FIRST_CF}"},
        expect=[("notes", expect, 0, "keyword in the cell")],
    )
    for body, note in [
        ("BNCLRA70A41H501", "a woman born in Rome"),
        ("VRDGPP80C15F205", "a man born in Milan"),
        ("MRTFNC92E22L219", "a man born in Turin"),
    ]:
        f.add(
            cells={"id": "r", "codice_fiscale": _cf(body)},
            expect=[("codice_fiscale", expect, 0, note)],
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
    ssn = "USA_SOCIAL_SECURITY_NUMBER"
    itin = "USA_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER"
    cf = "ITALY_NATIONAL_IDENTIFICATION_NUMBER"
    #
    # the counts are what Macie reported (2026-11-15), which our rule now
    # follows: a keyword inside a longer word does not count
    #
    for column, value, identifier, n, note in [
        ("ssn", mlf.ssn(rng), ssn, 1, "control: the keyword is the header"),
        ("ssnumber", mlf.ssn(rng), ssn, 0, "keyword at the start of a longer word"),
        ("customer_ssn", mlf.ssn(rng), ssn, 1, "keyword after an underscore"),
        ("notes", f"ssn {mlf.ssn(rng)}", ssn, 1, "control: keyword in the cell"),
        ("notes", f"myssn {mlf.ssn(rng)}", ssn, 0, "keyword at the end of a word"),
        ("itin", mlf.itin(rng), itin, 1, "control: the keyword is the header"),
        ("itinerary", mlf.itin(rng), itin, 0, "keyword inside itinerary"),
        ("dob", "1985-11-05", "DATE_OF_BIRTH", 1, "control: the keyword is the header"),
        ("dobson", "1985-11-06", "DATE_OF_BIRTH", 0, "keyword inside dobson"),
        ("codice fiscal", FIRST_CF, cf, 1, "the documented keyword, exactly"),
        ("tax code", FIRST_CF, cf, 1, "control: a keyword Macie took in a cell"),
    ]:
        f.add(
            cells={"id": "r", column: value},
            expect=[(column, identifier, n, note)],
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
# the fourth live probe (2026-11-16): the phone rule for the countries
# other than the US. The second probe found Macie reports a +1 number with
# no keyword only unbroken or with a group in parentheses; our rule
# applies that to every country. Each country's identifier, its number in
# four forms with no keyword, and once near a keyword
#
SEED_3 = 20261116
PHONES_3 = {
    "UK_PHONE_NUMBER": [
        "+442079460958",
        "+44 (20) 7946 0958",
        "+44 20 7946 0958",
        "+44-20-7946-0958",
    ],
    "FRANCE_PHONE_NUMBER": [
        "+33123456789",
        "+33 (1) 23 45 67 89",
        "+33 1 23 45 67 89",
        "+33-1-23-45-67-89",
    ],
    "GERMANY_PHONE_NUMBER": [
        "+4930123456",
        "+49 (30) 123456",
        "+49 30 123456",
        "+49-30-123456",
    ],
    "ITALY_PHONE_NUMBER": [
        "+393123456789",
        "+39 (312) 345 6789",
        "+39 312 345 6789",
        "+39-312-345-6789",
    ],
    "SPAIN_PHONE_NUMBER": [
        "+34612345678",
        "+34 (612) 34 56 78",
        "+34 612 34 56 78",
        "+34-612-34-56-78",
    ],
    "BRAZIL_PHONE_NUMBER": [
        "+5511961234567",
        "+55 (11) 96123-4567",
        "+55 11 96123 4567",
        "+55-11-96123-4567",
    ],
}


def phones_3(rng) -> mlf.LiveFile:
    f = mlf.LiveFile(name="probe3_phones.csv", headers=["id", "notes"])
    for identifier, (unbroken, parens, spaced, dashed) in PHONES_3.items():
        for value, n, note in [
            #
            # the counts are ours since the rule change (2026-11-17): an
            # international number outside the US is found only unbroken
            #
            (unbroken, 1, "unbroken"),
            (parens, 0, "a group in parentheses"),
            (spaced, 0, "spaces between the groups"),
            (dashed, 0, "dashes between the groups"),
        ]:
            f.add(
                cells={"id": "r", "notes": f"call {value}"},
                expect=[("notes", identifier, n, f"no keyword; {note}")],
            )
        f.add(
            cells={"id": "r", "notes": f"phone {spaced}"},
            expect=[("notes", identifier, 0, "keyword in the cell, spaces")],
        )
    return f


FILES_3 = [phones_3]

#
# the fifth live probe (2026-11-17), following the fourth: national
# numbers after a keyword, in the cell and as the column header; an
# international number with spaces under a phone header; other unbroken
# numbers for Germany and Italy, whose first were not reported; and
# Brazil, which the fourth probe's job left out
#
SEED_4 = 20261117
PHONES_4 = {
    #
    # identifier: (national, international with spaces, other unbroken)
    #
    "UK_PHONE_NUMBER": ("020 7946 0958", "+44 20 7946 0958", ["+441214960123"]),
    "FRANCE_PHONE_NUMBER": ("01 23 45 67 89", "+33 1 23 45 67 89", ["+33612345678"]),
    "GERMANY_PHONE_NUMBER": (
        "030 12345678",
        "+49 30 12345678",
        ["+493012345678", "+4915112345678", "+498912345678"],
    ),
    "ITALY_PHONE_NUMBER": (
        "06 1234 5678",
        "+39 06 1234 5678",
        ["+390612345678", "+393471234567"],
    ),
    "SPAIN_PHONE_NUMBER": ("612 34 56 78", "+34 612 34 56 78", ["+34912345678"]),
    "BRAZIL_PHONE_NUMBER": (
        "(11) 96123-4567",
        "+55 11 96123 4567",
        ["+5511961234567", "+552133334444"],
    ),
}


def phones_4(rng) -> mlf.LiveFile:
    f = mlf.LiveFile(name="probe4_phones.csv", headers=["id", "phone", "notes"])
    for identifier, (national, spaced, unbroken) in PHONES_4.items():
        f.add(
            cells={"id": "r", "notes": f"tel {national}"},
            expect=[("notes", identifier, 1, "national, keyword in the cell")],
        )
        f.add(
            cells={"id": "r", "phone": national},
            expect=[("phone", identifier, 1, "national, keyword as the header")],
        )
        f.add(
            cells={"id": "r", "phone": spaced},
            expect=[("phone", identifier, 0, "international with spaces, header")],
        )
        for value in unbroken:
            f.add(
                cells={"id": "r", "notes": f"call {value}"},
                expect=[("notes", identifier, 1, "unbroken, no keyword")],
            )
    #
    # Brazil's rows from the fourth probe, which its job did not run
    #
    br = "BRAZIL_PHONE_NUMBER"
    for cell, n, note in [
        ("call +55 (11) 96123-4567", 0, "a group in parentheses, no keyword"),
        ("call +55 11 96123 4567", 0, "spaces, no keyword"),
        ("phone +55 11 96123 4567", 0, "keyword in the cell, spaces"),
    ]:
        f.add(cells={"id": "r", "notes": cell}, expect=[("notes", br, n, note)])
    return f


FILES_4 = [phones_4]

#
# the sixth live probe (2026-11-17), for #479: how Macie reads a CSV whose
# first line is not the header. The same rows three ways: with a header,
# with none, and after a title line. Two SSNs are found only through the
# ssn header; one is found through its cell's own keyword, whatever the
# header. Our runs, like the stand-ins below, take the first line as the
# header, so without one the header keyword is gone
#
SEED_5 = 20261118


class RawFile:
    """a probe file written line by line as given, for files whose first
    line is not a header. expected rows are physical, 1-based; a column
    is named by the first line's cell, as a run reads it"""

    def __init__(self, *, name: str, lines: list[list[str]]) -> None:
        self.name = name
        self.lines = lines
        self.expected: list[dict] = []

    def expect(self, *, row: int, column: int, identifier: str, count: int, note: str):
        self.expected.append(
            {
                "file": self.name,
                "row": row,
                "column": self.lines[0][column - 1],
                "column_number": column,
                "identifier": identifier,
                "count": count,
                "note": note,
            }
        )

    def write(self, *, directory: str) -> str:
        path = os.path.join(directory, self.name)
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            for line in self.lines:
                w.writerow(line)
        return path


def _header_rows(rng) -> list[list[str]]:
    return [
        ["1", mlf.ssn(rng), ""],
        ["2", mlf.ssn(rng), ""],
        ["3", "", f"ssn {mlf.ssn(rng)}"],
    ]


def headers_5(rng) -> list[RawFile]:
    ssn = "USA_SOCIAL_SECURITY_NUMBER"
    rows = _header_rows(rng)
    normal = RawFile(name="header_normal.csv", lines=[["id", "ssn", "notes"]] + rows)
    normal.expect(row=2, column=2, identifier=ssn, count=1, note="the ssn header")
    normal.expect(row=3, column=2, identifier=ssn, count=1, note="the ssn header")
    normal.expect(row=4, column=3, identifier=ssn, count=1, note="keyword in the cell")
    none = RawFile(name="header_none.csv", lines=list(rows))
    none.expect(row=2, column=2, identifier=ssn, count=0, note="no header: no keyword")
    none.expect(row=3, column=3, identifier=ssn, count=1, note="keyword in the cell")
    title = RawFile(
        name="header_title.csv",
        lines=[["Employee export", "", ""], ["id", "ssn", "notes"]] + rows,
    )
    title.expect(row=3, column=2, identifier=ssn, count=0, note="title as the header")
    title.expect(row=4, column=2, identifier=ssn, count=0, note="title as the header")
    title.expect(row=5, column=3, identifier=ssn, count=1, note="keyword in the cell")
    return [normal, none, title]


FILES_5 = [headers_5]
#
# probe number -> seed, files, directory, expectations file
#
PROBES = {
    1: (SEED, FILES, "probe", "expected_probe.json"),
    2: (SEED_2, FILES_2, "probe2", "expected_probe2.json"),
    3: (SEED_3, FILES_3, "probe3", "expected_probe3.json"),
    4: (SEED_4, FILES_4, "probe4", "expected_probe4.json"),
    5: (SEED_5, FILES_5, "probe5", "expected_probe5.json"),
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
        made = make(rng)
        for f in made if isinstance(made, list) else [made]:
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
