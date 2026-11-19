"""Steps 3 and 4 of the validation output survey (#779): flag quirks in
the harness runs and group them by message template.

    python tests/survey/detectors.py runs.jsonl --report report.md [--json groups.json]

Each detector looks at one run, or at the runs of one variant under the
different policies, and returns findings. A finding has a detector code
and the message it is about. Findings are grouped by (detector, message
template), where the template is the message with values, chains and the
function name normalized away, so that one quirk in many functions is one
group.
"""

import argparse
import json
import re
import sys
from collections import defaultdict

SCANNED_LINES = 2
RAISE_POLICIES = {"raise, collect, print"}
NON_RAISE = {"collect, print", "print"}

#
# exceptions a user may see in raise mode: CsvPath's own. anything else is
# a raw Python, or library, exception reaching the user.
#
CSVPATH_EXCEPTIONS = {
    "MatchException",
    "ChildrenException",
    "ChildrenValidationException",
    "DataException",
    "MatchComponentException",
    "VariableException",
    "ParsingException",
    "InputException",
    "InvalidChildException",
    "UnknownFunctionException",
    "InternalFunctionException",
    "PrintParserException",
    "FormatException",
    "FileException",
    "ProcessingException",
    "ConfigurationException",
    "CsvPathsException",
    "InvalidNameException",
}
PARSER_EXCEPTIONS = {
    "UnexpectedCharacters",
    "UnexpectedToken",
    "UnexpectedEOF",
    "UnexpectedInput",
    "VisitError",
}
REPR = re.compile(r"<class '|object at 0x|Traceback \(|<csvpath\.|<function ")
PRINTED = re.compile(r"^[^:]*:(?P<file>[^:]*):(?P<line>\d+):::(?P<source>[^:]*):\s+(?P<msg>.*)$", re.S)

DETECTORS = {
    "WORKER_DIED": ("critical", "the run killed its worker process (memory, crash)"),
    "TIMEOUT": ("critical", "the run did not finish in the time limit"),
    "PARSER_RAW": ("high", "a raw parser (lark) exception reached the user"),
    "RAISED_WITHOUT_RAISE": ("high", "an exception escaped although raise is not in the policy"),
    "RAW_EXCEPTION": ("high", "a raw Python exception type reached the user in raise mode"),
    "REPR_IN_MESSAGE": ("high", "a Python repr in what the user reads"),
    "STDOUT_ONLY": ("high", "a message went to stdout, but no error was recorded or printed"),
    "SILENT_NONE": ("high", "a bad input left the value None with no error at all"),
    "EMPTY_SOURCE": ("medium", "an error with an empty source"),
    "DUPLICATE_COLLECT": ("medium", "the same error collected more than once for a line"),
    "DUPLICATE_PRINT": ("medium", "the same error printed more than once for a line"),
    "PRINT_COLLECT_MISMATCH": ("medium", "printed and collected error counts disagree"),
    "PRINT_ONLY_DIFFERS": ("medium", "print-only prints a different count than collect, print"),
    "RAISE_UNRECORDED": ("medium", "raise mode raised but recorded no error"),
    "RAISE_MISSING": ("medium", "collect records errors but raise mode does not raise"),
    "CASCADE": ("review", "one bad input gives more than one distinct message"),
    "MATCHED_DESPITE_ERROR": ("review", "every line matched although errors were recorded"),
    "ACCEPTED": ("review", "a bad input gave no error at all (may be fine)"),
}


def printed_errors(rec: dict) -> list[dict]:
    out = []
    for p in rec.get("printed") or []:
        m = PRINTED.match(p)
        if m:
            out.append(m.groupdict())
    return out


def messages(rec: dict) -> list[str]:
    ms = [e["message"] for e in rec.get("errors") or []]
    ms += [p["msg"] for p in printed_errors(rec)]
    if rec.get("exception"):
        ms.append(rec["exception"][1])
    return ms


def template(*, msg: str, name: str) -> str:
    t = msg
    t = re.sub(r"<class '[^']*'>", "<class X>", t)
    t = re.sub(r"'[^']*'", "'V'", t)
    t = re.sub(r'"[^"]*"', '"V"', t)
    t = re.sub(r"\b\w+\[\d+\](\.\w+\[\d+\])*(\.\w+)?", "CHAIN", t)
    if name:
        t = re.sub(rf"\b{re.escape(name)}\b", "FN", t)
    t = re.sub(r"-?\d+(\.\d+)?", "N", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:300]


def single_run(rec: dict) -> list[tuple[str, str]]:
    """findings for one run: (detector, message)"""
    out = []
    exc = rec.get("exception")
    etype = exc[0] if exc else None
    emsg = exc[1] if exc else ""
    pol = rec["policy"]
    errors = rec.get("errors") or []
    pe = printed_errors(rec)
    if etype == "WorkerDied":
        return [("WORKER_DIED", rec["csvpath_body"])]
    if etype == "Timeout":
        return [("TIMEOUT", rec["csvpath_body"])]
    if etype in PARSER_EXCEPTIONS:
        out.append(("PARSER_RAW", f"{etype}: {emsg.splitlines()[0] if emsg else ''}"))
    elif etype and pol in NON_RAISE:
        out.append(("RAISED_WITHOUT_RAISE", f"{etype}: {emsg}"))
    elif etype and etype not in CSVPATH_EXCEPTIONS:
        out.append(("RAW_EXCEPTION", f"{etype}: {emsg}"))
    for m in set(messages(rec)):
        if REPR.search(m or ""):
            out.append(("REPR_IN_MESSAGE", m))
    for e in errors:
        if e["source"] == "":
            out.append(("EMPTY_SOURCE", e["message"]))
    for p in pe:
        if p["source"] == "":
            out.append(("EMPTY_SOURCE", p["msg"]))
    seen = defaultdict(int)
    for p in pe:
        seen[(p["line"], p["source"], p["msg"])] += 1
    for (line, source, msg), n in seen.items():
        if n > 1:
            out.append(("DUPLICATE_PRINT", msg))
    stdout = (rec.get("stdout") or "").strip()
    if stdout and not errors and not pe and pol in NON_RAISE:
        out.append(("STDOUT_ONLY", stdout.splitlines()[0]))
    dup = defaultdict(int)
    for e in errors:
        dup[(e.get("line"), e["source"], e["message"])] += 1
    for (line, source, msg), n in dup.items():
        if n > 1 and line is not None:
            out.append(("DUPLICATE_COLLECT", msg))
    if (
        pol == "collect, print"
        and rec["placement"] == "assigned"
        and rec["variant"] != "seed"
        and rec.get("value", "<unset>") is None
        and not errors
        and not pe
        and not stdout
        and not etype
    ):
        out.append(("SILENT_NONE", rec["variant"].split(":")[-1]))
    if pol == "collect, print" and not etype and len(pe) != len(errors):
        out.append(("PRINT_COLLECT_MISMATCH", f"printed {len(pe)}, collected {len(errors)}"))
    if pol == "collect, print" and not etype:
        per_line = defaultdict(set)
        for e in errors:
            per_line[e.get("line")].add(e["message"])
        for distinct in per_line.values():
            if len(distinct) > 1:
                out.append(("CASCADE", " || ".join(sorted(distinct))))
                break
        if errors and rec.get("lines") == SCANNED_LINES and len(errors) >= SCANNED_LINES:
            out.append(("MATCHED_DESPITE_ERROR", errors[0]["message"]))
        if (
            rec["variant"] != "seed"
            and not errors
            and not pe
            and not stdout
            and rec["placement"] == "as_is"
        ):
            out.append(("ACCEPTED", rec["variant"].split(":")[-1]))
    return out


def across_policies(runs: list[dict]) -> list[tuple[str, str, dict]]:
    """findings that compare one variant's runs under the policies"""
    by = {r["policy"]: r for r in runs}
    out = []
    c, p, r = by.get("collect, print"), by.get("print"), by.get("raise, collect, print")
    if c and p and not c.get("exception") and not p.get("exception"):
        if len(printed_errors(c)) != len(printed_errors(p)):
            out.append(
                (
                    "PRINT_ONLY_DIFFERS",
                    f"collect, print {len(printed_errors(c))} vs print {len(printed_errors(p))}",
                    p,
                )
            )
    if r and r.get("exception") and not (r.get("errors")):
        if r["exception"][0] not in ("WorkerDied", "Timeout") and r["exception"][0] not in PARSER_EXCEPTIONS:
            out.append(("RAISE_UNRECORDED", f"{r['exception'][0]}: {r['exception'][1]}", r))
    if c and r and c.get("errors") and not c.get("exception") and not r.get("exception"):
        out.append(("RAISE_MISSING", c["errors"][0]["message"], r))
    return out


def analyze(path: str) -> dict:
    groups: dict = {}
    variants = defaultdict(list)
    total = 0

    def add(*, det: str, msg: str, rec: dict) -> None:
        key = (det, template(msg=msg or "", name=rec["name"]))
        g = groups.get(key)
        if g is None:
            g = groups[key] = {
                "detector": det,
                "severity": DETECTORS[det][0],
                "template": key[1],
                "runs": 0,
                "functions": set(),
                "policies": set(),
                "placements": set(),
                "example": None,
                "example_message": None,
            }
        g["runs"] += 1
        g["functions"].add(rec["name"])
        g["policies"].add(rec["policy"])
        g["placements"].add(rec["placement"])
        if g["example"] is None or len(rec["csvpath_body"]) < len(g["example"]["body"]):
            g["example"] = {
                "body": rec["csvpath_body"],
                "policy": rec["policy"],
                "name": rec["name"],
                "variant": rec["variant"],
            }
            g["example_message"] = msg

    with open(path, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            total += 1
            for det, msg in single_run(rec):
                add(det=det, msg=msg, rec=rec)
            variants[(rec["name"], rec["variant"], rec["placement"])].append(rec)
    for runs in variants.values():
        for det, msg, rec in across_policies(runs):
            add(det=det, msg=msg, rec=rec)
    return {"total": total, "groups": groups}


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "review": 3}


def report(*, result: dict, out: str) -> None:
    gs = sorted(
        result["groups"].values(),
        key=lambda g: (SEVERITY_ORDER[g["severity"]], -len(g["functions"]), -g["runs"]),
    )
    by_det = defaultdict(lambda: [0, 0])
    for g in gs:
        by_det[g["detector"]][0] += 1
        by_det[g["detector"]][1] += g["runs"]
    lines = [
        "# Validation output survey: findings",
        "",
        f"{result['total']} runs, {len(gs)} groups.",
        "",
        "| detector | severity | groups | runs | meaning |",
        "|---|---|---|---|---|",
    ]
    for det, (sev, meaning) in DETECTORS.items():
        n = by_det.get(det, [0, 0])
        lines.append(f"| {det} | {sev} | {n[0]} | {n[1]} | {meaning} |")
    lines += ["", "## Groups", ""]
    for i, g in enumerate(gs, 1):
        ex = g["example"]
        fns = sorted(g["functions"])
        lines += [
            f"### {i}. {g['detector']} ({g['severity']}): {len(fns)} functions, {g['runs']} runs",
            "",
            f"- template: `{g['template']}`",
            f"- example: `{ex['body']}` under `{ex['policy']}` ({ex['name']}, {ex['variant']})",
            f"- message: `{(g['example_message'] or '')[:300]}`",
            f"- placements: {', '.join(sorted(g['placements']))}; policies: {'; '.join(sorted(g['policies']))}",
            f"- functions: {', '.join(fns[:40])}{' ...' if len(fns) > 40 else ''}",
            "",
        ]
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("runs")
    ap.add_argument("--report", required=True)
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    result = analyze(a.runs)
    report(result=result, out=a.report)
    if a.json:
        gs = []
        for g in result["groups"].values():
            g = dict(g)
            for k in ("functions", "policies", "placements"):
                g[k] = sorted(g[k])
            gs.append(g)
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(gs, fh, indent=1)
    sev = defaultdict(int)
    for g in result["groups"].values():
        sev[g["severity"]] += 1
    print(f"{result['total']} runs -> {len(result['groups'])} groups: {dict(sev)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
