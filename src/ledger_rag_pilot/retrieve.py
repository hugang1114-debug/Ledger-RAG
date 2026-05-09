import math
import re
from collections import Counter


STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "by",
    "does",
    "is",
    "it",
    "of",
    "or",
    "the",
    "to",
    "what",
    "which",
    "with",
}


def tokenize(text):
    return [token for token in re.findall(r"[a-z0-9]+", text.lower()) if token not in STOPWORDS]


def score_span(query_tokens, span_text):
    span_tokens = tokenize(span_text)
    if not span_tokens:
        return 0.0
    query_counts = Counter(query_tokens)
    span_counts = Counter(span_tokens)
    overlap = sum(min(query_counts[token], span_counts[token]) for token in query_counts)
    coverage = overlap / max(len(set(query_tokens)), 1)
    density = overlap / math.sqrt(len(span_tokens))
    return round(coverage + density, 6)


def retrieve(question_text, spans, top_k=2):
    query_tokens = tokenize(question_text)
    ranked = []

    for span in spans:
        score = score_span(query_tokens, span["text"])
        ranked.append((score, span["span_id"], span))

    ranked.sort(key=lambda item: (-item[0], item[1]))

    results = []
    for rank, (score, _span_id, span) in enumerate(ranked[:top_k], start=1):
        results.append(
            {
                "rank": rank,
                "evidence_id": span["span_id"],
                "source_doc_id": span["source_doc_id"],
                "source_uri": span["source_uri"],
                "text": span["text"],
                "score": score,
                "retriever_name": "offline_lexical",
                "ledger_span_id": span["ledger_span_id"],
                "source_hash": span["source_hash"],
                "replay_path": span["replay_path"],
            }
        )

    return results
