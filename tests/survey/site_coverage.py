"""Step 5 of the validation output survey (#779): the share of message
sites (message_sites.py) that a harness run reached.

Run the harness under coverage, combine, then:
    python tests/survey/site_coverage.py --data <.coverage> [--unhit unhit.json]

A site counts as reached if its line ran. For a raise or handle_error
site that is the message being produced; a reached site whose message
was never seen in the runs is still counted, since the line ran.
"""

import argparse
import json
import os
import sys
from collections import Counter

import coverage

sys.path.insert(0, os.path.dirname(__file__))
import message_sites  # noqa: E402


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", required=True)
    ap.add_argument("--unhit")
    a = ap.parse_args(argv)
    cov = coverage.Coverage(data_file=a.data)
    cov.load()
    data = cov.get_data()
    executed = {}
    for f in data.measured_files():
        rel = os.path.relpath(f).replace(os.sep, "/")
        executed[rel] = set(data.lines(f) or [])
    sites = message_sites.find_sites()
    hit = [s for s in sites if s.line in executed.get(s.file, set())]
    unhit = [s for s in sites if s.line not in executed.get(s.file, set())]
    print(f"{len(hit)} of {len(sites)} message sites reached ({100 * len(hit) / len(sites):.1f}%)")
    by_area_all = Counter(s.area for s in sites)
    by_area_hit = Counter(s.area for s in hit)
    for area, n in by_area_all.most_common():
        print(f"  {by_area_hit[area]:4} / {n:4}  {area}")
    by_kind_all = Counter(s.kind for s in sites)
    by_kind_hit = Counter(s.kind for s in hit)
    for k, n in by_kind_all.items():
        print(f"  {by_kind_hit[k]:4} / {n:4}  {k}")
    if a.unhit:
        with open(a.unhit, "w", encoding="utf-8") as fh:
            json.dump([s.__dict__ for s in unhit], fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
