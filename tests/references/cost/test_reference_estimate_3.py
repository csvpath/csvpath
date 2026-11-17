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
            (160, 3),
            (161, 4),
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

    @pytest.mark.parametrize("bad", [-1, float("nan"), float("inf")])
    def test_a_bad_total_raises(self, bad):
        with pytest.raises(ValueError):
            ReferenceEstimate3.score_for(bad)

    def test_float_noise_at_an_edge_stays_in_its_bucket(self):
        assert ReferenceEstimate3.score_for(sum([0.1] * 400)) == 2

    def test_a_huge_total_is_the_maximum(self):
        assert ReferenceEstimate3.score_for(10**400) == 10

    def test_the_maximum_is_published(self):
        assert ReferenceEstimate3.MAX_SCORE == 10


class TestTheSpecExamples:
    # the worked examples' scores, from their read counts and the defaults
    def test_the_corpus_star_valid_on_s3_is_4(self):
        est = _estimate(
            [
                Read(part=QUERY, kind="ledger", count=1, basis=EXACT, because="$*"),
                Read(part=QUERY, kind="run_listing", count=11, basis=UPPER_BOUND, because=".*"),
                Read(part=QUERY, kind="instance_manifest", count=23, basis=EXACT, because=".*"),
            ]
        )
        assert (est.score, est.query_score, est.resolve_score) == (4, 4, 1)

    def test_nine_thousand_runs_is_9(self):
        est = _estimate(
            [
                Read(part=QUERY, kind="ledger", count=1, basis=EXACT, because="$*"),
                Read(part=QUERY, kind="run_listing", count=9000, basis=UPPER_BOUND, because=".*"),
                Read(part=QUERY, kind="instance_manifest", count=18900, basis=EXACT, because=".*"),
            ]
        )
        assert est.score == 9

    def test_having_by_content_is_7(self):
        est = _estimate(
            [
                Read(part=QUERY, kind="ledger", count=1, basis=EXACT, because="$acme"),
                Read(part=QUERY, kind="run_listing", count=200, basis=UPPER_BOUND, because=":having()"),
                Read(part=QUERY, kind="instance_manifest", count=800, basis=EXACT, because=":having()"),
                Read(part=QUERY, kind="errors_json", count=800, basis=UPPER_BOUND, because=":having(:errors())"),
            ]
        )
        assert est.score == 7

    def test_the_combined_score_buckets_the_sum(self):
        # the spec's example: query 430 (4) + resolve 400 (4) = 830 (5)
        est = _estimate(
            [
                Read(part=QUERY, kind="ledger", count=1, basis=EXACT, because="$acme"),
                Read(part=QUERY, kind="run_listing", count=1, basis=EXACT, because=":last()"),
                Read(part=QUERY, kind="instance_manifest", count=40, basis=EXACT, because=".*"),
                Read(part=RESOLVE, kind="errors_json", count=40, basis=EXACT, because=":errors()"),
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

    @pytest.mark.parametrize(
        "bad", ["s3:x:1", "s3:1", "s3:-1:2", "sql:a", "s3:nan:1", "s3:inf:1", ":1:2", "s3:1:2, s3:3:4"]
    )
    def test_a_bad_override_raises_naming_it(self, bad):
        with pytest.raises(ValueError, match="cost_weights"):
            CostWeights(overrides=bad)

    def test_an_unknown_backend_raises(self):
        with pytest.raises(ValueError):
            CostWeights().weight(kind="ledger", backend="ftp")

    def test_backend_names_are_case_insensitive(self):
        w = CostWeights(overrides="S3:3:4, Sql:1")
        assert w.weight(kind="ledger", backend="s3") == 3
        assert w.weight(kind="ledger", backend="s3", sql=True) == 1

    def test_a_list_from_config_parses(self):
        # Config splits a value with commas into a list
        w = CostWeights(overrides=["s3:10:20", "sftp:6:7"])
        assert w.weight(kind="ledger", backend="sftp") == 6

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
        names = ("part", "kind", "count", "basis", "because")
        with pytest.raises(ValueError):
            Read(**dict(zip(names, args)))

    def test_a_read_takes_keywords_only(self):
        positional = (QUERY, "ledger", 1, EXACT, "x")
        with pytest.raises(TypeError):
            Read(*positional)


class TestTheParts:
    def _est(self):
        return _estimate(
            [
                Read(part=QUERY, kind="ledger", count=1, basis=EXACT, because="$acme"),
                Read(part=QUERY, kind="instance_manifest", count=4, basis=EXACT, because=".*"),
                Read(part=QUERY, kind="instance_manifest", count=2, basis=UPPER_BOUND, because=".*"),
                Read(part=RESOLVE, kind="errors_json", count=4, basis=EXACT, because=":errors()"),
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
        est = _estimate([Read(part=QUERY, kind="ledger", count=1, basis=EXACT, because="$x")], would_raise="several files (5.3)")
        assert est.to_dict()["would_raise"] == "several files (5.3)"
        assert est.query_score == 1 and "would raise" in est.summary()

    def test_no_reads_scores_1(self):
        est = _estimate([])
        assert (est.score, est.query_score, est.resolve_score) == (1, 1, 1)

    def test_bad_construction_raises(self):
        with pytest.raises(TypeError):
            _estimate(["not a Read"])
        with pytest.raises(ValueError):
            _estimate([], backend="ftp")


class TestExpressionEstimate:
    def test_one_estimate_per_side(self):
        left = _estimate([Read(part=QUERY, kind="ledger", count=1, basis=EXACT, because="$a")])
        right = _estimate([Read(part=QUERY, kind="ledger", count=1, basis=EXACT, because="$b")])
        ex = ExpressionEstimate3(expression="$a UNION $b", left=left, right=right)
        assert ex.to_dict()["left"]["reference"] == "$x.results.:last()"
        assert "left:" in ex.summary() and "right:" in ex.summary()

    def test_a_side_must_be_an_estimate(self):
        with pytest.raises(TypeError):
            ExpressionEstimate3(expression="$a UNION $b", left="x", right="y")
