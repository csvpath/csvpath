"""docs/macie/managed-identifiers.md is generated from the packaged
catalog. This test fails when they differ; to regenerate the page:

    poetry run python tests/macie/test_macie_docs.py
"""

import os
import sys

from csvpath.macie.managed_catalog import ManagedCatalog

DOC = os.path.join("docs", "macie", "managed-identifiers.md")
CATEGORIES = ["FINANCIAL_INFORMATION", "PERSONAL_INFORMATION", "CREDENTIALS"]

HEAD = """# Managed identifier reference

Every managed data identifier with a stand-in, from the packaged catalog
(`csvpath/macie/rulesbase/managed_identifiers.json`). This page is
generated from the catalog; `tests/macie/test_macie_docs.py` checks it
and regenerates it.

- **Keywords**: the keyword mode (`required`, `absent` or `none`) and the
  keyword list's name in the catalog, which is what a
  [project rulesbase](customizing.md) overrides.
- **Detector**: the detector's name in the catalog; a parameter after `:`
  (e.g. `iban:GB`) selects the country.
- **Fidelity**: A, Macie documents the rule; B, the format is ours from
  the issuer's published rules (see [translation](translation.md)).
- **Partial**: what the stand-in does not detect that Macie says Macie
  does.

Not supported: `NAME` and `ADDRESS`, and driver's licenses for Finland,
Greece, Hungary, Ireland, Latvia, Lithuania, Luxembourg, Malta, the
Netherlands, Poland, Portugal, Romania, Slovakia, Slovenia and Sweden
(see [limitations](limitations.md)).
"""


def _cell(text: str) -> str:
    return text.replace("|", "\\\\|")


def render() -> str:
    catalog = ManagedCatalog.load()
    entries = {n: catalog.identifier(name=n) for n in catalog.names}
    out = [HEAD]
    for category in CATEGORIES:
        names = sorted(n for n, e in entries.items() if e["category"] == category)
        out.append(f"\n## {category} ({len(names)})\n")
        out.append(
            "| Identifier | Keywords | Detector | Severity | Fidelity | Partial |"
        )
        out.append("|---|---|---|---|---|---|")
        for n in names:
            e = entries[n]
            kw = e["keyword_mode"]
            if e["keywords_from"] is not None:
                kw = f"{kw}, `{e['keywords_from']}`"
            partial = _cell(e.get("partial") or "")
            out.append(
                f"| `{n}` | {kw} | `{e['detector']}` | {e['severity']} "
                f"| {e['fidelity']} | {partial} |"
            )
    out.append(f"\n{len(entries)} identifiers.\n")
    return "\n".join(out)


def test_macie_managed_identifier_doc_matches_the_catalog() -> None:
    with open(DOC, encoding="utf-8") as f:
        assert f.read() == render(), (
            f"{DOC} is out of date: run poetry run python tests/macie/test_macie_docs.py"
        )


if __name__ == "__main__":
    with open(DOC, "w", encoding="utf-8") as f:
        f.write(render())
    sys.stdout.write(f"wrote {DOC}\n")
