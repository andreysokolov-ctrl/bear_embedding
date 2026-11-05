"""Offline IR metrics at the identifier level supplied by the caller.

Chunk IDs must be compared with chunk qrels, document IDs with document qrels.
Missing judgments are treated as zero relevance. No model inference is done here.
"""

import math
from collections.abc import Mapping, Sequence
from numbers import Real


def _finite_number(value):
    return isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value)


def query_metrics(ranking: Sequence[str], qrels: Mapping[str, float], *, final_k=10, candidate_k=50):
    if type(final_k) is not int or type(candidate_k) is not int or not 1 <= final_k <= candidate_k:
        raise ValueError("Require 1 <= final_k <= candidate_k")
    if not qrels or any(not _finite_number(value) or value < 0 for value in qrels.values()):
        raise ValueError("qrels must contain finite non-negative relevance grades")
    if len(set(ranking)) != len(ranking):
        raise ValueError("Duplicate result IDs distort retrieval metrics")
    positives = {identifier for identifier, grade in qrels.items() if grade > 0}
    if not positives:
        raise ValueError("At least one positive judgment is required")
    gains = [(2 ** qrels.get(identifier, 0) - 1) / math.log2(rank + 2)
             for rank, identifier in enumerate(ranking[:final_k])]
    ideal = sorted(qrels.values(), reverse=True)[:final_k]
    idcg = sum((2 ** grade - 1) / math.log2(rank + 2) for rank, grade in enumerate(ideal))
    first = next((rank for rank, identifier in enumerate(ranking[:final_k], 1)
                  if identifier in positives), None)
    return {f"ndcg@{final_k}": sum(gains) / idcg,
            f"mrr@{final_k}": 1 / first if first else 0.0,
            f"recall@{candidate_k}": len(set(ranking[:candidate_k]) & positives) / len(positives)}


def percentile(values, fraction):
    if not values or not 0 <= fraction <= 1:
        raise ValueError("Non-empty values and fraction in [0,1] required")
    if any(not _finite_number(value) or value < 0 for value in values):
        raise ValueError("Latencies must be finite non-negative milliseconds")
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def evaluate_rankings(rankings, qrels, *, latencies_ms=None, final_k=10, candidate_k=50):
    """Macro average over all judged queries; reject missing queries, never skip them."""
    if not qrels or set(rankings) != set(qrels):
        raise ValueError("Rankings must cover exactly the judged query IDs (use [] for no hits)")
    per_query = {query_id: query_metrics(rankings[query_id], grades,
                                       final_k=final_k, candidate_k=candidate_k)
                 for query_id, grades in qrels.items()}
    keys = next(iter(per_query.values()))
    summary = {key: sum(row[key] for row in per_query.values()) / len(per_query) for key in keys}
    summary["query_count"] = len(per_query)
    if latencies_ms is not None:
        if set(latencies_ms) != set(qrels):
            raise ValueError("Provide one measured latency per judged query")
        values = list(latencies_ms.values())
        summary.update(p50_ms=percentile(values, 0.5), p95_ms=percentile(values, 0.95))
    return {"summary": summary, "per_query": per_query}
