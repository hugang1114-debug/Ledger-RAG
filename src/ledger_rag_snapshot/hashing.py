import hashlib
import json
import re
from pathlib import Path


def sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path, chunk_size=1024 * 1024):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def hash_manifest_entries(entries):
    canonical_entries = sorted(entries, key=lambda item: item["path"])
    payload = json.dumps(canonical_entries, sort_keys=True, separators=(",", ":"))
    return sha256_text(payload)


def _id_part(value):
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return re.sub(r"_+", "_", normalized)


def build_source_snapshot_id(dataset_id, split, source_version, processed_corpus_hash):
    hash_prefix = processed_corpus_hash[:16]
    return "_".join(
        [
            _id_part(dataset_id),
            _id_part(split),
            _id_part(source_version),
            hash_prefix,
        ]
    )
