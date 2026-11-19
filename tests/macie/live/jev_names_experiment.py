"""The NAME and ADDRESS experiment (specs/macie/jev-names-addresses-
design.md): can Jev tell, from a column's masked shapes, its header and
its neighbours, whether it holds people's full names or postal
addresses?

Every case is a synthetic column, labelled with the truth. Values never
go to Jev: the case-keeping mask makes each upper-case letter A, each
lower-case letter a and each digit #, with spaces and punctuation kept,
so only shapes leave the machine. Each column is asked about both NAME
and ADDRESS, so a names column is also a look-alike for ADDRESS.

    poetry run python tests/macie/live/jev_names_experiment.py plan <out dir>
    JEV_KEY=... poetry run python tests/macie/live/jev_names_experiment.py send <out dir>

plan writes the requests to <out dir>/requests.json and prints what
would be sent; nothing leaves the machine. send sends them and writes
<out dir>/results.json and a summary. Run send only with David's OK:
Jev is billed per call.
"""

import collections
import json
import os
import random
import sys
import time

MODEL = "jev-1.14.0"
BATCH = 10
ROWS = 200
SEED = 20261118
TOP_SHAPES = 6

STATE = """\
A data-loss-prevention scan is checking CSV columns for personal data.
Values are masked: each upper-case letter is A, each lower-case letter
is a, each digit is #; spaces and punctuation are kept. You see each
column's shapes, never its values. For each column you are told the
file, the column and its neighbouring columns, how many rows are filled
and distinct, and the most common shapes with their counts."""

CHOICES = {
    "likely": "the column very probably holds the kind of personal data named",
    "doubtful": "the column probably does not hold that kind of personal data",
    "unrelated": "the column clearly holds something else",
}

IDENTIFIERS = {
    "NAME": (
        "a person's full name: a given name and a family name",
        "Does this column hold people's full names?",
    ),
    "ADDRESS": (
        "a postal address that includes a city or place and its postal code",
        "Does this column hold postal addresses?",
    ),
}

FIRST = """Akua Omar Sara Ken Ola Mia Tom Li Ana John Martha Priya Lucas Elena
Mateo Chloe Noah Fatima Hiro Ingrid Diego Amara Yusuf Lena Marco Zoe Ravi
Nadia Felix Grace""".split()
LAST = """Mansa Haddad Lund Ito Berg Chen Ruiz Wei Silva Doe Rivera Patel
Moreau Rossi Garcia Martin Novak Okafor Tanaka Larsen Costa Kowalski
Nguyen Schmidt Fischer Dubois Murphy Kim Singh Jones""".split()
STREETS = """Main Elm Oak Maple Cedar Pine Lake Hill Park River""".split()
CITIES_US = [
    ("Springfield", "IL", "62704"),
    ("Portland", "OR", "97205"),
    ("Austin", "TX", "78701"),
    ("Denver", "CO", "80202"),
]


def mask(text: str) -> str:
    """the case-keeping mask: A upper, a lower, # digit"""
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, not {type(text)}")
    return "".join(
        "A"
        if c.isalpha() and c.isupper()
        else "a"
        if c.isalpha()
        else "#"
        if c.isdigit()
        else c
        for c in text
    )


def _d(rng, n: int) -> str:
    return "".join(rng.choice("0123456789") for _ in range(n))


def _full(rng) -> str:
    return f"{rng.choice(FIRST)} {rng.choice(LAST)}"


def _us_address(rng) -> str:
    city, state, zip_ = rng.choice(CITIES_US)
    return f"{rng.randint(1, 9999)} {rng.choice(STREETS)} St, {city}, {state} {zip_}"


#
# (id, file, column, neighbours, truth, value maker). truth is the
# identifier the column truly holds, None, or "ambiguous"
#
CASES = [
    (
        "full_name",
        "customers.csv",
        "full_name",
        ["id", "full_name", "email", "signup_date"],
        "NAME",
        _full,
    ),
    (
        "last_first",
        "members.csv",
        "member",
        ["member_id", "member", "tier", "joined"],
        "NAME",
        lambda r: f"{r.choice(LAST)}, {r.choice(FIRST)}",
    ),
    (
        "middle_initial",
        "staff.csv",
        "contact_name",
        ["staff_id", "contact_name", "extension"],
        "NAME",
        lambda r: (
            f"{r.choice(FIRST)} {r.choice('ABCDEFGHJKLMNPRST')}. {r.choice(LAST)}"
        ),
    ),
    (
        "titled",
        "patients.csv",
        "physician",
        ["patient_id", "physician", "visit_date"],
        "NAME",
        lambda r: f"Dr. {_full(r)}",
    ),
    (
        "upper_names",
        "claims.csv",
        "claimant",
        ["claim_no", "claimant", "amount"],
        "NAME",
        lambda r: _full(r).upper(),
    ),
    (
        "hyphen_names",
        "hr.csv",
        "employee",
        ["emp_no", "employee", "dept"],
        "NAME",
        lambda r: (
            f"{r.choice(FIRST)} {r.choice(['O', 'Mac'])}'{r.choice(LAST)}"
            if r.random() < 0.3
            else f"{r.choice(FIRST)} {r.choice(LAST)}-{r.choice(LAST)}"
        ),
    ),
    (
        "vague_header",
        "export.csv",
        "field_3",
        ["field_1", "field_2", "field_3", "field_4"],
        "NAME",
        _full,
    ),
    (
        "product_name",
        "catalog.csv",
        "product_name",
        ["sku", "product_name", "price"],
        None,
        lambda r: (
            f"{r.choice(['Blue', 'Quiet', 'Rapid', 'Solar'])} {r.choice(['Ocean', 'Peak', 'Forest', 'Harbor'])} {r.choice(['Lamp', 'Chair', 'Kettle', 'Desk'])}"
        ),
    ),
    (
        "company",
        "vendors.csv",
        "vendor",
        ["vendor_id", "vendor", "terms"],
        None,
        lambda r: f"{r.choice(LAST)} {r.choice(['Corp', 'Inc', 'Ltd', 'GmbH', 'LLC'])}",
    ),
    (
        "city",
        "stores.csv",
        "city",
        ["store_id", "city", "region"],
        None,
        lambda r: r.choice(
            [
                "San Francisco",
                "New York",
                "Los Angeles",
                "Salt Lake City",
                "Springfield",
                "Portland",
            ]
        ),
    ),
    (
        "job_title",
        "roles.csv",
        "title",
        ["role_id", "title", "grade"],
        None,
        lambda r: (
            f"{r.choice(['Senior', 'Junior', 'Lead', 'Staff'])} {r.choice(['Engineer', 'Analyst', 'Designer', 'Manager'])}"
        ),
    ),
    (
        "department",
        "org.csv",
        "department",
        ["dept_id", "department", "cost_center"],
        None,
        lambda r: r.choice(
            ["Human Resources", "Customer Success", "Field Operations", "Legal Affairs"]
        ),
    ),
    (
        "street_name",
        "streets.csv",
        "street",
        ["segment_id", "street", "length_m"],
        None,
        lambda r: (
            f"{r.choice(STREETS)} {r.choice(['Street', 'Avenue', 'Road', 'Lane'])}"
        ),
    ),
    (
        "country",
        "shipping.csv",
        "country",
        ["order_id", "country", "carrier"],
        None,
        lambda r: r.choice(
            ["United States", "United Kingdom", "New Zealand", "South Africa"]
        ),
    ),
    (
        "username",
        "accounts.csv",
        "username",
        ["account_id", "username", "created"],
        None,
        lambda r: f"{r.choice(FIRST).lower()[0]}{r.choice(LAST).lower()}{_d(r, 2)}",
    ),
    (
        "email",
        "leads.csv",
        "email",
        ["lead_id", "email", "source"],
        None,
        lambda r: f"{r.choice(FIRST).lower()}.{r.choice(LAST).lower()}@example.com",
    ),
    (
        "first_only",
        "signups.csv",
        "first_name",
        ["signup_id", "first_name", "plan"],
        "ambiguous",
        lambda r: r.choice(FIRST),
    ),
    (
        "notes_names",
        "calls.csv",
        "notes",
        ["call_id", "notes", "duration"],
        "ambiguous",
        lambda r: r.choice(
            [
                f"Spoke with {_full(r)} about renewal",
                "Left a voicemail",
                f"{_full(r)} asked for a callback",
                "No answer",
            ]
        ),
    ),
    (
        "us_address",
        "customers.csv",
        "address",
        ["id", "full_name", "address", "phone"],
        "ADDRESS",
        _us_address,
    ),
    (
        "uk_address",
        "uk_customers.csv",
        "postal_address",
        ["id", "postal_address", "since"],
        "ADDRESS",
        lambda r: (
            f"{r.randint(1, 200)} {r.choice(STREETS)} Road, London {r.choice(['SW1A', 'EC1V', 'N1', 'SE10'])} {r.randint(1, 9)}{r.choice('ABDEFGHJ')}{r.choice('ABDEFGHJ')}"
        ),
    ),
    (
        "ca_address",
        "ca_clients.csv",
        "adresse",
        ["client", "adresse", "langue"],
        "ADDRESS",
        lambda r: (
            f"{r.randint(1, 999)} Rue Sainte-Catherine, Montréal, QC H{r.randint(1, 9)}B {r.randint(1, 9)}A{r.randint(1, 9)}"
        ),
    ),
    (
        "de_address",
        "de_kunden.csv",
        "anschrift",
        ["kunde", "anschrift", "seit"],
        "ADDRESS",
        lambda r: (
            f"{r.choice(['Haupt', 'Berg', 'Linden'])}straße {r.randint(1, 99)}, {_d(r, 5)} {r.choice(['Berlin', 'Hamburg', 'München'])}"
        ),
    ),
    (
        "fr_address",
        "fr_clients.csv",
        "adresse_postale",
        ["client", "adresse_postale"],
        "ADDRESS",
        lambda r: (
            f"{r.randint(1, 99)} rue de la {r.choice(['Paix', 'Gare', 'République'])}, {r.choice(['75002', '69001', '13001'])} {r.choice(['Paris', 'Lyon', 'Marseille'])}"
        ),
    ),
    (
        "apt_address",
        "tenants.csv",
        "mailing_address",
        ["tenant_id", "mailing_address", "lease_end"],
        "ADDRESS",
        lambda r: (
            f"{r.randint(1, 999)} {r.choice(STREETS)} Ave Apt {r.randint(1, 20)}{r.choice('ABCD')}, {r.choice(CITIES_US)[0]}, {r.choice(CITIES_US)[1]} {r.choice(CITIES_US)[2]}"
        ),
    ),
    (
        "vague_address",
        "export.csv",
        "field_4",
        ["field_1", "field_2", "field_3", "field_4"],
        "ADDRESS",
        _us_address,
    ),
    (
        "street_only",
        "deliveries.csv",
        "street_address",
        ["delivery_id", "street_address", "window"],
        None,
        lambda r: f"{r.randint(1, 9999)} {r.choice(STREETS)} St",
    ),
    (
        "city_state",
        "events.csv",
        "location",
        ["event_id", "location", "date"],
        None,
        lambda r: f"{r.choice(CITIES_US)[0]}, {r.choice(CITIES_US)[1]}",
    ),
    (
        "zip_only",
        "regions.csv",
        "zip",
        ["region_id", "zip", "manager"],
        None,
        lambda r: r.choice(CITIES_US)[2],
    ),
    (
        "gps",
        "devices.csv",
        "position",
        ["device_id", "position", "seen_at"],
        None,
        lambda r: f"{r.uniform(-80, 80):.4f}, {r.uniform(-170, 170):.4f}",
    ),
    (
        "order_ref",
        "orders.csv",
        "order_ref",
        ["order_ref", "total", "status"],
        None,
        lambda r: f"ORD-2026-{_d(r, 5)}",
    ),
    (
        "date",
        "visits.csv",
        "visit_date",
        ["visit_id", "visit_date", "clinic"],
        None,
        lambda r: f"2026-{r.randint(1, 12):02d}-{r.randint(1, 28):02d}",
    ),
    (
        "phone",
        "contacts.csv",
        "phone",
        ["contact_id", "phone", "ext"],
        None,
        lambda r: f"({_d(r, 3)}) {_d(r, 3)}-{_d(r, 4)}",
    ),
]


def column(*, maker, rng) -> list[str]:
    values = [maker(rng) for _ in range(ROWS)]
    #
    # a few empty cells, as real columns have
    #
    for i in rng.sample(range(ROWS), 4):
        values[i] = ""
    return values


def question(*, case: tuple, values: list[str], identifier: str) -> str:
    _, file, col, neighbours, _, _ = case
    meaning, ask = IDENTIFIERS[identifier]
    filled = [v for v in values if v != ""]
    shapes = collections.Counter(mask(v) for v in filled).most_common(TOP_SHAPES)
    listed = ", ".join(f"`{s}` ({n})" for s, n in shapes)
    return (
        f"Identifier: {identifier} ({meaning}).\n"
        f"File: {file}. Column: {col}. Columns in the file: {', '.join(neighbours)}.\n"
        f"Rows: {len(values)}; filled: {len(filled)}; distinct: {len(set(filled))}.\n"
        f"Most common shapes: {listed}.\n"
        f"{ask}"
    )


def questions() -> list[dict]:
    rng = random.Random(SEED)
    out = []
    for case in CASES:
        values = column(maker=case[5], rng=rng)
        for identifier in IDENTIFIERS:
            truth = case[4]
            label = (
                "ambiguous"
                if truth == "ambiguous"
                else "real"
                if truth == identifier
                else "not"
            )
            out.append(
                {
                    "id": f"{case[0]}:{identifier}",
                    "label": label,
                    "text": question(case=case, values=values, identifier=identifier),
                }
            )
    return out


def requests() -> list[dict]:
    qs = questions()
    return [
        {"questions": {q["id"]: q["text"] for q in qs[i : i + BATCH]}}
        for i in range(0, len(qs), BATCH)
    ]


def plan(*, out: str) -> list[dict]:
    if not isinstance(out, str) or out.strip() == "":
        raise ValueError("out must be a directory path")
    os.makedirs(out, exist_ok=True)
    reqs = requests()
    doc = {
        "model": MODEL,
        "state": STATE,
        "choices": CHOICES,
        "labels": {q["id"]: q["label"] for q in questions()},
        "requests": reqs,
    }
    with open(os.path.join(out, "requests.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    return reqs


def send(*, out: str) -> dict:
    from typesafe_sdk import TypeSafeClient
    from typesafe_sdk._core.question_types import Choice

    key = os.environ.get("JEV_KEY")
    if not key:
        raise ValueError("JEV_KEY is not set")
    reqs = plan(out=out)
    results = {"model": MODEL, "requests": []}
    with TypeSafeClient(model=MODEL, api_key=key) as client:
        for r in reqs:
            qs = {
                k: Choice(instructions=v, criteria=CHOICES)
                for k, v in r["questions"].items()
            }
            started = time.perf_counter()
            response = client.system_one(state=STATE, questions=qs)
            results["requests"].append(
                {
                    "model": response.model,
                    "seconds": round(time.perf_counter() - started, 2),
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "answers": {k: a.model_dump() for k, a in response.answers.items()},
                }
            )
    results["summary"] = summarize(results=results)
    with open(os.path.join(out, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    return results


def summarize(*, results: dict) -> dict:
    labels = {q["id"]: q["label"] for q in questions()}
    per = {}
    for r in results["requests"]:
        for k, a in r["answers"].items():
            per[k] = (
                labels[k],
                a["choice"],
                round(a["probabilities"].get("likely", 0.0), 3),
            )
    scored = {k: v for k, v in per.items() if v[0] != "ambiguous"}
    right = [
        k
        for k, (label, choice, _) in scored.items()
        if (choice == "likely") == (label == "real")
    ]
    return {
        "questions": len(per),
        "scored": len(scored),
        "right": len(right),
        "wrong": sorted(set(scored) - set(right)),
        "ambiguous": {k: v for k, v in per.items() if v[0] == "ambiguous"},
        "input_tokens": sum(r["input_tokens"] for r in results["requests"]),
        "output_tokens": sum(r["output_tokens"] for r in results["requests"]),
        "per_question": per,
    }


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("plan", "send"):
        sys.stderr.write("usage: jev_names_experiment.py plan|send <out dir>\n")
        sys.exit(2)
    if sys.argv[1] == "plan":
        reqs = plan(out=sys.argv[2])
        n = sum(len(r["questions"]) for r in reqs)
        sys.stdout.write(
            f"{len(reqs)} requests, {n} questions; written to {sys.argv[2]}/requests.json\n"
        )
    else:
        result = send(out=sys.argv[2])
        sys.stdout.write(json.dumps(result["summary"], indent=2) + "\n")
