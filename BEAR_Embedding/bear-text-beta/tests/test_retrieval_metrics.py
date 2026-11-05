import pytest
from bear_text_beta.retrieval_metrics import evaluate_rankings, percentile, query_metrics


def test_one_relevant_at_third_position():
    metrics = query_metrics(["wrong", "also-wrong", "right"], {"right": 1})
    assert metrics == {"ndcg@10": 0.5, "mrr@10": 1 / 3, "recall@50": 1}


def test_reranking_cannot_change_candidate_recall():
    original = [str(i) for i in range(50)]
    reranked = list(reversed(original))
    qrels = {"49": 2, "48": 1, "missing": 1}
    before, after = query_metrics(original, qrels), query_metrics(reranked, qrels)
    assert before["recall@50"] == after["recall@50"] == 2 / 3
    assert before["mrr@10"] == before["ndcg@10"] == 0
    assert after["mrr@10"] == 1 and after["ndcg@10"] > 0


def test_macro_average_includes_no_hits_and_latency():
    report = evaluate_rankings({"q1": ["a"], "q2": []}, {"q1": {"a": 1}, "q2": {"b": 1}},
                               latencies_ms={"q1": 10, "q2": 30})
    assert report["summary"] == {"ndcg@10": 0.5, "mrr@10": 0.5, "recall@50": 0.5,
                                  "query_count": 2, "p50_ms": 20, "p95_ms": 29}


@pytest.mark.parametrize("ranking,qrels", [(["a", "a"], {"a": 1}), ([], {}), ([], {"a": 0}),
                                            ([], {"a": -1}), ([], {"a": float("nan")})])
def test_bad_qrels_and_duplicate_ids_rejected(ranking, qrels):
    with pytest.raises(ValueError):
        query_metrics(ranking, qrels)


def test_missing_query_not_silently_dropped():
    with pytest.raises(ValueError):
        evaluate_rankings({}, {"q": {"a": 1}})
    with pytest.raises(ValueError):
        evaluate_rankings({"q": []}, {"q": {"a": 1}}, latencies_ms={})
    with pytest.raises(ValueError):
        percentile([float("inf")], 0.5)
