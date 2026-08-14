"""Generates a coverage matrix of every registered references-v3 function:
role, which datatypes it declares support for, arg shape, field source, and
whether it has real test coverage -- both at the function-unit level and
integration-tested (actually exercised via a real reference string against a
real Finder) per datatype.

David asked for "a better lay of the land" on the references-v3 surface --
this is the mechanical half of that: it turns "what's covered" from tribal
knowledge spread across three Finder files plus one doc into a single,
regeneratable, auditable table. Deliberately NOT a fuzzer (that idea is
deferred, separately) -- this only reports on the finite, enumerable set of
functions that already exist; it does not explore what a random/generated
reference string would do at runtime.

Run:
    CSVPATH_CONFIG_PATH=assets/config/config.ini poetry run python3 \
        tests/references/tools/generate_function_matrix.py

Writes the report to references_notes/notes/function_coverage_matrix.md.

Mechanically derived every run (always accurate, no manual upkeep): role,
datatypes, arg shape, source, unit-test-file-exists, integration-test-grep-
hit-per-datatype.

Manually curated (accurate as of 2026-08-13; re-check if a Finder's query()
logic changes): the position/notes column. WHERE in a reference string
(name_one/name_two/name_three) a function is legal is enforced by
procedural code scattered across three different Finder classes, not
declared anywhere as data -- reliably auto-deriving it would need a much
heavier static-analysis pass than this script attempts, so it is
hand-written here instead, from direct reading of all three Finders during
the same work that produced this script.
"""

import re
from pathlib import Path

from csvpath.references.functions.reference_function_factory_3 import (
    ReferenceFunctionFactory as RFF,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

INTEGRATION_TEST_FILES = {
    "files": [
        REPO_ROOT / "tests/references/test_files_reference_finder_3.py",
        REPO_ROOT / "tests/references/test_normative_examples_files.py",
    ],
    "csvpaths": [
        REPO_ROOT / "tests/references/test_csvpaths_reference_finder_3.py",
        REPO_ROOT / "tests/references/test_normative_examples_csvpaths.py",
    ],
    "results": [
        REPO_ROOT / "tests/references/test_results_reference_finder_3.py",
        REPO_ROOT / "tests/references/test_normative_examples_results.py",
    ],
}

#
# manually curated -- see module docstring's "Manually curated" section.
# Every function NOT listed here is a plain field accessor (SOURCE=
# "manifest"/"definition"/"computed") and gets DEFAULT_FIELD_ACCESSOR_NOTE
# instead -- they all share one rule (ride beside the matched entity's own
# pointer chain), so listing each individually would be pure repetition.
#
POSITION_NOTES = {
    "first": "CSVPATHS/RESULTS: name_one (version/run selector). FILES: name_three (version selector).",
    "last": "same position(s) as :first().",
    "index": "same position(s) as :first().",
    "name": "FILES name_one only -- the literal-path-building selector (:name(\"x\")). Not meaningful for CSVPATHS/RESULTS (no path dimension in name_one there); RESULTS uses literal/'*' path segments instead of :name().",
    "all": "FILES/CSVPATHS: rides beside the pointer in whichever chain occupies the version-selector position (name_three for FILES, name_one for CSVPATHS). RESULTS: name_one (run-level), one-level GROUP peer of '*'.",
    "flatten": "FILES: name_one, first-segment-only, any-depth POOL peer of ':all()'/'*'. RESULTS: name_one, any-depth POOL peer of ':all()'/'*'. Not built for CSVPATHS -- no depth dimension to flatten (groups do not nest).",
    "groups": "FILES: name_one, any-depth GROUP peer of ':flatten()'. RESULTS: name_one, any-depth GROUP peer of ':flatten()'. Not built for CSVPATHS.",
    "having": "CSVPATHS name_one only -- filters the version list by statement-identity presence before any pointer/range reduces further.",
    "from": "RESULTS: name_one (run-level range) AND name_three (statement-level range, index-mode only). FILES: name_three (version-level range, index+date mode). CSVPATHS: name_one (version-level range, index+date mode) AND name_three (statement-level range, index-mode only, since individual statements have no arrival time of their own).",
    "to": "always paired with :from() -- same position(s).",
    "date": "VALUE-role argument wrapper, RESULTS-only in DATATYPES but reused by FILES/CSVPATHS' own date-mode ranges too (accepted via From3/To3's own ARG_TYPES, not a separate per-datatype registration) -- used INSIDE :from()/:to(), never appears bare as a position of its own.",
    "manifest": "bare or beside a pointer, in the version/run-selector chain for all three datatypes (name_one for CSVPATHS/RESULTS, name_three for FILES) -- also the special root_major='*' global-ledger case for FILES/CSVPATHS.",
    "definition": "CSVPATHS/FILES only, bare, group/named-file-level (not per-version) -- no position dimension, always the whole resource.",
    "path": "FILES/CSVPATHS -- wraps another whole-resource function (e.g. :path(:manifest())), rides in the same chain that function would occupy on its own.",
    "errors": "RESULTS instance-level content accessor -- rides after name_three's statement-identity selection.",
    "vars": "same position as :errors().",
    "meta": "same position as :errors().",
    "data": "same position as :errors().",
    "unmatched": "same position as :errors().",
    "file": "same position as :errors() -- takes a literal filename arg (print-mode output file).",
    "idchain": "RESULTS only -- VALUE-role arg wrapper, used inside :errors(...), never a position of its own.",
}
DEFAULT_FIELD_ACCESSOR_NOTE = (
    "field accessor -- rides beside the matched entity's own pointer, "
    "same chain/position as :first()/:last()/:index(n) for that datatype."
)


def _unit_test_path(function_cls) -> Path:
    # e.g. csvpath.references.functions.fields.uuid_3
    #   -> tests/references/functions/fields/test_uuid_3.py
    mod_parts = function_cls.__module__.split(".")
    subpkg, modname = mod_parts[-2], mod_parts[-1]
    return REPO_ROOT / "tests" / "references" / "functions" / subpkg / f"test_{modname}.py"


def _integration_hits(name: str, datatype: str) -> bool:
    # require both a '$' (a real reference string's own marker) and
    # ':name(' on the SAME line -- a bare ':from()'/':to()' mention in a
    # comment/docstring (extremely common in this codebase) would
    # otherwise false-positive as "tested" with a plain ':name\(' search.
    # Deliberately NOT excluding quote characters between the two: a
    # nested string arg (e.g. ':name("orders.csv").:from(1):to(3)') puts
    # quotes between '$' and a LATER function call on the same line, so
    # excluding them would wrongly break the match at the first nested arg.
    pattern = re.compile(r"\$.*:" + re.escape(name) + r"\(")
    for path in INTEGRATION_TEST_FILES[datatype]:
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            if pattern.search(line):
                return True
    return False


def main() -> None:
    RFF.get_registered_class("first")  # triggers _load() -- see factory's own laziness
    rows = []
    for name, cls in sorted(RFF._FUNCTIONS.items()):
        datatypes = cls.DATATYPES or ()
        unit_tested = _unit_test_path(cls).exists()
        integration = {
            dt: (_integration_hits(name, dt) if dt in datatypes else None)
            for dt in ("files", "csvpaths", "results")
        }
        rows.append(
            {
                "name": name,
                "role": cls.ROLE,
                "datatypes": datatypes,
                "arg_required": cls.ARG_REQUIRED,
                "source": cls.SOURCE,
                "unit_tested": unit_tested,
                "integration": integration,
                "note": POSITION_NOTES.get(name, DEFAULT_FIELD_ACCESSOR_NOTE),
            }
        )

    def cell(v) -> str:
        if v is None:
            return "n/a"
        return "yes" if v else "**MISSING**"

    out = []
    out.append("# CSVPath References v3 -- function coverage matrix\n\n")
    out.append(
        "Generated by `tests/references/tools/generate_function_matrix.py` -- "
        "re-run any time the function registry or test files change; do not "
        "hand-edit the table below (edit the script's own `POSITION_NOTES` "
        "dict instead, for the one manually-curated column).\n\n"
    )
    out.append(
        "| Function | Role | Datatypes | Arg required | Source | Unit test | "
        "FILES | CSVPATHS | RESULTS | Position / notes |\n"
    )
    out.append("|---|---|---|---|---|---|---|---|---|---|\n")
    for r in rows:
        out.append(
            f"| `:{r['name']}()` | {r['role']} | {', '.join(r['datatypes']) or '-'} | "
            f"{'yes' if r['arg_required'] else 'no'} | {r['source'] or '-'} | "
            f"{cell(r['unit_tested'])} | {cell(r['integration']['files'])} | "
            f"{cell(r['integration']['csvpaths'])} | {cell(r['integration']['results'])} | "
            f"{r['note']} |\n"
        )

    missing = [
        r
        for r in rows
        if not r["unit_tested"] or any(v is False for v in r["integration"].values())
    ]
    out.append("\n## Gaps found\n\n")
    if not missing:
        out.append(
            "None -- every registered function has a unit test and at least "
            "one integration-test hit for every datatype it declares support "
            "for.\n"
        )
    else:
        for r in missing:
            problems = []
            if not r["unit_tested"]:
                problems.append("no unit test file")
            for dt, v in r["integration"].items():
                if v is False:
                    problems.append(f"no {dt} integration-test hit")
            out.append(f"- `:{r['name']}()` -- {'; '.join(problems)}\n")

    report_path = REPO_ROOT / "references_notes" / "notes" / "function_coverage_matrix.md"
    report_path.write_text("".join(out))
    print(f"wrote {report_path} ({len(rows)} functions, {len(missing)} with gaps)")


if __name__ == "__main__":
    main()
