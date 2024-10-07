import numpy as np

def hit_rate(ground_truth, predictions):
    hit_rate_scores = []
    for query, relevant_docs in ground_truth.items():
        retrieved_docs = predictions.get(query, [])
        hit = 1 if any(doc in relevant_docs for doc in retrieved_docs) else 0
        hit_rate_scores.append(hit)
    return float(np.mean(np.array(hit_rate_scores)))


def mean_reciprocal_rank(ground_truth, predictions):
    mrr_scores = []
    for query, relevant_docs in ground_truth.items():
        retrieved_docs = predictions.get(query, [])
        ranks = [1/(i+1) for i, doc in enumerate(retrieved_docs) if doc in relevant_docs]
        mrr_scores.append(max(ranks) if ranks else 0)
    return float(np.mean(np.array(mrr_scores)))


