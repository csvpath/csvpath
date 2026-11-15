"""The Jev review experiment's masking and requests
(tests/macie/live/jev_review_experiment.py). No network: plan() only
builds the requests. The leak test is the one that matters: no
value-shaped text from a case may reach a question."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join("tests", "macie", "live"))
import jev_review_experiment as jre  # noqa: E402


def test_macie_jev_mask() -> None:
    assert jre.mask("309-04-7794") == "###-##-####"
    assert jre.mask("RSSMRA85T10A562S") == "AAAAAA##A##A###A"
    assert jre.mask("+1 (212) 555-0148") == "+# (###) ###-####"
    assert jre.mask("") == ""
    with pytest.raises(TypeError):
        jre.mask(None)


def test_macie_jev_mask_cell_keeps_words() -> None:
    assert jre.mask_cell("ssn on file: 721-99-9913 ok") == "ssn on file: ###-##-#### ok"
    assert jre.mask_cell("pay GB82WEST12345698765432") == "pay AA##AAAA##############"
    with pytest.raises(TypeError):
        jre.mask_cell(None)


def test_macie_jev_no_value_reaches_a_question() -> None:
    for case in jre.CASES:
        q = jre.question(case)
        for sample in case["samples"]:
            for token in sample.split(" "):
                if any(c.isdigit() for c in token):
                    assert token not in q, (case["id"], token)


def test_macie_jev_cases_are_labelled() -> None:
    ids = [c["id"] for c in jre.CASES]
    assert len(ids) == len(set(ids))
    labels = [c["label"] for c in jre.CASES]
    assert labels.count("real") >= 10
    assert labels.count("false") >= 10
    with pytest.raises(ValueError):
        jre._case(
            cid="x",
            label="maybe",
            identifier="X",
            meaning="x",
            file="f",
            columns=["a"],
            column="a",
            rows=1,
            found=1,
            distinct=1,
            why="w",
            samples=[],
        )


def test_macie_jev_plan(tmp_path) -> None:
    reqs = jre.plan(out=str(tmp_path))
    assert [r["kind"] for r in reqs] == ["noul", "noul", "noul", "choice"]
    assert sum(len(r["questions"]) for r in reqs) == len(jre.CASES) + jre.CHOICE_CASES
    with open(os.path.join(tmp_path, "requests.json"), encoding="utf-8") as f:
        written = json.load(f)
    assert written["state"] == jre.STATE
    assert written["requests"] == reqs
    with pytest.raises(ValueError):
        jre.plan(out=" ")


def test_macie_jev_summary() -> None:
    results = {
        "requests": [
            {
                "kind": "noul",
                "seconds": 1.0,
                "input_tokens": 10,
                "output_tokens": 2,
                "answers": {
                    "ssn-hr": {"type": "noul", "noul": 0.9},
                    "ssn-ticket": {"type": "noul", "noul": 0.2},
                    "dob-dogs": {"type": "noul", "noul": 0.5},
                },
            }
        ]
    }
    s = jre.summarize(results=results)
    assert s["scored"] == 2
    assert s["correct_at_0_5"] == 2
    assert s["auc"] == 1.0
    assert s["per_case"]["dob-dogs"] == ("ambiguous", 0.5)
