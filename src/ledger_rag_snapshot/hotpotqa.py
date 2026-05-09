import json
import re
import shutil
import urllib.request
from pathlib import Path

from ledger_rag_snapshot.hashing import (
    build_source_snapshot_id,
    hash_manifest_entries,
    sha256_file,
    sha256_text,
)


HOTPOTQA_HOMEPAGE = "https://hotpotqa.github.io/"
HOTPOTQA_DEV_DISTRACTOR_URL = "http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json"
HOTPOTQA_EVAL_SCRIPT_URL = "https://raw.githubusercontent.com/hotpotqa/hotpot/master/hotpot_evaluate_v1.py"
HOTPOTQA_LICENSE_NOTE = "CC BY-SA 4.0 per official HotpotQA homepage checked for Gate 4 and used for this source snapshot."


class OfficialSourceUnavailable(RuntimeError):
    pass


def load_hotpotqa_records(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_text(value):
    return re.sub(r"\s+", " ", value).strip()


def slugify(value):
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return re.sub(r"_+", "_", normalized) or "untitled"


def json_dumps(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path, rows):
    with Path(path).open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json_dumps(row) + "\n")


def _question_id(record):
    return str(record.get("_id") or record.get("id"))


def process_hotpotqa_records(records, split, source_uri):
    corpus_rows = []
    question_rows = []
    split_entries = []

    for record in sorted(records, key=_question_id):
        question_id = _question_id(record)
        title_to_doc = {}
        context_doc_ids = []

        for context_index, context_item in enumerate(record["context"]):
            title = normalize_text(context_item[0])
            sentences = [normalize_text(sentence) for sentence in context_item[1]]
            source_doc_id = f"hotpotqa_{slugify(question_id)}_doc_{context_index}_{slugify(title)}"
            sentence_rows = [
                {
                    "sentence_id": f"{source_doc_id}_sent_{sentence_index}",
                    "sentence_index": sentence_index,
                    "text": sentence,
                    "sentence_hash": sha256_text(sentence),
                }
                for sentence_index, sentence in enumerate(sentences)
            ]
            text = " ".join(sentences)

            title_to_doc[title] = {
                "source_doc_id": source_doc_id,
                "sentence_count": len(sentences),
            }
            context_doc_ids.append(source_doc_id)
            corpus_rows.append(
                {
                    "dataset_id": "hotpotqa",
                    "split": split,
                    "question_id": question_id,
                    "source_doc_id": source_doc_id,
                    "source_uri": f"{source_uri}#question={question_id}&context={context_index}",
                    "title": title,
                    "context_index": context_index,
                    "sentences": sentence_rows,
                    "text": text,
                    "source_hash": sha256_text(text),
                }
            )

        support_refs = []
        for title, sentence_index in record["supporting_facts"]:
            normalized_title = normalize_text(title)
            doc = title_to_doc.get(normalized_title)
            source_doc_id = doc["source_doc_id"] if doc else None
            support_refs.append(
                {
                    "title": normalized_title,
                    "sentence_index": int(sentence_index),
                    "source_doc_id": source_doc_id,
                    "sentence_id": f"{source_doc_id}_sent_{int(sentence_index)}" if source_doc_id else None,
                }
            )

        question_rows.append(
            {
                "dataset_id": "hotpotqa",
                "split": split,
                "question_id": question_id,
                "question_text": normalize_text(record["question"]),
                "answer": normalize_text(record["answer"]),
                "question_type": record.get("type"),
                "level": record.get("level"),
                "support_evidence_refs": support_refs,
                "context_source_doc_ids": context_doc_ids,
            }
        )
        split_entries.append(
            {
                "question_id": question_id,
                "support_evidence_refs": support_refs,
                "context_source_doc_ids": context_doc_ids,
            }
        )

    return {
        "corpus": corpus_rows,
        "questions": question_rows,
        "split_manifest": {
            "dataset_id": "hotpotqa",
            "split": split,
            "question_count": len(question_rows),
            "question_ids": [row["question_id"] for row in question_rows],
            "entries": split_entries,
        },
    }


def hash_rows(rows):
    payload = "".join(json_dumps(row) + "\n" for row in rows)
    return sha256_text(payload)


def hash_split_manifest(split_manifest):
    return sha256_text(json_dumps(split_manifest))


def _manifest_entry(root, path):
    local_path = Path(path)
    return {
        "path": local_path.relative_to(root).as_posix(),
        "size_bytes": local_path.stat().st_size,
        "sha256": sha256_file(local_path),
    }


def build_hotpotqa_snapshot_from_raw(raw_path, output_root, split, source_url, eval_script_path, command_record):
    output_dir = Path(output_root) / "hotpotqa" / split
    raw_dir = output_dir / "raw"
    processed_dir = output_dir / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    raw_path = Path(raw_path)
    stored_raw_path = raw_dir / "hotpot_dev_distractor_v1.json"
    if raw_path.resolve() != stored_raw_path.resolve():
        shutil.copyfile(raw_path, stored_raw_path)

    raw_entries = [_manifest_entry(output_dir, stored_raw_path)]
    if eval_script_path:
        eval_path = Path(eval_script_path)
        stored_eval_path = raw_dir / "hotpot_evaluate_v1.py"
        if eval_path.resolve() != stored_eval_path.resolve():
            shutil.copyfile(eval_path, stored_eval_path)
        raw_entries.append(_manifest_entry(output_dir, stored_eval_path))

    records = load_hotpotqa_records(stored_raw_path)
    processed = process_hotpotqa_records(records, split=split, source_uri=source_url)

    corpus_path = processed_dir / "corpus.jsonl"
    questions_path = processed_dir / "questions.jsonl"
    split_manifest_path = processed_dir / "split_manifest.json"
    raw_manifest_path = output_dir / "raw_manifest.json"
    snapshot_record_path = output_dir / "snapshot_record.json"

    write_jsonl(corpus_path, processed["corpus"])
    write_jsonl(questions_path, processed["questions"])
    write_json(split_manifest_path, processed["split_manifest"])

    raw_manifest = {
        "dataset_id": "hotpotqa",
        "split": split,
        "official_url": HOTPOTQA_HOMEPAGE,
        "source_url": source_url,
        "files": sorted(raw_entries, key=lambda item: item["path"]),
    }
    write_json(raw_manifest_path, raw_manifest)

    raw_data_hash = hash_manifest_entries(raw_manifest["files"])
    processed_corpus_hash = hash_rows(processed["corpus"])
    split_hash = hash_split_manifest(processed["split_manifest"])
    source_snapshot_id = build_source_snapshot_id(
        dataset_id="hotpotqa",
        split=split,
        source_version="official",
        processed_corpus_hash=processed_corpus_hash,
    )

    snapshot_record = {
        "dataset_id": "hotpotqa",
        "dataset_name": "HotpotQA",
        "decision": "main_v1",
        "split": split,
        "official_url": HOTPOTQA_HOMEPAGE,
        "source_url": source_url,
        "license_note": HOTPOTQA_LICENSE_NOTE,
        "source_snapshot_id": source_snapshot_id,
        "dataset_path": output_dir.as_posix(),
        "raw_data_hash": raw_data_hash,
        "processed_corpus_hash": processed_corpus_hash,
        "split_hash": split_hash,
        "build_command_record": command_record,
        "retrieval_index_path": "unset",
        "storage_class": "small",
        "status": "source_ready",
        "record_count": len(records),
        "corpus_doc_count": len(processed["corpus"]),
        "question_count": len(processed["questions"]),
        "paths": {
            "raw_manifest": raw_manifest_path.as_posix(),
            "corpus": corpus_path.as_posix(),
            "questions": questions_path.as_posix(),
            "split_manifest": split_manifest_path.as_posix(),
            "snapshot_record": snapshot_record_path.as_posix(),
        },
        "notes": [
            "HotpotQA dev distractor source snapshot only; retrieval index is not built in Gate 8B.",
            "Dataset files are local artifacts under ignored datasets/ storage.",
        ],
    }
    write_json(snapshot_record_path, snapshot_record)
    return snapshot_record


def update_hotpotqa_registry_record(registry, snapshot_record):
    updated = json.loads(json.dumps(registry))
    for record in updated["snapshots"]:
        if record["dataset_id"] != "hotpotqa":
            continue
        record.update(
            {
                "split": snapshot_record["split"],
                "official_url": snapshot_record["official_url"],
                "license_note": snapshot_record["license_note"],
                "source_snapshot_id": snapshot_record["source_snapshot_id"],
                "dataset_path": snapshot_record["dataset_path"],
                "raw_data_hash": snapshot_record["raw_data_hash"],
                "processed_corpus_hash": snapshot_record["processed_corpus_hash"],
                "split_hash": snapshot_record["split_hash"],
                "build_command_record": snapshot_record["build_command_record"],
                "retrieval_index_path": "unset",
                "storage_class": "small",
                "status": "source_ready",
                "notes": snapshot_record["notes"],
            }
        )
        return updated
    raise ValueError("hotpotqa record not found in registry")


def download_official_file(url, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=60) as response, destination.open("wb") as handle:
            shutil.copyfileobj(response, handle)
    except Exception as exc:
        raise OfficialSourceUnavailable(f"official source unavailable: {url}: {exc}") from exc
    return destination
