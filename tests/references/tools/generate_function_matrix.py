"""Generates a coverage matrix of every registered references-v3 function:
role, which datatypes it declares support for, arg shape, field source,
which name_one/name_two/name_three position it is legal in per datatype,
and whether it has real test coverage -- both at the function-unit level
and integration-tested (actually exercised via a real reference string
against a real Finder) per datatype.

David asked for "a better lay of the land" on the references-v3 surface --
this is the mechanical half of that: it turns "what's covered, and where"
from tribal knowledge spread across three Finder files plus one doc into a
single, regeneratable, auditable table. Deliberately NOT a fuzzer (that
idea is deferred, separately) -- this only reports on the finite,
enumerable set of functions that already exist; it does not explore what a
random/generated reference string would do at runtime.

Run:
    CSVPATH_CONFIG_PATH=assets/config/config.ini poetry run python3 \
        tests/references/tools/generate_function_matrix.py

Writes the report to references_notes/notes/function_coverage_matrix.md.

Mechanically derived every run (always accurate, no manual upkeep): role,
datatypes, arg shape, source, unit-test-file-exists, integration-test-grep-
hit-per-datatype, and the POSITION of every plain field-accessor function
(SOURCE set) -- FILES field accessors ride at name_three, CSVPATHS field
accessors ride at name_one (both mirror that datatype's own version-
selector position), and RESULTS field accessors are derived from whether
their own KEY dict has a Reference3.RESULTS entry (name_one/run-level), a
Reference3.RESULT entry (name_three/instance-level), or both.

Manually curated (accurate as of 2026-08-13; re-check if a Finder's
query() logic changes): position for the ~20 non-field-accessor functions
(pointers, context setters, well-known-file/wrapper functions, argument-
only VALUE wrappers) in SPECIAL_POSITIONS/SPECIAL_NOTES below. WHERE these
are legal is enforced by procedural code scattered across three different
Finder classes, not declared anywhere as data -- reliably auto-deriving it
would need a much heavier static-analysis pass than this script attempts,
so it is hand-written here instead, from direct reading of all three
Finders during the same work that produced this script.
"""

import re
from pathlib import Path

from csvpath.references.functions.reference_function_factory_3 import (
    ReferenceFunctionFactory as RFF,
)
from csvpath.references.reference_3 import Reference3

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
# manually curated positions for the ~20 functions that are NOT plain
# field accessors -- see module docstring's "Manually curated" section.
# One entry per datatype: a position string, None (not supported/not
# meaningful), or a flagged string for a known declared-but-broken case
# (see ":name()" below).
#
SPECIAL_POSITIONS = {
    "first": {"files": "name_three", "csvpaths": "name_one", "results": "name_one"},
    "last": {"files": "name_three", "csvpaths": "name_one", "results": "name_one"},
    "index": {"files": "name_three", "csvpaths": "name_one", "results": "name_one"},
    "name": {
        "files": "name_one",
        "csvpaths": "**declared but broken -- silently no-ops, see Notes**",
        "results": None,
    },
    "all": {"files": "name_three", "csvpaths": "name_one", "results": "name_one"},
    "flatten": {"files": "name_one", "csvpaths": None, "results": "name_one"},
    "groups": {"files": "name_one", "csvpaths": None, "results": "name_one"},
    "having": {"files": None, "csvpaths": "name_one", "results": None},
    "from": {
        "files": "name_three",
        "csvpaths": "name_one, name_three",
        "results": "name_one, name_three",
    },
    "to": {
        "files": "name_three",
        "csvpaths": "name_one, name_three",
        "results": "name_one, name_three",
    },
    "date": {
        "files": "argument (inside :from()/:to())",
        "csvpaths": "argument (inside :from()/:to())",
        "results": "argument (inside :from()/:to())",
    },
    "manifest": {"files": "name_three", "csvpaths": "name_one", "results": "name_one"},
    "definition": {"files": "name_one (bare)", "csvpaths": "name_one (bare)", "results": None},
    "path": {"files": "name_three", "csvpaths": "name_one", "results": None},
    "errors": {"files": None, "csvpaths": None, "results": "name_three (instance-level)"},
    "vars": {"files": None, "csvpaths": None, "results": "name_three (instance-level)"},
    "meta": {"files": None, "csvpaths": None, "results": "name_three (instance-level)"},
    "data": {"files": None, "csvpaths": None, "results": "name_three (instance-level)"},
    "unmatched": {"files": None, "csvpaths": None, "results": "name_three (instance-level)"},
    "file": {"files": None, "csvpaths": None, "results": "name_three (instance-level)"},
    "idchain": {"files": None, "csvpaths": None, "results": "argument (inside :errors())"},
}

SPECIAL_NOTES = {
    "name": (
        "DATATYPES includes csvpaths, but CsvpathsReferenceFinder3."
        "_resolve_versions() has no unrecognized-function guard the way "
        "query()'s name_three handling does -- $acme.csvpaths.:name(\"x\") "
        "silently no-ops instead of raising, contradicting the class's own "
        "docstring. Flagged 2026-08-13, not fixed."
    ),
    "all": (
        "FILES/CSVPATHS: switches the version-selector chain from POINTER-"
        "reduces-to-one to unreduced-list-of-every-match. RESULTS: one-level "
        "GROUP peer of '*'."
    ),
    "flatten": "any-depth POOL peer of ':all()'/'*'. Not built for CSVPATHS -- no depth dimension (groups do not nest).",
    "groups": "any-depth GROUP peer of ':flatten()'. Not built for CSVPATHS.",
    "having": "filters the version list by statement-identity presence before any pointer/range reduces further.",
    "from": "':to()' is INCLUSIVE. Index-mode (int/:index(n)) POSITIONALLY slices; date-mode (str/:date(...)) FILTERS by arrival time. A real pointer riding alongside reduces the RANGE, not the full candidate set.",
    "to": "always paired with :from() -- see its own note.",
    "date": "VALUE-role wrapper; DATATYPES declares results only, but is reused inside FILES/CSVPATHS' own :from()/:to() via their ARG_TYPES, not a separate per-datatype registration.",
    "manifest": "may ride bare or beside a pointer -- never narrows/selects itself. Also the special root_major='*' global-ledger case for FILES/CSVPATHS.",
    "definition": "group/named-file-level, not per-version -- always the whole resource.",
    "path": "wraps another whole-resource function (e.g. :path(:manifest())) -- returns its filesystem path instead of its content.",
    "idchain": "arg to :errors(...) -- filters by a matching-line's idchain value.",
    "first": "version/run/instance selector.",
    "last": "version/run/instance selector.",
    "index": "version/run/instance selector.",
    "errors": "instance-level content accessor -- :idchain() may be passed as its arg to filter further.",
    "vars": "instance-level content accessor, same position as :errors().",
    "meta": "instance-level content accessor, same position as :errors().",
    "data": "instance-level content accessor, same position as :errors().",
    "unmatched": "instance-level content accessor, same position as :errors().",
    "file": "instance-level content accessor (print-mode output file) -- takes a literal filename arg.",
}
DEFAULT_NOTE = (
    "field accessor -- rides beside the matched entity's own pointer."
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


def _default_position(cls, datatype: str) -> str | None:
    """mechanical position for a plain field accessor (SOURCE set, not in
    SPECIAL_POSITIONS) -- FILES/CSVPATHS mirror that datatype's own
    version-selector position; RESULTS is derived from whether the
    function's own KEY dict serves the run level (Reference3.RESULTS),
    the instance level (Reference3.RESULT), or both."""
    if datatype not in (cls.DATATYPES or ()):
        return None
    if datatype == "files":
        return "name_three"
    if datatype == "csvpaths":
        return "name_one"
    # results
    has_run = Reference3.RESULTS in cls.KEY
    has_instance = Reference3.RESULT in cls.KEY
    if has_run and has_instance:
        return "name_one, name_three"
    if has_instance:
        return "name_three (instance-level only)"
    if has_run:
        return "name_one (run-level only)"
    return "name_one"  # SOURCE="-" default-shape functions not otherwise flagged


def main() -> None:
    RFF.get_registered_class("first")  # triggers _load() -- see factory's own laziness
    rows = []
    for name, cls in sorted(RFF._FUNCTIONS.items()):
        datatypes = cls.DATATYPES or ()
        unit_tested = _unit_test_path(cls).exists()
        positions = SPECIAL_POSITIONS.get(name)
        note = SPECIAL_NOTES.get(name, DEFAULT_NOTE if positions is None else "")
        cells = {}
        for dt in ("files", "csvpaths", "results"):
            pos = positions[dt] if positions is not None else _default_position(cls, dt)
            tested = _integration_hits(name, dt) if dt in datatypes else None
            cells[dt] = (pos, tested)
        rows.append(
            {
                "name": name,
                "role": cls.ROLE,
                "datatypes": datatypes,
                "arg_required": cls.ARG_REQUIRED,
                "source": cls.SOURCE,
                "unit_tested": unit_tested,
                "cells": cells,
                "note": note,
            }
        )

    def cell_text(pos, tested) -> str:
        if pos is None:
            return "n/a"
        if tested is None:
            return pos
        return f"{pos} -- {'tested' if tested else '**MISSING**'}"

    out = []
    out.append("# CsvPath References v3 -- function coverage matrix\n\n")
    out.append(
        "Generated by `tests/references/tools/generate_function_matrix.py` -- "
        "re-run any time the function registry or test files change; do not "
        "hand-edit the table below (edit the script's own `SPECIAL_POSITIONS`/"
        "`SPECIAL_NOTES` dicts instead, for the manually-curated parts).\n\n"
    )
    out.append(
        "| Function | Role | Datatypes | Arg required | Source | Unit test | "
        "FILES | CSVPATHS | RESULTS | Notes |\n"
    )
    out.append("|---|---|---|---|---|---|---|---|---|---|\n")
    for r in rows:
        c = r["cells"]
        out.append(
            f"| `:{r['name']}()` | {r['role']} | {', '.join(r['datatypes']) or '-'} | "
            f"{'yes' if r['arg_required'] else 'no'} | {r['source'] or '-'} | "
            f"{'yes' if r['unit_tested'] else '**MISSING**'} | "
            f"{cell_text(*c['files'])} | {cell_text(*c['csvpaths'])} | "
            f"{cell_text(*c['results'])} | {r['note']} |\n"
        )

    missing = [
        r
        for r in rows
        if not r["unit_tested"] or any(v[1] is False for v in r["cells"].values())
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
            for dt, (pos, tested) in r["cells"].items():
                if tested is False:
                    problems.append(f"no {dt} integration-test hit")
            out.append(f"- `:{r['name']}()` -- {'; '.join(problems)}\n")

    report_path = REPO_ROOT / "references_notes" / "notes" / "function_coverage_matrix.md"
    report_path.write_text("".join(out))
    print(f"wrote {report_path} ({len(rows)} functions, {len(missing)} with gaps)")


if __name__ == "__main__":
    main()
