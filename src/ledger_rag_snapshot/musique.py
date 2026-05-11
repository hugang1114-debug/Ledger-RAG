import json
import re
import shutil
import html
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from ledger_rag_snapshot.hashing import (
    build_source_snapshot_id,
    hash_manifest_entries,
    sha256_file,
    sha256_text,
)


MUSIQUE_REPO_URL = "https://github.com/StonyBrookNLP/musique"
MUSIQUE_DRIVE_FILE_ID = "1tGdADlNjWFaHLeZZGShh2IRcpO6Lv24h"
MUSIQUE_ZIP_URL = f"https://drive.google.com/uc?export=download&id={MUSIQUE_DRIVE_FILE_ID}"
MUSIQUE_EVAL_SCRIPT_URL = "https://raw.githubusercontent.com/StonyBrookNLP/musique/main/evaluate_v1.0.py"
MUSIQUE_LICENSE_URL = "https://raw.githubusercontent.com/StonyBrookNLP/musique/main/LICENSE"
MUSIQUE_LICENSE_NOTE = "CC BY 4.0 per official StonyBrookNLP/musique LICENSE checked for this source snapshot."


class OfficialSourceUnavailable(RuntimeError):
    pass


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


def read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def _question_id(record):
    return str(record.get("id") or record.get("_id"))


def split_member_name(split):
    return f"musique_ans_v1.0_{split}.jsonl"


def find_split_member(zip_path, split):
    target = split_member_name(split)
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        for name in names:
            normalized = name.replace("\\", "/")
            if normalized == f"data/{target}" or normalized == target or normalized.endswith(f"/{target}"):
                return name
    raise ValueError(f"could not find {target} in {zip_path}")


def extract_member(zip_path, member_name, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        content = archive.read(member_name)
    destination.write_bytes(content)
    return destination


def paragraph_idx(paragraph, fallback):
    if "idx" in paragraph:
        return int(paragraph["idx"])
    if "paragraph_idx" in paragraph:
        return int(paragraph["paragraph_idx"])
    return fallback


def paragraph_text(paragraph):
    return normalize_text(paragraph.get("paragraph_text") or paragraph.get("text") or paragraph.get("paragraph") or "")


def paragraph_title(paragraph, idx):
    return normalize_text(paragraph.get("title") or f"paragraph_{idx}")


def process_musique_records(records, split, source_uri):
    corpus_rows = []
    question_rows = []
    split_entries = []

    for record in sorted(records, key=_question_id):
        question_id = _question_id(record)
        idx_to_doc = {}
        context_doc_ids = []

        for fallback_index, paragraph in enumerate(record["paragraphs"]):
            idx = paragraph_idx(paragraph, fallback_index)
            title = paragraph_title(paragraph, idx)
            text = paragraph_text(paragraph)
            source_doc_id = f"musique_{slugify(question_id)}_para_{idx}_{slugify(title)}"
            idx_to_doc[idx] = {
                "source_doc_id": source_doc_id,
                "title": title,
            }
            context_doc_ids.append(source_doc_id)
            corpus_rows.append(
                {
                    "dataset_id": "musique",
                    "split": split,
                    "question_id": question_id,
                    "source_doc_id": source_doc_id,
                    "source_uri": f"{source_uri}#question={question_id}&paragraph={idx}",
                    "title": title,
                    "paragraph_idx": idx,
                    "is_supporting": bool(paragraph.get("is_supporting", False)),
                    "text": text,
                    "source_hash": sha256_text(text),
                }
            )

        support_refs = []
        for paragraph in record["paragraphs"]:
            idx = paragraph_idx(paragraph, 0)
            if not paragraph.get("is_supporting", False):
                continue
            doc = idx_to_doc.get(idx)
            support_refs.append(
                {
                    "paragraph_idx": idx,
                    "title": doc["title"] if doc else paragraph_title(paragraph, idx),
                    "source_doc_id": doc["source_doc_id"] if doc else None,
                }
            )

        question_decomposition = record.get("question_decomposition", [])
        question_rows.append(
            {
                "dataset_id": "musique",
                "split": split,
                "question_id": question_id,
                "question_text": normalize_text(record["question"]),
                "answer": normalize_text(record.get("answer", "")),
                "answer_aliases": record.get("answer_aliases", []),
                "answerable": record.get("answerable"),
                "support_evidence_refs": support_refs,
                "question_decomposition": question_decomposition,
                "context_source_doc_ids": context_doc_ids,
            }
        )
        split_entries.append(
            {
                "question_id": question_id,
                "support_evidence_refs": support_refs,
                "question_decomposition": question_decomposition,
                "context_source_doc_ids": context_doc_ids,
            }
        )

    return {
        "corpus": corpus_rows,
        "questions": question_rows,
        "split_manifest": {
            "dataset_id": "musique",
            "split": split,
            "source_variant": "musique_ans_v1.0",
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


def build_musique_snapshot_from_zip(zip_path, output_root, split, source_url, license_path, eval_script_path, command_record):
    output_dir = Path(output_root) / "musique" / split
    raw_dir = output_dir / "raw"
    extracted_dir = raw_dir / "data"
    processed_dir = output_dir / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    extracted_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    zip_path = Path(zip_path)
    stored_zip_path = raw_dir / "musique_v1.0.zip"
    if zip_path.resolve() != stored_zip_path.resolve():
        shutil.copyfile(zip_path, stored_zip_path)

    split_member = find_split_member(stored_zip_path, split)
    extracted_split_path = extract_member(stored_zip_path, split_member, extracted_dir / split_member_name(split))
    raw_entries = [_manifest_entry(output_dir, stored_zip_path), _manifest_entry(output_dir, extracted_split_path)]

    with zipfile.ZipFile(stored_zip_path) as archive:
        leakage_members = [
            name
            for name in archive.namelist()
            if name.replace("\\", "/").endswith("/dev_test_singlehop_questions_v1.0.json")
            or name == "dev_test_singlehop_questions_v1.0.json"
        ]
        if leakage_members:
            extracted_leakage_path = extract_member(stored_zip_path, leakage_members[0], extracted_dir / "dev_test_singlehop_questions_v1.0.json")
            raw_entries.append(_manifest_entry(output_dir, extracted_leakage_path))

    if license_path:
        license_source = Path(license_path)
        stored_license_path = raw_dir / "LICENSE"
        if license_source.resolve() != stored_license_path.resolve():
            shutil.copyfile(license_source, stored_license_path)
        raw_entries.append(_manifest_entry(output_dir, stored_license_path))

    if eval_script_path:
        eval_source = Path(eval_script_path)
        stored_eval_path = raw_dir / "evaluate_v1.0.py"
        if eval_source.resolve() != stored_eval_path.resolve():
            shutil.copyfile(eval_source, stored_eval_path)
        raw_entries.append(_manifest_entry(output_dir, stored_eval_path))

    records = read_jsonl(extracted_split_path)
    processed = process_musique_records(records, split=split, source_uri=source_url)

    corpus_path = processed_dir / "corpus.jsonl"
    questions_path = processed_dir / "questions.jsonl"
    split_manifest_path = processed_dir / "split_manifest.json"
    raw_manifest_path = output_dir / "raw_manifest.json"
    snapshot_record_path = output_dir / "snapshot_record.json"

    write_jsonl(corpus_path, processed["corpus"])
    write_jsonl(questions_path, processed["questions"])
    write_json(split_manifest_path, processed["split_manifest"])

    raw_manifest = {
        "dataset_id": "musique",
        "split": split,
        "official_url": MUSIQUE_REPO_URL,
        "source_url": source_url,
        "files": sorted(raw_entries, key=lambda item: item["path"]),
    }
    write_json(raw_manifest_path, raw_manifest)

    raw_data_hash = hash_manifest_entries(raw_manifest["files"])
    processed_corpus_hash = hash_rows(processed["corpus"])
    split_hash = hash_split_manifest(processed["split_manifest"])
    source_snapshot_id = build_source_snapshot_id(
        dataset_id="musique",
        split=split,
        source_version="official",
        processed_corpus_hash=processed_corpus_hash,
    )

    snapshot_record = {
        "dataset_id": "musique",
        "dataset_name": "MuSiQue",
        "decision": "main_v1",
        "split": split,
        "official_url": MUSIQUE_REPO_URL,
        "source_url": source_url,
        "license_note": MUSIQUE_LICENSE_NOTE,
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
            "MuSiQue-Answerable dev source snapshot only; retrieval index is not built in Gate 8D.",
            "Dataset files are local artifacts under ignored datasets/ storage.",
            "MuSiQue seed-dataset leakage caution is preserved through the extracted dev_test_singlehop_questions file when present.",
        ],
    }
    write_json(snapshot_record_path, snapshot_record)
    return snapshot_record


def update_musique_registry_record(registry, snapshot_record):
    updated = json.loads(json.dumps(registry))
    for record in updated["snapshots"]:
        if record["dataset_id"] != "musique":
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
    raise ValueError("musique record not found in registry")


def download_official_file(url, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=60) as response, destination.open("wb") as handle:
            shutil.copyfileobj(response, handle)
    except Exception as exc:
        raise OfficialSourceUnavailable(f"official source unavailable: {url}: {exc}") from exc
    return destination


def _tag_attributes(tag):
    return {
        html.unescape(key): html.unescape(value)
        for key, value in re.findall(r'([A-Za-z_:][-A-Za-z0-9_:.]*)="([^"]*)"', tag)
    }


def google_drive_confirmation_url(html_text, file_id):
    href_match = re.search(r'href="([^"]*(?:/uc\?|drive\.usercontent\.google\.com/download)[^"]*)"', html_text)
    if href_match:
        href = html.unescape(href_match.group(1))
        if href.startswith("/"):
            return "https://drive.google.com" + href
        return href

    form_match = re.search(r'<form[^>]*id="download-form"[^>]*>(.*?)</form>', html_text, flags=re.IGNORECASE | re.DOTALL)
    if not form_match:
        return None

    form_tag_start = html_text.rfind("<form", 0, form_match.start(1))
    form_tag_end = html_text.find(">", form_tag_start)
    form_tag = html_text[form_tag_start : form_tag_end + 1]
    form_attrs = _tag_attributes(form_tag)
    action = form_attrs.get("action", "https://drive.usercontent.google.com/download")

    params = []
    seen = set()
    for input_match in re.finditer(r"<input\b[^>]*>", form_match.group(1), flags=re.IGNORECASE):
        attrs = _tag_attributes(input_match.group(0))
        name = attrs.get("name")
        if not name:
            continue
        value = attrs.get("value", "")
        params.append((name, value))
        seen.add(name)

    if "id" not in seen:
        params.insert(0, ("id", file_id))
    if "confirm" not in seen:
        return None
    return action + "?" + urllib.parse.urlencode(params)


def download_google_drive_file(file_id, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    first_url = f"https://drive.google.com/uc?export=download&id={urllib.parse.quote(file_id)}"

    try:
        with opener.open(first_url, timeout=60) as response:
            first_payload = response.read()
            final_url = response.geturl()
            content_type = response.headers.get("Content-Type", "")

        if "text/html" not in content_type.lower():
            destination.write_bytes(first_payload)
            return destination

        html_text = first_payload.decode("utf-8", errors="replace")
        confirm_url = google_drive_confirmation_url(html_text, file_id)
        if not confirm_url:
            raise OfficialSourceUnavailable("Google Drive confirmation link not found")
        with opener.open(confirm_url, timeout=60) as response:
            destination.write_bytes(response.read())
        return destination
    except OfficialSourceUnavailable:
        raise
    except Exception as exc:
        raise OfficialSourceUnavailable(f"official source unavailable: {first_url}: {exc}") from exc
