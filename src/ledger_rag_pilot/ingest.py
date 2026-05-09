import hashlib
import json
import re
from pathlib import Path


def load_fixture(path):
    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_text(text):
    return re.sub(r"\s+", " ", text).strip()


def stable_hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def short_hash(value):
    return stable_hash(value)[:16]


def split_sentences(text):
    normalized = normalize_text(text)
    parts = re.split(r"(?<=[.!?])\s+", normalized)
    return [part.strip() for part in parts if part.strip()]


def ingest_fixture(fixture):
    documents = []
    chunks = []
    spans = []

    for doc_index, document in enumerate(fixture["documents"]):
        source_doc_id = document["source_doc_id"]
        source_uri = document["source_uri"]
        text = normalize_text(document["text"])
        source_hash = stable_hash(text)
        document_id = f"doc_{short_hash(source_doc_id + source_hash)}"
        chunk_id = f"chunk_{short_hash(document_id + ':0')}"

        documents.append(
            {
                "record_type": "document",
                "document_id": document_id,
                "source_doc_id": source_doc_id,
                "source_uri": source_uri,
                "source_hash": source_hash,
                "doc_index": doc_index,
                "text": text,
            }
        )
        chunks.append(
            {
                "record_type": "chunk",
                "chunk_id": chunk_id,
                "document_id": document_id,
                "source_doc_id": source_doc_id,
                "chunk_index": 0,
                "text": text,
                "chunk_hash": stable_hash(text),
            }
        )

        for span_index, sentence in enumerate(split_sentences(text)):
            span_hash = stable_hash(sentence)
            span_id = f"span_{short_hash(chunk_id + ':' + str(span_index) + ':' + span_hash)}"
            spans.append(
                {
                    "record_type": "span",
                    "span_id": span_id,
                    "ledger_span_id": span_id,
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "source_doc_id": source_doc_id,
                    "source_uri": source_uri,
                    "span_index": span_index,
                    "text": sentence,
                    "span_hash": span_hash,
                    "source_hash": source_hash,
                    "replay_path": f"{source_uri}#span={span_index}",
                }
            )

    return {"documents": documents, "chunks": chunks, "spans": spans}

