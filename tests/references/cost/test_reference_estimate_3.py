import json

import pytest

from csvpath.references.reference_estimate_3 import (
    EXACT,
    QUERY,
    RESOLVE,
    UPPER_BOUND,
    CostWeights,
    ExpressionEstimate3,
    Read,
    ReferenceEstimate3,
)

#
# the estimate's types, score and weights (references_v3_cost_estimates.md,
# approved by David 2026-11-17)
#


def _estimate(reads, *, backend="s3", why=None, sql=False, would_raise=None):
    return ReferenceEstimate3(
        reference="$x.results.:last()",
        reads=reads,
        why=why or ["a reason"],
        backend=backend,
        weights=CostWeights(),
        sql=sql,
        would_raise=would_raise,
    )


class TestScore:
    @pytest.mark.parametrize(
        "weighted, score",
        [
            (0, 1),
            (10, 1),
            (11, 2),
            (40, 2),
            (41, 3),
            (640, 4),
            (641, 5),
            (2560, 5),
            (655360, 9),
            (655361, 10),
            (10**12, 10),
        ],
    )
    def test_the_buckets_are_x4_from_10(self, weighted, score):
        assert ReferenceEstimate3.score_for(weighted) == score

    def test_a_negative_total_raises(self):
        with pytest.raises(ValueError):
            ReferenceEstimate3.score_for(-1)

    def test_the_maximum_is_published(self):
        assert ReferenceEstimate3.MAX_SCORE == 10


class TestTheSpecExamples:
    # the worked examples' scores, from their read counts and the defaults
    def test_the_corpus_star_valid_on_s3_is_4(self):
        est = _estimate(
            [
                Read(QUERY, "ledger", 1, EXACT, "$*"),
                Read(QUERY, "run_listing", 11, UPPER_BOUND, ".*"),
                Read(QUERY, "instance_manifest", 23, EXACT, ".*"),
            ]
        )
        assert (est.score, est.query_score, est.resolve_score) == (4, 4, 1)

    def test_nine_thousand_runs_is_9(self):
        est = _estimate(
            [
                Read(QUERY, "ledger", 1, EXACT, "$*"),
                Read(QUERY, "run_listing", 9000, UPPER_BOUND, ".*"),
                Read(QUERY, "instance_manifest", 18900, EXACT, ".*"),
            ]
        )
        assert est.score == 9

    def test_having_by_content_is_7(self):
        est = _estimate(
            [
                Read(QUERY, "ledger", 1, EXACT, "$acme"),
                Read(QUERY, "run_listing", 200, UPPER_BOUND, ":having()"),
                Read(QUERY, "instance_manifest", 800, EXACT, ":having()"),
                Read(QUERY, "errors_json", 800, UPPER_BOUND, ":having(:errors())"),
            ]
        )
        assert est.score == 7

    def test_the_combined_score_buckets_the_sum(self):
        # the spec's example: query 430 (4) + resolve 400 (4) = 830 (5)
        est = _estimate(
            [
                Read(QUERY, "ledger", 1, EXACT, "$acme"),
                Read(QUERY, "run_listing", 1, EXACT, ":last()"),
                Read(QUERY, "instance_manifest", 40, EXACT, ".*"),
                Read(RESOLVE, "errors_json", 40, EXACT, ":errors()"),
            ]
        )
        assert (est.query_score, est.resolve_score, est.score) == (4, 4, 5)


class TestWeights:
    def test_the_defaults(self):
        w = CostWeights()
        assert w.weight(kind="instance_manifest", backend="local") == 1
        assert w.weight(kind="run_listing", backend="s3") == 20
        assert w.weight(kind="errors_json", backend="gcs") == 10
        assert w.weight(kind="ledger", backend="sftp") == 5

    def test_sql_serves_ledgers_manifests_and_listings_not_content(self):
        w = CostWeights()
        assert w.weight(kind="instance_manifest", backend="s3", sql=True) == 2
        assert w.weight(kind="run_listing", backend="s3", sql=True) == 2
        assert w.weight(kind="errors_json", backend="s3", sql=True) == 10

    def test_overrides(self):
        w = CostWeights(overrides="s3:3:4, sql:1, nas:7:9")
        assert w.weight(kind="ledger", backend="s3") == 3
        assert w.weight(kind="name_listing", backend="s3") == 4
        assert w.weight(kind="ledger", backend="nas") == 7
        assert w.weight(kind="ledger", backend="s3", sql=True) == 1
        assert w.weight(kind="ledger", backend="azure") == 10

    @pytest.mark.parametrize("bad", ["s3:x:1", "s3:1", "s3:-1:2", "sql:a"])
    def test_a_bad_override_raises_naming_it(self, bad):
        with pytest.raises(ValueError, match="cost_weights"):
            CostWeights(overrides=bad)

    def test_an_unknown_backend_raises(self):
        with pytest.raises(ValueError):
            CostWeights().weight(kind="ledger", backend="ftp")

    def test_from_config(self):
        class _Config:
            def get(self, *, section, name):
                assert (section, name) == ("references", "cost_weights")
                return "local:2:3"

        assert CostWeights.for_config(_Config()).weight(kind="ledger", backend="local") == 2


class TestRead:
    @pytest.mark.parametrize(
        "args",
        [
            ("both", "ledger", 1, EXACT, "x"),
            (QUERY, "bytes", 1, EXACT, "x"),
            (QUERY, "ledger", -1, EXACT, "x"),
            (QUERY, "ledger", True, EXACT, "x"),
            (QUERY, "ledger", 1, "guess", "x"),
            (QUERY, "ledger", 1, EXACT, " "),
        ],
    )
    def test_a_bad_read_raises(self, args):
        with pytest.raises(ValueError):
            Read(*args)


class TestTheParts:
    def _est(self):
        return _estimate(
            [
                Read(QUERY, "ledger", 1, EXACT, "$acme"),
                Read(QUERY, "instance_manifest", 4, EXACT, ".*"),
                Read(QUERY, "instance_manifest", 2, UPPER_BOUND, ".*"),
                Read(RESOLVE, "errors_json", 4, EXACT, ":errors()"),
            ],
            why=["'.*' reads each instance's manifest", ":errors() reads one file each"],
        )

    def test_reads_per_part(self):
        est = self._est()
        assert est.query_reads == {"ledger": 1, "instance_manifest": 6}
        assert est.resolve_reads == {"errors_json": 4}

    def test_estimated_lists_what_is_not_exact(self):
        assert self._est().estimated == ["instance_manifest x2 (upper bound, .*)"]

    def test_to_dict_is_json_ready_and_complete(self):
        d = self._est().to_dict()
        json.dumps(d)
        assert d["max_score"] == 10 and d["backend"] == "s3"
        assert d["score"] == self._est().score
        assert d["reads"][0] == {
            "part": "query",
            "kind": "ledger",
            "count": 1,
            "basis": "exact",
            "because": "$acme",
        }

    def test_summary_has_the_scores_reads_and_why(self):
        text = self._est().summary()
        assert "score" in text and "query:" in text and "resolve: 4 errors_json" in text
        assert "why:" in text and "estimated:" in text

    def test_would_raise_keeps_the_scores(self):
        est = _estimate([Read(QUERY, "ledger", 1, EXACT, "$x")], would_raise="several files (5.3)")
        assert est.to_dict()["would_raise"] == "several files (5.3)"
        assert est.query_score == 1 and "would raise" in est.summary()

    def test_bad_construction_raises(self):
        with pytest.raises(TypeError):
            _estimate(["not a Read"])
        with pytest.raises(ValueError):
            _estimate([], backend="ftp")


class TestExpressionEstimate:
    def test_one_estimate_per_side(self):
        left = _estimate([Read(QUERY, "ledger", 1, EXACT, "$a")])
        right = _estimate([Read(QUERY, "ledger", 1, EXACT, "$b")])
        ex = ExpressionEstimate3(expression="$a UNION $b", left=left, right=right)
        assert ex.to_dict()["left"]["reference"] == "$x.results.:last()"
        assert "left:" in ex.summary() and "right:" in ex.summary()

    def test_a_side_must_be_an_estimate(self):
        with pytest.raises(TypeError):
            ExpressionEstimate3(expression="$a UNION $b", left="x", right="y")
