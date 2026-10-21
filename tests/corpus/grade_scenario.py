#!/usr/bin/env python3
"""Grades one agent's free-text answer to a tests/corpus/scenarios.yaml
scenario against that scenario's ground truth.

This is deliberately decoupled from however the answer was produced -- there
is no API wired up here to spawn an agent directly (Claude Code's Agent tool
is only callable from inside a Claude Code session, not from a standalone
script). The intended flow is: a human or an orchestrating Claude Code
session hands a scenario's `question` to a fresh agent, captures its final
answer as plain text, and passes that text to this script.

Usage:
    poetry run python tests/corpus/grade_scenario.py <scenario_id> "<answer text>"
    poetry run python tests/corpus/grade_scenario.py --all answers.json

Exit code 0 on PASS, 1 on FAIL/error -- usable as a pass/fail check.
"""
import json
import re
import sys
from pathlib import Path

import yaml

SCENARIOS_PATH = Path(__file__).resolve().parent / "scenarios.yaml"


def load_scenarios() -> dict:
    data = yaml.safe_load(SCENARIOS_PATH.read_text())
    return {s["id"]: s for s in data["scenarios"]}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def grade(scenario: dict, answer: str) -> tuple[bool, str]:
    answer_type = scenario["answer_type"]
    expected = scenario["expected"]
    normalized = _normalize(answer)

    if answer_type == "number":
        numbers = re.findall(r"-?\d+", answer)
        if not numbers:
            return False, f"no number found in answer; expected {expected}"
        found = [int(n) for n in numbers]
        if expected in found:
            return True, f"found expected number {expected} in answer"
        return False, f"expected {expected}, found numbers {found}"

    if answer_type == "text_contains_all":
        missing = [term for term in expected if _normalize(term) not in normalized]
        if missing:
            return False, f"answer is missing required terms: {missing}"
        return True, f"answer contains all required terms: {expected}"

    return False, f"unknown answer_type: {answer_type}"


def main() -> None:
    scenarios = load_scenarios()
    if len(sys.argv) == 3 and sys.argv[1] == "--all":
        answers = json.loads(Path(sys.argv[2]).read_text())
        failures = 0
        for scenario_id, answer in answers.items():
            scenario = scenarios.get(scenario_id)
            if scenario is None:
                print(f"UNKNOWN SCENARIO: {scenario_id}")
                failures += 1
                continue
            passed, reason = grade(scenario, answer)
            status = "PASS" if passed else "FAIL"
            print(f"[{status}] {scenario_id}: {reason}")
            if not passed:
                failures += 1
        print(f"\n{len(answers) - failures}/{len(answers)} passed")
        sys.exit(1 if failures else 0)

    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    scenario_id, answer = sys.argv[1], sys.argv[2]
    scenario = scenarios.get(scenario_id)
    if scenario is None:
        print(f"Unknown scenario id: {scenario_id}")
        print(f"Known ids: {sorted(scenarios.keys())}")
        sys.exit(1)

    passed, reason = grade(scenario, answer)
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {scenario_id}: {reason}")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
