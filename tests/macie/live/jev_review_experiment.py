"""The Jev review experiment (specs/macie/jev-review-design.md): can Jev,
given only masked context, tell real findings from false ones?

Every case is a column of findings as our stand-ins would report it,
labelled with the truth. Values never go to Jev: each letter becomes A
and each digit #, spaces and punctuation stay. The cases are synthetic.

    poetry run python tests/macie/live/jev_review_experiment.py plan <out dir>
    JEV_KEY=... poetry run python tests/macie/live/jev_review_experiment.py send <out dir> [--pilot]

plan writes the requests to <out dir>/requests.json and prints what would
be sent; nothing leaves the machine. send sends them (--pilot: only the
first request, cut to PILOT_QUESTIONS questions, to measure cost first)
and writes <out dir>/results.json and a summary. Run send only with
David's OK: Jev is billed per call.
"""

import json
import os
import random
import string
import sys
import time

#
# questions per request. The design note asks for one batched request per
# file; here a request stands in for a file
#
BATCH = 10
PILOT_QUESTIONS = 3
#
# the subset also asked as a choice(), to compare with noul()
#
CHOICE_CASES = 10

STATE = """\
A data-loss-prevention scan of CSV files flagged values that may be
sensitive personal or financial data. You are reviewing the flags.
Values are masked: in every word that holds a digit, each letter is A
and each digit is #, with punctuation kept, so you see each value's
shape, never the value. Other words are shown as written.
For each flagged column you are told the file, the column and its
neighbouring columns, facts about the column's values, why the scan
flagged them, and masked samples of the cell text."""

CHOICES = {
    "likely": "the flagged values are very probably real sensitive data of the kind named",
    "doubtful": "the flagged values are probably not that kind of sensitive data",
    "unrelated": "the flag is clearly a false alarm, e.g. ids, codes, or placeholders",
}


def mask(text: str) -> str:
    """each letter becomes A, each digit #; everything else is kept"""
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, not {type(text)}")
    return "".join("A" if c.isalpha() else "#" if c.isdigit() else c for c in text)


def mask_cell(text: str) -> str:
    """the words around a value are kept, so Jev sees the context; every
    token holding a digit, which is where the values are, is masked. A
    letters-only value (a name) would be sent as is: see the design
    note's open questions"""
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, not {type(text)}")
    return " ".join(
        mask(t) if any(c.isdigit() for c in t) else t for t in text.split(" ")
    )


def _fake_secret(*, seed: int) -> str:
    """40 characters shaped like an AWS secret key, built at run time:
    credential-shaped values, even fake ones, trip GitHub's push
    protection when committed"""
    rng = random.Random(seed)
    return "".join(rng.choice(string.ascii_letters + string.digits) for _ in range(40))


def _case(
    *,
    cid: str,
    label: str,
    identifier: str,
    meaning: str,
    file: str,
    columns: list[str],
    column: str,
    rows: int,
    found: int,
    distinct: int,
    why: str,
    samples: list[str],
    sequential: bool = False,
) -> dict:
    if label not in ("real", "false", "ambiguous"):
        raise ValueError(f"bad label {label!r}")
    if column not in columns:
        raise ValueError(f"{cid}: {column} is not one of its columns")
    return {
        "id": cid,
        "label": label,
        "identifier": identifier,
        "meaning": meaning,
        "file": file,
        "columns": columns,
        "column": column,
        "rows": rows,
        "found": found,
        "distinct": distinct,
        "why": why,
        "samples": samples,
        "sequential": sequential,
    }


#
# the samples are written as plain synthetic text and masked when the
# question is built, so a reader of this file sees what the mask hides
#
CASES = [
    #
    # real: the shape, the column and the context agree
    #
    _case(
        cid="ssn-hr",
        label="real",
        identifier="USA_SOCIAL_SECURITY_NUMBER",
        meaning="a US Social Security number",
        file="employees.csv",
        columns=["employee_id", "name", "ssn", "dob", "hire_date"],
        column="ssn",
        rows=850,
        found=850,
        distinct=850,
        why="the column header is the keyword ssn",
        samples=["309-04-7794", "166-46-2907", "716-90-7411"],
    ),
    _case(
        cid="ssn-note",
        label="real",
        identifier="USA_SOCIAL_SECURITY_NUMBER",
        meaning="a US Social Security number",
        file="claims.csv",
        columns=["claim_id", "member", "notes"],
        column="notes",
        rows=3000,
        found=41,
        distinct=41,
        why="the keyword ssn is in the cell",
        samples=[
            "member ssn 644-25-1556 confirmed by phone",
            "ssn on file: 721-99-9913",
        ],
    ),
    _case(
        cid="card-pay",
        label="real",
        identifier="CREDIT_CARD_NUMBER",
        meaning="a payment card number (it passed the Luhn check)",
        file="payments.csv",
        columns=["payment_id", "card_number", "expiry", "cvv", "amount"],
        column="card_number",
        rows=1200,
        found=1200,
        distinct=1187,
        why="the column header holds the keyword card",
        samples=["4532015112830366", "5425233430109903", "4916338506082832"],
    ),
    _case(
        cid="iban-note",
        label="real",
        identifier="UK_BANK_ACCOUNT_NUMBER",
        meaning="a UK bank account as an IBAN (it passed mod 97)",
        file="suppliers.csv",
        columns=["supplier", "contact", "notes"],
        column="notes",
        rows=400,
        found=37,
        distinct=37,
        why="an IBAN needs no keyword",
        samples=[
            "pay to GB82 WEST 1234 5698 7654 32 net 30",
            "remit GB33BUKB20201555555555",
        ],
    ),
    _case(
        cid="dob-patients",
        label="real",
        identifier="DATE_OF_BIRTH",
        meaning="a person's date of birth",
        file="patients.csv",
        columns=["mrn", "name", "dob", "sex", "postcode"],
        column="dob",
        rows=2200,
        found=2200,
        distinct=1980,
        why="the column header is the keyword dob",
        samples=["1985-11-05", "1952-03-17", "2001-07-29"],
    ),
    _case(
        cid="phone-contacts",
        label="real",
        identifier="PHONE_NUMBER",
        meaning="a US or Canadian phone number",
        file="contacts.csv",
        columns=["contact_id", "name", "phone", "email", "city"],
        column="phone",
        rows=640,
        found=640,
        distinct=633,
        why="the column header is the keyword phone",
        samples=["(212) 555-0147", "415-555-0199", "+1 (617) 555-0123"],
    ),
    _case(
        cid="passport-travel",
        label="real",
        identifier="USA_PASSPORT_NUMBER",
        meaning="a US passport number",
        file="travellers.csv",
        columns=[
            "booking",
            "surname",
            "given_names",
            "passport",
            "nationality",
            "expiry",
        ],
        column="passport",
        rows=300,
        found=212,
        distinct=212,
        why="the column header is the keyword passport",
        samples=["561930284", "A04815326", "487126993"],
    ),
    _case(
        cid="cpf-br",
        label="real",
        identifier="BRAZIL_CPF_NUMBER",
        meaning="a Brazilian CPF taxpayer number (check digits valid)",
        file="clientes.csv",
        columns=["cliente", "nome", "cpf", "telefone", "cidade"],
        column="cpf",
        rows=900,
        found=900,
        distinct=900,
        why="the column header is the keyword cpf",
        samples=["390.533.447-05", "111.444.777-35", "529.982.247-25"],
    ),
    _case(
        cid="nhs-patients",
        label="real",
        identifier="UK_NHS_NUMBER",
        meaning="a UK NHS number (mod 11 valid)",
        file="gp_patients.csv",
        columns=["patient", "nhs", "surgery", "registered"],
        column="nhs",
        rows=1500,
        found=1500,
        distinct=1500,
        why="the column header is the keyword nhs",
        samples=["943 476 5919", "401 023 2137", "485 777 3456"],
    ),
    _case(
        cid="cf-payroll",
        label="real",
        identifier="ITALY_NATIONAL_IDENTIFICATION_NUMBER",
        meaning="an Italian Codice Fiscale (check letter valid)",
        file="buste_paga.csv",
        columns=["matricola", "cognome", "nome", "note"],
        column="note",
        rows=500,
        found=500,
        distinct=500,
        why="the keyword tax code is in the cell",
        samples=["tax code RSSMRA85T10A562S", "tax code BNCLRA70A41H501B"],
    ),
    _case(
        cid="aws-config",
        label="real",
        identifier="AWS_CREDENTIALS",
        meaning="an AWS secret access key",
        file="deploy_settings.csv",
        columns=["env", "setting", "value"],
        column="value",
        rows=60,
        found=3,
        distinct=3,
        why="the keyword aws_secret_access_key is in the cell",
        samples=[f"aws_secret_access_key = {_fake_secret(seed=1)}"],
    ),
    _case(
        cid="npi-providers",
        label="real",
        identifier="USA_NATIONAL_PROVIDER_IDENTIFIER",
        meaning="a US National Provider Identifier (Luhn valid)",
        file="providers.csv",
        columns=["provider", "specialty", "npi", "state"],
        column="npi",
        rows=700,
        found=700,
        distinct=700,
        why="the column header is the keyword npi",
        samples=["1234567893", "1245319599", "1679576722"],
    ),
    _case(
        cid="dni-es",
        label="real",
        identifier="SPAIN_DNI_NUMBER",
        meaning="a Spanish DNI (control letter valid)",
        file="empleados.csv",
        columns=["empleado", "nombre", "dni", "puesto"],
        column="dni",
        rows=320,
        found=320,
        distinct=320,
        why="the column header is the keyword dni",
        samples=["12345678Z", "87654321X", "45678912W"],
    ),
    _case(
        cid="dl-hr",
        label="real",
        identifier="DRIVERS_LICENSE",
        meaning="a US driver's license number",
        file="drivers.csv",
        columns=["driver_id", "name", "drivers_license", "state", "class"],
        column="drivers_license",
        rows=180,
        found=180,
        distinct=180,
        why="the column header is the keyword drivers license",
        samples=["A1234567", "D7654321", "B9988776"],
    ),
    #
    # false: the shape fits and a keyword is there, but the column is not
    # what the identifier means
    #
    _case(
        cid="ssn-ticket",
        label="false",
        identifier="USA_SOCIAL_SECURITY_NUMBER",
        meaning="a US Social Security number",
        file="support_tickets.csv",
        columns=["ticket", "opened", "status", "notes"],
        column="notes",
        rows=5000,
        found=26,
        distinct=26,
        why="the keyword ssn is in the cell",
        samples=[
            "ssn not provided by caller; see ticket 482-11-3907",
            "asked for ssn, refused. merged into case 301-56-7720",
        ],
    ),
    _case(
        cid="ssn-placeholder",
        label="false",
        identifier="USA_SOCIAL_SECURITY_NUMBER",
        meaning="a US Social Security number",
        file="test_accounts.csv",
        columns=["account", "ssn", "plan", "created"],
        column="ssn",
        rows=400,
        found=400,
        distinct=1,
        why="the column header is the keyword ssn",
        samples=["123-45-6789", "123-45-6789", "123-45-6789"],
    ),
    _case(
        cid="card-tracking",
        label="false",
        identifier="CREDIT_CARD_NUMBER",
        meaning="a payment card number (it passed the Luhn check)",
        file="shipments.csv",
        columns=["order", "carrier", "notes"],
        column="notes",
        rows=8000,
        found=74,
        distinct=74,
        why="the keyword card is in the cell",
        samples=[
            "gift card shipment, tracking 4417123456789113",
            "card stock reorder, tracking 4024007198964305",
        ],
    ),
    _case(
        cid="card-library",
        label="false",
        identifier="CREDIT_CARD_NUMBER",
        meaning="a payment card number (it passed the Luhn check)",
        file="library_members.csv",
        columns=["member", "branch", "library_card", "joined"],
        column="library_card",
        rows=2600,
        found=260,
        distinct=260,
        why="the column header holds the keyword card (library_card)",
        samples=["2913400012345671", "2913400098765435"],
    ),
    _case(
        cid="phone-sku",
        label="false",
        identifier="PHONE_NUMBER",
        meaning="a US or Canadian phone number",
        file="product_catalog.csv",
        columns=["sku", "phone", "case_color", "price", "stock"],
        column="phone",
        rows=1400,
        found=1400,
        distinct=9,
        why="the column header is the keyword phone",
        samples=["415-555-0100", "212-555-0100", "415-555-0100"],
    ),
    _case(
        cid="passport-photo",
        label="false",
        identifier="USA_PASSPORT_NUMBER",
        meaning="a US passport number",
        file="photo_orders.csv",
        columns=["order", "product", "passport_photo_id", "size", "price"],
        column="passport_photo_id",
        rows=900,
        found=900,
        distinct=900,
        why="the column header holds the keyword passport (passport_photo_id)",
        samples=["100234871", "100234872", "100234873"],
        sequential=True,
    ),
    _case(
        cid="nhs-supplier",
        label="false",
        identifier="UK_NHS_NUMBER",
        meaning="a UK NHS number (mod 11 valid)",
        file="trust_procurement.csv",
        columns=["po", "nhs_supplier_code", "item", "qty", "unit_cost"],
        column="nhs_supplier_code",
        rows=3100,
        found=290,
        distinct=14,
        why="the column header holds the keyword nhs (nhs_supplier_code)",
        samples=["400 000 0018", "400 000 0026", "400 000 0018"],
    ),
    _case(
        cid="dl-download",
        label="false",
        identifier="DRIVERS_LICENSE",
        meaning="a US driver's license number",
        file="cdn_logs.csv",
        columns=["ts", "path", "bytes", "notes"],
        column="notes",
        rows=20000,
        found=310,
        distinct=12,
        why="the keyword dl# is in the cell",
        samples=["dl# A1000001 resumed", "dl# A1000002 failed checksum"],
        sequential=True,
    ),
    _case(
        cid="bank-crm",
        label="false",
        identifier="BANK_ACCOUNT_NUMBER",
        meaning="a US or Canadian bank account number",
        file="crm_export.csv",
        columns=["company", "owner", "notes"],
        column="notes",
        rows=6000,
        found=88,
        distinct=88,
        why="the keyword account is in the cell",
        samples=[
            "account 10293847 moved to enterprise tier",
            "account 55667788 renewal call",
        ],
    ),
    _case(
        cid="aws-docs",
        label="false",
        identifier="AWS_CREDENTIALS",
        meaning="an AWS secret access key",
        file="kb_articles.csv",
        columns=["article", "title", "body_excerpt"],
        column="body_excerpt",
        rows=1200,
        found=4,
        distinct=1,
        why="the keyword aws_secret_access_key is in the cell",
        samples=[
            "example from the AWS docs: aws_secret_access_key = "
            f"{_fake_secret(seed=2)[:30]}EXAMPLEKEY"
        ],
    ),
    _case(
        cid="cpf-invoice",
        label="false",
        identifier="BRAZIL_CPF_NUMBER",
        meaning="a Brazilian CPF taxpayer number (check digits valid)",
        file="notas_fiscais.csv",
        columns=["nota", "emitente", "obs"],
        column="obs",
        rows=9000,
        found=31,
        distinct=31,
        why="the keyword cpf is in the cell",
        samples=[
            "cpf do emitente ausente; nota 111.222.333-96",
            "cpf pendente, pedido 222.333.444-05",
        ],
    ),
    _case(
        cid="dob-flags",
        label="false",
        identifier="DATE_OF_BIRTH",
        meaning="a person's date of birth",
        file="form_config.csv",
        columns=["field", "dob", "required", "default"],
        column="dob",
        rows=40,
        found=40,
        distinct=1,
        why="the column header is the keyword dob",
        samples=["1900-01-01", "1900-01-01", "1900-01-01"],
    ),
    #
    # ambiguous: sensitive or not depends on policy, not on the data; not
    # scored, reported to see what Jev does with them
    #
    _case(
        cid="dob-dogs",
        label="ambiguous",
        identifier="DATE_OF_BIRTH",
        meaning="a person's date of birth",
        file="kennel_club_entries.csv",
        columns=["entry", "dog_name", "breed", "dob", "owner_postcode"],
        column="dob",
        rows=1100,
        found=1100,
        distinct=870,
        why="the column header is the keyword dob",
        samples=["2019-04-12", "2021-09-30", "2018-01-05"],
    ),
    _case(
        cid="phone-vendors",
        label="ambiguous",
        identifier="PHONE_NUMBER",
        meaning="a US or Canadian phone number",
        file="vendors.csv",
        columns=["vendor", "support_phone", "website", "terms"],
        column="support_phone",
        rows=210,
        found=210,
        distinct=205,
        why="the column header holds the keyword phone",
        samples=["+1 (800) 555-0142", "+1 (888) 555-0177"],
    ),
    _case(
        cid="ssn-masked",
        label="ambiguous",
        identifier="USA_SOCIAL_SECURITY_NUMBER",
        meaning="a US Social Security number",
        file="statements.csv",
        columns=["statement", "member", "ssn_last4_note"],
        column="ssn_last4_note",
        rows=4000,
        found=4000,
        distinct=3950,
        why="the column header holds the keyword ssn",
        samples=["ssn ending 7794, full 309-04-7794 on request"],
    ),
]


#
# the second run (2026-11-15): four cases with little context, asked only
# then, so the first run's requests stay as they were sent
#
EXTRA_CASES = [
    _case(
        cid="ssn-bare",
        label="real",
        identifier="USA_SOCIAL_SECURITY_NUMBER",
        meaning="a US Social Security number",
        file="export.csv",
        columns=["col1", "ssn", "col3"],
        column="ssn",
        rows=120,
        found=120,
        distinct=120,
        why="the column header is the keyword ssn",
        samples=["412-56-7788", "530-21-0094", "288-73-6105"],
    ),
    _case(
        cid="iban-payroll",
        label="real",
        identifier="GERMANY_BANK_ACCOUNT_NUMBER",
        meaning="a German bank account as an IBAN (it passed mod 97)",
        file="payroll_eu.csv",
        columns=["employee", "iban", "bic", "net_pay"],
        column="iban",
        rows=260,
        found=260,
        distinct=260,
        why="an IBAN needs no keyword",
        samples=["DE89370400440532013000", "DE02120300000000202051"],
    ),
    _case(
        cid="ssn-testdata",
        label="false",
        identifier="USA_SOCIAL_SECURITY_NUMBER",
        meaning="a US Social Security number",
        file="export.csv",
        columns=["col1", "ssn", "col3"],
        column="ssn",
        rows=5000,
        found=5000,
        distinct=3,
        why="the column header is the keyword ssn",
        samples=["111-22-3333", "222-33-4444", "111-22-3333"],
    ),
    _case(
        cid="card-game",
        label="false",
        identifier="CREDIT_CARD_NUMBER",
        meaning="a payment card number (it passed the Luhn check)",
        file="game_events.csv",
        columns=["player", "deck", "card", "turn"],
        column="card",
        rows=40000,
        found=3900,
        distinct=52,
        why="the column header is the keyword card",
        samples=["4000000000000002", "4000000000000010"],
    ),
]


def column_facts(case: dict) -> list[str]:
    """what our own code can say exactly about the flagged values, in plain
    words: Jev did not weigh the bare counts in the first run"""
    found, distinct = case["found"], case["distinct"]
    facts = []
    if found > 1 and distinct == 1:
        facts.append(f"Every one of the {found} flagged values is the same value.")
    elif found > 1 and distinct / found <= 0.05:
        facts.append(
            f"Only {distinct} distinct values among {found} flagged cells: "
            "the same few values repeat."
        )
    elif found > 1 and distinct == found:
        facts.append("Every flagged value is different.")
    if case["sequential"]:
        facts.append(
            "The flagged values are consecutive: each is the one before plus one."
        )
    return facts


def question(case: dict, *, run: int = 1) -> str:
    samples = "\n".join(f'  "{mask_cell(s)}"' for s in case["samples"])
    facts = ""
    if run == 2:
        lines = column_facts(case)
        if lines:
            facts = "Facts the scan computed about the flagged values:\n" + "".join(
                f"  - {line}\n" for line in lines
            )
    return (
        f"Identifier: {case['identifier']} ({case['meaning']}).\n"
        f"File: {case['file']}. Columns: {', '.join(case['columns'])}.\n"
        f"Flagged column: {case['column']}.\n"
        f"Flagged in {case['found']} of {case['rows']} rows; "
        f"{case['distinct']} distinct flagged values.\n"
        f"{facts}"
        f"Why the scan flagged them: {case['why']}.\n"
        f"Masked samples of flagged cells:\n{samples}\n"
        f"Is it likely that the flagged values in the {case['column']} "
        f"column are real: {case['meaning']}?"
    )


def cases(*, run: int = 1) -> list[dict]:
    if run not in (1, 2):
        raise ValueError(f"run must be 1 or 2, not {run!r}")
    return CASES if run == 1 else CASES + EXTRA_CASES


def requests(*, run: int = 1) -> list[dict]:
    """the noul() requests in batches, then the choice() requests: in the
    first run, the first CHOICE_CASES cases (all real, an oversight); in
    the second, every case"""
    asked = cases(run=run)
    out = []
    for i in range(0, len(asked), BATCH):
        batch = asked[i : i + BATCH]
        out.append(
            {
                "kind": "noul",
                "questions": {c["id"]: question(c, run=run) for c in batch},
            }
        )
    chosen = asked[:CHOICE_CASES] if run == 1 else asked
    for i in range(0, len(chosen), BATCH if run == 2 else CHOICE_CASES):
        batch = chosen[i : i + (BATCH if run == 2 else CHOICE_CASES)]
        out.append(
            {
                "kind": "choice",
                "questions": {c["id"]: question(c, run=run) for c in batch},
            }
        )
    return out


def plan(*, out: str, run: int = 1) -> list[dict]:
    if not isinstance(out, str) or out.strip() == "":
        raise ValueError("out must be a directory path")
    os.makedirs(out, exist_ok=True)
    reqs = requests(run=run)
    with open(os.path.join(out, "requests.json"), "w", encoding="utf-8") as f:
        json.dump({"state": STATE, "choices": CHOICES, "requests": reqs}, f, indent=2)
    return reqs


def send(*, out: str, pilot: bool, run: int = 1) -> dict:
    from typesafe_sdk import TypeSafeClient
    from typesafe_sdk._core.question_types import Choice, Noul

    key = os.environ.get("JEV_KEY")
    if not key:
        raise ValueError("JEV_KEY is not set")
    reqs = plan(out=out, run=run)
    if pilot:
        first = reqs[0]
        keep = list(first["questions"])[:PILOT_QUESTIONS]
        reqs = [{"kind": "noul", "questions": {k: first["questions"][k] for k in keep}}]
    results = {"pilot": pilot, "run": run, "requests": []}
    with TypeSafeClient(model="jev-latest", api_key=key) as client:
        for r in reqs:
            if r["kind"] == "noul":
                qs = {k: Noul(instructions=v) for k, v in r["questions"].items()}
            else:
                qs = {
                    k: Choice(instructions=v, criteria=CHOICES)
                    for k, v in r["questions"].items()
                }
            started = time.perf_counter()
            response = client.system_one(state=STATE, questions=qs)
            seconds = time.perf_counter() - started
            results["requests"].append(
                {
                    "kind": r["kind"],
                    "model": response.model,
                    "seconds": round(seconds, 2),
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "answers": {k: a.model_dump() for k, a in response.answers.items()},
                }
            )
    results["summary"] = summarize(results=results)
    with open(os.path.join(out, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    return results


def _auc(*, scored: list[tuple[float, str]]) -> float | None:
    """the chance a real case scores above a false one"""
    real = [p for p, label in scored if label == "real"]
    false = [p for p, label in scored if label == "false"]
    pairs = [(r, f) for r in real for f in false]
    if not pairs:
        return None
    return round(
        sum(1.0 if r > f else 0.5 if r == f else 0.0 for r, f in pairs) / len(pairs),
        3,
    )


def _band(p: float) -> str:
    #
    # the design note's three bands
    #
    return "likely" if p >= 0.7 else "doubtful" if p <= 0.3 else "uncertain"


def summarize(*, results: dict) -> dict:
    labels = {c["id"]: c["label"] for c in CASES + EXTRA_CASES}
    noul, choice = {}, {}
    for r in results["requests"]:
        for k, a in r["answers"].items():
            if r["kind"] == "noul":
                noul[k] = a["noul"]
            else:
                choice[k] = (a["choice"], a["probabilities"].get("likely", 0.0))
    scored = [(noul[k], labels[k]) for k in noul if labels[k] != "ambiguous"]
    real = [p for p, label in scored if label == "real"]
    false = [p for p, label in scored if label == "false"]
    wrong_band = [
        k
        for k in noul
        if labels[k] != "ambiguous"
        and _band(noul[k]) != "uncertain"
        and (_band(noul[k]) == "likely") != (labels[k] == "real")
    ]
    committed = [
        k for k in noul if labels[k] != "ambiguous" and _band(noul[k]) != "uncertain"
    ]
    summary = {
        "questions": sum(len(r["answers"]) for r in results["requests"]),
        "input_tokens": sum(r["input_tokens"] or 0 for r in results["requests"]),
        "output_tokens": sum(r["output_tokens"] or 0 for r in results["requests"]),
        "seconds": round(sum(r["seconds"] for r in results["requests"]), 2),
        "mean_real": round(sum(real) / len(real), 3) if real else None,
        "mean_false": round(sum(false) / len(false), 3) if false else None,
        "correct_at_0_5": sum(
            1 for p, label in scored if (p >= 0.5) == (label == "real")
        ),
        "scored": len(scored),
        "auc": _auc(scored=scored),
        "committed": len(committed),
        "wrong_band": wrong_band,
        "per_case": {k: (labels[k], round(v, 3)) for k, v in noul.items()},
    }
    if choice:
        cscored = [
            (choice[k][1], labels[k]) for k in choice if labels[k] != "ambiguous"
        ]
        summary["choice_auc"] = _auc(scored=cscored)
        summary["choice_correct"] = sum(
            1
            for k in choice
            if labels[k] != "ambiguous"
            and (choice[k][0] == "likely") == (labels[k] == "real")
        )
        summary["choice_scored"] = len(cscored)
        summary["choice_per_case"] = {
            k: (labels[k], c, round(p, 3)) for k, (c, p) in choice.items()
        }
    return summary


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("plan", "send"):
        sys.stderr.write(
            "usage: jev_review_experiment.py plan|send <out dir> [--pilot] [--run 2]\n"
        )
        sys.exit(2)
    run = 2 if "--run" in sys.argv[3:] and "2" in sys.argv[3:] else 1
    if sys.argv[1] == "plan":
        reqs = plan(out=sys.argv[2], run=run)
        n = sum(len(r["questions"]) for r in reqs)
        sys.stdout.write(
            f"run {run}: {len(cases(run=run))} cases; {len(reqs)} requests, "
            f"{n} questions; written to {sys.argv[2]}/requests.json\n"
        )
    else:
        result = send(out=sys.argv[2], pilot="--pilot" in sys.argv[3:], run=run)
        sys.stdout.write(json.dumps(result["summary"], indent=2) + "\n")
