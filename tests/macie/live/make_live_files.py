"""Writes the synthetic data files for the one live check against Amazon
Macie (tests/macie/live/README.md; specs/macie/download-design.md,
Testing). Every value is made up. Values that should be found are built
valid, check digits and all, with the Framework's own checks; near misses
break one rule. Nothing here is real data.

    poetry run python tests/macie/live/make_live_files.py <out dir>

writes <out dir>/data/*.csv (to upload under data/ in the bucket),
<out dir>/macie-config/allow/contractors.txt (the words allow list), and
<out dir>/expected.json, what the Framework's stand-ins are expected to
find, cell by cell. expected.json is not uploaded: labels in the data
would be keywords themselves (CREDIT_CARD_NUMBER holds "card number").

The files are written, not committed: credential-shaped values, even
fake ones, trip GitHub's push protection. They are deterministic (one
seed), so a rerun writes the same files.
"""

import csv
import json
import os
import random
import string
import sys

from csvpath.macie.util.checksum_utility import ChecksumUtility as chut

SEED = 20261109
#
# each file is padded with clean rows to about this size, so the live
# check can also time a run
#
TARGET_BYTES = 200_000
CONTRACTORS = ["EMP-678901", "EMP-456789", "emp-234567"]


class LiveFile:
    """one CSV: its rows, and what is expected of its cells"""

    def __init__(self, *, name: str, headers: list[str]) -> None:
        self.name = name
        self.headers = headers
        self.rows: list[list[str]] = []
        self.expected: list[dict] = []

    def add(self, *, cells: dict, expect: list[tuple] = ()) -> None:
        """expect: (column, identifier, count, note) for this row"""
        unknown = set(cells) - set(self.headers)
        if unknown:
            raise ValueError(f"{self.name} has no columns {sorted(unknown)}")
        self.rows.append([cells.get(h, "") for h in self.headers])
        #
        # Macie numbering: the header is row 1
        #
        row = len(self.rows) + 1
        for column, identifier, count, note in expect:
            self.expected.append(
                {
                    "file": self.name,
                    "row": row,
                    "column": column,
                    "column_number": self.headers.index(column) + 1,
                    "identifier": identifier,
                    "count": count,
                    "note": note,
                }
            )

    def pad(self, *, rng: random.Random, column: str) -> None:
        words = ["routine", "record", "updated", "reviewed", "archived", "filed"]
        while self._size() < TARGET_BYTES:
            text = " ".join(rng.choice(words) for _ in range(6))
            self.rows.append(
                [
                    text if h == column else ("r" if h == "id" else "")
                    for h in self.headers
                ]
            )

    def _size(self) -> int:
        return sum(len(",".join(r)) + 1 for r in self.rows)

    def write(self, *, directory: str) -> str:
        path = os.path.join(directory, self.name)
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(self.headers)
            for i, r in enumerate(self.rows, start=1):
                w.writerow([str(i) if c == "r" else c for c in r])
        return path


#
# values: valid by construction, with the Framework's checks
#


def _digits(rng: random.Random, n: int) -> str:
    return "".join(rng.choice(string.digits) for _ in range(n))


def _check_digit(body: str, ok) -> str:
    """body plus the one trailing digit that makes ok() true"""
    for d in string.digits:
        if ok(body + d):
            return body + d
    raise ValueError(f"no check digit makes {body} valid")


def card(rng, *, valid: bool = True) -> str:
    n = _check_digit("4" + _digits(rng, 14), lambda s: chut.luhn(digits=s))
    if not valid:
        n = n[:-1] + str((int(n[-1]) + 1) % 10)
    return n


def ssn(rng) -> str:
    area = rng.choice([a for a in range(1, 900) if a != 666])
    return f"{area:03d}-{rng.randint(1, 99):02d}-{rng.randint(1, 9999):04d}"


def itin(rng) -> str:
    return (
        f"9{_digits(rng, 2)}-{rng.choice([70, 78, 83, 88, 92, 95])}-{_digits(rng, 4)}"
    )


def iban(rng, *, country: str, bban: str) -> str:
    for check in range(100):
        candidate = f"{country}{check:02d}{bban}"
        if chut.iban_mod97(iban=candidate):
            return candidate
    raise ValueError(f"no IBAN check digits for {country} {bban}")


def nhs(rng) -> str:
    while True:
        body = _digits(rng, 9)
        for d in string.digits:
            if chut.nhs_mod11(digits=body + d):
                return f"{body[:3]} {body[3:6]} {body[6:]}{d}"


def nir(rng) -> str:
    body = "1" + "85" + "11" + "75" + "056" + _digits(rng, 3)
    for key in range(100):
        candidate = f"{body}{key:02d}"
        if chut.fr_nir_key(nir=candidate):
            return candidate
    raise ValueError("no NIR key")


def de_id(rng) -> str:
    letters = "CFGHJKLMNPRTVWXYZ"
    body = rng.choice(letters) + "".join(
        rng.choice(letters + string.digits) for _ in range(8)
    )
    return body + chut.icao_check(text=body)


def dni(rng) -> str:
    number = _digits(rng, 8)
    return number + chut.es_id_letter(number=number)


def nie(rng) -> str:
    number = _digits(rng, 7)
    return "X" + number + chut.es_id_letter(number="0" + number)


def codice_fiscale(rng) -> str:
    body = "RSSMRA85T10A562"
    return body + chut.it_cf_check(code=body)


def cpf(rng) -> str:
    while True:
        body = _digits(rng, 9)
        for a in string.digits:
            for b in string.digits:
                if len(set(body)) > 1 and chut.cpf_mod11(digits=body + a + b):
                    d = body + a + b
                    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


def cnpj(rng) -> str:
    while True:
        body = _digits(rng, 8) + "0001"
        for a in string.digits:
            for b in string.digits:
                if chut.cnpj_mod11(digits=body + a + b):
                    d = body + a + b
                    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"


def rut(rng) -> str:
    body = str(rng.randint(10_000_000, 25_000_000))
    return f"{body[:2]}.{body[2:5]}.{body[5:]}-{chut.rut_check(body=body)}"


def curp(rng) -> str:
    body = "GOMA850510HDFRRN0"
    return body + chut.mx_curp_check(curp=body)


def npi(rng) -> str:
    while True:
        body = "1" + _digits(rng, 8)
        for d in string.digits:
            if chut.luhn(digits="80840" + body + d):
                return body + d


def dea(rng) -> str:
    while True:
        body = _digits(rng, 6)
        for d in string.digits:
            if chut.us_dea(digits=body + d):
                return "AB" + body + d


def mbi(rng) -> str:
    letters = "ACDEFGHJKMNPQRTUVWXY"
    pick = rng.choice
    return (
        str(rng.randint(1, 9))
        + pick(letters)
        + pick(letters + string.digits)
        + pick(string.digits)
        + "-"
        + pick(letters)
        + pick(letters + string.digits)
        + pick(string.digits)
        + "-"
        + pick(letters)
        + pick(letters)
        + pick(string.digits)
        + pick(string.digits)
    )


def b64(rng, n: int, alphabet: str) -> str:
    return "".join(rng.choice(alphabet) for _ in range(n))


#
# the files
#


def employees(rng) -> LiveFile:
    f = LiveFile(name="employees.csv", headers=["id", "name", "employee_id", "notes"])
    cdi = "EmployeeId"
    f.add(
        cells={"id": "r", "name": "Akua Mansa", "employee_id": "EMP-123456"},
        expect=[("employee_id", cdi, 1, "header is a keyword variant")],
    )
    f.add(
        cells={"id": "r", "notes": "employee id: EMP-111111 and EMP-222222"},
        expect=[("notes", cdi, 2, "two occurrences, keyword in the cell")],
    )
    f.add(
        cells={"id": "r", "employee_id": "EMP-678901"},
        expect=[("employee_id", cdi, 0, "on the contractors words allow list")],
    )
    f.add(
        cells={"id": "r", "employee_id": "emp-234567"},
        expect=[("employee_id", cdi, 0, "regex is case sensitive")],
    )
    f.add(
        cells={"id": "r", "employee_id": "EMP-912345"},
        expect=[("employee_id", cdi, 0, "on the training-accounts regex allow list")],
    )
    f.add(
        cells={"id": "r", "employee_id": "EMP-000000"},
        expect=[("employee_id", cdi, 0, "ignore word")],
    )
    f.add(
        cells={"id": "r", "notes": "EMP-345678"},
        expect=[("notes", cdi, 0, "no keyword")],
    )
    f.add(
        cells={"id": "r", "notes": "emp id " + "x" * 60 + " EMP-345679"},
        expect=[("notes", cdi, 0, "keyword further than 50 characters away")],
    )
    f.pad(rng=rng, column="notes")
    return f


def payments(rng) -> LiveFile:
    f = LiveFile(
        name="payments.csv",
        headers=[
            "id",
            "customer",
            "card_number",
            "expiry",
            "cvv",
            "bank_account",
            "notes",
        ],
    )
    f.add(
        cells={"id": "r", "customer": "Mateo Jones", "card_number": card(rng)},
        expect=[
            ("card_number", "CREDIT_CARD_NUMBER", 1, "header keyword"),
            ("card_number", "CREDIT_CARD_NUMBER_(NO_KEYWORD)", 0, "has a keyword"),
        ],
    )
    f.add(
        cells={"id": "r", "notes": f"paid in full {card(rng)}"},
        expect=[
            ("notes", "CREDIT_CARD_NUMBER_(NO_KEYWORD)", 1, "no keyword"),
            ("notes", "CREDIT_CARD_NUMBER", 0, "no keyword"),
        ],
    )
    f.add(
        cells={"id": "r", "card_number": card(rng, valid=False)},
        expect=[("card_number", "CREDIT_CARD_NUMBER", 0, "fails Luhn")],
    )
    grouped = card(rng)
    f.add(
        cells={
            "id": "r",
            "card_number": " ".join(grouped[i : i + 4] for i in range(0, 16, 4)),
        },
        expect=[("card_number", "CREDIT_CARD_NUMBER", 1, "grouped 4-4-4-4 (ours)")],
    )

    f.add(
        cells={"id": "r", "expiry": "02/28"},
        expect=[("expiry", "CREDIT_CARD_EXPIRATION", 1, "header keyword")],
    )
    f.add(
        cells={"id": "r", "cvv": "731"},
        expect=[("cvv", "CREDIT_CARD_SECURITY_CODE", 1, "header keyword")],
    )
    f.add(
        cells={"id": "r", "bank_account": _digits(rng, 12)},
        expect=[
            ("bank_account", "BANK_ACCOUNT_NUMBER", 1, "US or Canada, header keyword")
        ],
    )
    f.add(
        cells={
            "id": "r",
            "notes": iban(rng, country="GB", bban="NWBK" + _digits(rng, 14)),
        },
        expect=[("notes", "UK_BANK_ACCOUNT_NUMBER", 1, "IBAN, no keyword needed")],
    )
    f.add(
        cells={"id": "r", "notes": iban(rng, country="DE", bban=_digits(rng, 18))},
        expect=[("notes", "GERMANY_BANK_ACCOUNT_NUMBER", 1, "IBAN, no keyword needed")],
    )
    f.pad(rng=rng, column="notes")
    return f


def people_us(rng) -> LiveFile:
    f = LiveFile(
        name="people_us.csv",
        headers=[
            "id",
            "name",
            "ssn",
            "phone",
            "dob",
            "passport",
            "drivers_license",
            "address",
            "notes",
        ],
    )
    f.add(
        cells={
            "id": "r",
            "name": "Martha Rivera",
            "ssn": ssn(rng),
            "phone": "(212) 555-0147",
            "dob": "1985-11-05",
            "passport": _digits(rng, 9),
            "drivers_license": "A" + _digits(rng, 7),
            "address": "123 Any Street, Springfield, IL 62701",
        },
        expect=[
            ("ssn", "USA_SOCIAL_SECURITY_NUMBER", 1, "header keyword"),
            ("phone", "PHONE_NUMBER", 1, "header keyword, no country code"),
            ("dob", "DATE_OF_BIRTH", 1, "header keyword"),
            ("passport", "USA_PASSPORT_NUMBER", 1, "header keyword"),
            ("drivers_license", "DRIVERS_LICENSE", 1, "California's format"),
        ],
    )
    f.add(
        cells={"id": "r", "ssn": "000-12-3456"},
        expect=[("ssn", "USA_SOCIAL_SECURITY_NUMBER", 0, "area 000 is never issued")],
    )
    f.add(
        cells={"id": "r", "notes": f"itin {itin(rng)}"},
        expect=[
            (
                "notes",
                "USA_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER",
                1,
                "keyword in the cell",
            )
        ],
    )
    f.add(
        cells={"id": "r", "notes": "call +1 212 555 0148"},
        expect=[("notes", "PHONE_NUMBER", 1, "country code, no keyword needed")],
    )
    f.add(
        cells={"id": "r", "notes": "212 555 0149"},
        expect=[("notes", "PHONE_NUMBER", 0, "no keyword, no country code")],
    )
    f.add(
        cells={
            "id": "r",
            "name": "Wang Xiulan",
            "address": "500 Main Street, Anytown, WA 98101",
        },
        expect=[],
    )
    f.pad(rng=rng, column="notes")
    return f


def people_eu(rng) -> LiveFile:
    f = LiveFile(
        name="people_eu.csv",
        headers=[
            "id",
            "name",
            "nino",
            "nhs",
            "insee",
            "personalausweis",
            "dni",
            "nie",
            "codice_fiscale",
            "notes",
        ],
    )
    f.add(
        cells={
            "id": "r",
            "name": "Arnav Desai",
            "nino": "AB 12 34 56 C",
            "nhs": nhs(rng),
            "insee": nir(rng),
            "personalausweis": de_id(rng),
            "dni": dni(rng),
            "nie": nie(rng),
            "codice_fiscale": codice_fiscale(rng),
        },
        expect=[
            ("nino", "UK_NATIONAL_INSURANCE_NUMBER", 1, "header keyword"),
            ("nhs", "UK_NHS_NUMBER", 1, "header keyword, mod 11"),
            (
                "insee",
                "FRANCE_NATIONAL_IDENTIFICATION_NUMBER",
                1,
                "header keyword, mod 97 key",
            ),
            (
                "personalausweis",
                "GERMANY_NATIONAL_IDENTIFICATION_NUMBER",
                1,
                "ICAO check digit",
            ),
            ("dni", "SPAIN_DNI_NUMBER", 1, "control letter"),
            ("nie", "SPAIN_NIE_NUMBER", 1, "control letter"),
            (
                "codice_fiscale",
                "ITALY_NATIONAL_IDENTIFICATION_NUMBER",
                1,
                "check letter",
            ),
        ],
    )
    f.add(
        cells={"id": "r", "notes": "número de la seguridad social 28/12345678/40"},
        expect=[("notes", "SPAIN_SOCIAL_SECURITY_NUMBER", 1, "format only (ours)")],
    )
    f.add(
        cells={"id": "r", "dni": dni(rng)[:-1] + "Q"},
        expect=[("dni", "SPAIN_DNI_NUMBER", 0, "wrong control letter")],
    )
    f.pad(rng=rng, column="notes")
    return f


def latam_health(rng) -> LiveFile:
    f = LiveFile(
        name="latam_health.csv",
        headers=["id", "cpf", "cnpj", "rut", "curp", "npi", "mbi", "dea_number", "ndc"],
    )
    f.add(
        cells={
            "id": "r",
            "cpf": cpf(rng),
            "cnpj": cnpj(rng),
            "rut": rut(rng),
            "curp": curp(rng),
            "npi": npi(rng),
            "mbi": mbi(rng),
            "dea_number": dea(rng),
            "ndc": "0002-1433-80",
        },
        expect=[
            ("cpf", "BRAZIL_CPF_NUMBER", 1, "check digits"),
            ("cnpj", "BRAZIL_CNPJ_NUMBER", 1, "check digits"),
            ("rut", "CHILE_RUT_NUMBER", 1, "check character"),
            ("curp", "MEXICO_CURP_NUMBER", 1, "check digit"),
            ("npi", "USA_NATIONAL_PROVIDER_IDENTIFIER", 1, "Luhn over 80840"),
            (
                "mbi",
                "USA_MEDICARE_BENEFICIARY_IDENTIFIER",
                1,
                "CMS format, with dashes",
            ),
            ("dea_number", "US_DRUG_ENFORCEMENT_AGENCY_NUMBER", 1, "check digit"),
            ("ndc", "USA_NATIONAL_DRUG_CODE", 1, "4-4-2"),
        ],
    )
    f.add(
        cells={"id": "r", "cpf": "111.111.111-11"},
        expect=[("cpf", "BRAZIL_CPF_NUMBER", 0, "repeated digits")],
    )
    f.pad(rng=rng, column="ndc")
    return f


def credentials(rng) -> LiveFile:
    f = LiveFile(name="credentials.csv", headers=["id", "kind", "value"])
    b64chars = string.ascii_letters + string.digits + "+/"
    #
    # built from parts at run time; see the module docstring
    #
    secret = b64(rng, 40, b64chars)
    f.add(
        cells={
            "id": "r",
            "kind": "cloud",
            "value": f"aws_secret_access_key = {secret}",
        },
        expect=[("value", "AWS_CREDENTIALS", 1, "keyword in the cell")],
    )
    token = "dXNlcjp" + b64(rng, 13, string.ascii_letters + string.digits) + "=="
    f.add(
        cells={"id": "r", "kind": "web", "value": f"Authorization: Basic {token}"},
        expect=[("value", "HTTP_BASIC_AUTH_HEADER", 1, "complete header")],
    )
    f.add(
        cells={"id": "r", "kind": "cloud", "value": "aws_secret_access_key = changeme"},
        expect=[("value", "AWS_CREDENTIALS", 0, "not 40 characters")],
    )
    f.pad(rng=rng, column="kind")
    return f


def clean(rng) -> LiveFile:
    f = LiveFile(name="clean.csv", headers=["id", "item", "notes"])
    f.add(cells={"id": "r", "item": "widget", "notes": "nothing sensitive here"})
    f.pad(rng=rng, column="notes")
    return f


FILES = [employees, payments, people_us, people_eu, latam_health, credentials, clean]


def write_all(*, out: str) -> dict:
    if not isinstance(out, str) or out.strip() == "":
        raise ValueError("out must be a directory path")
    rng = random.Random(SEED)
    data = os.path.join(out, "data")
    config = os.path.join(out, "macie-config", "allow")
    os.makedirs(data, exist_ok=True)
    os.makedirs(config, exist_ok=True)
    expected = []
    for make in FILES:
        f = make(rng)
        f.write(directory=data)
        expected.extend(f.expected)
    with open(os.path.join(config, "contractors.txt"), "w", encoding="utf-8") as fh:
        fh.write("".join(f"{c}\n" for c in CONTRACTORS))
    doc = {"seed": SEED, "contractors": CONTRACTORS, "expected": expected}
    with open(os.path.join(out, "expected.json"), "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
        fh.write("\n")
    return doc


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stderr.write("usage: make_live_files.py <out dir>\n")
        sys.exit(2)
    result = write_all(out=sys.argv[1])
    sys.stdout.write(
        f"wrote {len(FILES)} data files and {len(result['expected'])} expectations to {sys.argv[1]}\n"
    )
