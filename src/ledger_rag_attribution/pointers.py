import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class PointerValidationStatus(str, Enum):
    VALID = "valid_citation"
    NONEXISTENT_CITATION_ID = "nonexistent_citation_id"
    CITATION_ID_NOT_IN_RETRIEVED_EVIDENCE = "citation_id_not_in_retrieved_evidence"
    WRONG_SNAPSHOT_HASH = "wrong_snapshot_hash"
    WRONG_SPAN_HASH = "wrong_span_hash"
    MALFORMED_CITATION_ID = "malformed_citation_id"
    SEMANTICALLY_UNSUPPORTED = "structurally_valid_but_semantically_unsupported_citation"
    OVERCLAIM_PARTIALLY_SUPPORTED = "overclaim_partially_supported_claim"


@dataclass(frozen=True)
class CitationPointer:
    dataset_id: str
    source_id: str
    snapshot_hash: str
    span_id: str
    span_hash: str

    @classmethod
    def parse(cls, citation_id: str) -> "CitationPointer":
        parts = str(citation_id or "").split("/")
        if len(parts) != 5 or any(part == "" for part in parts):
            raise ValueError("citation_id must have five non-empty slash-delimited parts")
        return cls(*parts)

    def to_id(self) -> str:
        return "/".join(
            [
                self.dataset_id,
                self.source_id,
                self.snapshot_hash,
                self.span_id,
                self.span_hash,
            ]
        )


@dataclass(frozen=True)
class EvidenceSpan:
    dataset_id: str
    source_id: str
    snapshot_hash: str
    span_id: str
    text: str
    span_hash: str | None = None
    position: int | None = None
    metadata: dict = field(default_factory=dict)

    def citation_pointer(self) -> CitationPointer:
        return CitationPointer(
            dataset_id=self.dataset_id,
            source_id=self.source_id,
            snapshot_hash=self.snapshot_hash,
            span_id=self.span_id,
            span_hash=self.span_hash or compute_span_hash(self.text),
        )


@dataclass(frozen=True)
class PointerValidationResult:
    citation_id: str
    status: PointerValidationStatus
    structurally_valid: bool
    semantic_status: str | None = None
    pointer: CitationPointer | None = None
    details: dict = field(default_factory=dict)


def compute_span_hash(text: str) -> str:
    normalized = "\n".join(line.rstrip() for line in str(text).strip().splitlines())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def build_citation_id(span: EvidenceSpan) -> str:
    return span.citation_pointer().to_id()


def validation_error(status: PointerValidationStatus) -> str:
    return {
        PointerValidationStatus.VALID: "none",
        PointerValidationStatus.NONEXISTENT_CITATION_ID: "nonexistent_citation_id",
        PointerValidationStatus.CITATION_ID_NOT_IN_RETRIEVED_EVIDENCE: "not_in_retrieved_evidence",
        PointerValidationStatus.WRONG_SNAPSHOT_HASH: "wrong_snapshot_hash",
        PointerValidationStatus.WRONG_SPAN_HASH: "wrong_span_hash",
        PointerValidationStatus.MALFORMED_CITATION_ID: "malformed_citation_id",
        PointerValidationStatus.SEMANTICALLY_UNSUPPORTED: "none",
        PointerValidationStatus.OVERCLAIM_PARTIALLY_SUPPORTED: "none",
    }[status]


def validation_record(result: PointerValidationResult, claim_id: str = "") -> dict:
    error = validation_error(result.status)
    missing = result.details.get("missing")
    pointer_parsed = result.pointer is not None
    source_exists = pointer_parsed and not (result.status == PointerValidationStatus.NONEXISTENT_CITATION_ID and missing == "source")
    span_exists = source_exists and not (result.status == PointerValidationStatus.NONEXISTENT_CITATION_ID and missing == "span")
    snapshot_replay_success = span_exists and result.status != PointerValidationStatus.WRONG_SNAPSHOT_HASH
    span_hash_match = snapshot_replay_success and result.status != PointerValidationStatus.WRONG_SPAN_HASH
    in_retrieved_evidence = result.status not in {
        PointerValidationStatus.MALFORMED_CITATION_ID,
        PointerValidationStatus.NONEXISTENT_CITATION_ID,
        PointerValidationStatus.CITATION_ID_NOT_IN_RETRIEVED_EVIDENCE,
        PointerValidationStatus.WRONG_SNAPSHOT_HASH,
        PointerValidationStatus.WRONG_SPAN_HASH,
    }
    return {
        "claim_id": claim_id,
        "citation_id": result.citation_id,
        "structural_validity": "valid" if result.structurally_valid else "invalid",
        "validation_error": error,
        "source_exists": bool(source_exists),
        "snapshot_replay_success": bool(snapshot_replay_success),
        "span_replay_success": bool(span_hash_match),
        "span_hash_match": bool(span_hash_match),
        "in_retrieved_evidence": bool(in_retrieved_evidence),
        "semantic_support": result.semantic_status or "pending",
        "validator_status": result.status.value,
    }


def _index_spans(spans: Iterable[EvidenceSpan]):
    source_keys = set()
    span_keys = {}
    for span in spans:
        source_keys.add((span.dataset_id, span.source_id))
        key = (span.dataset_id, span.source_id, span.span_id)
        span_keys.setdefault(key, []).append(span)
    return source_keys, span_keys


def validate_citation(
    citation_id: str,
    *,
    ledger_spans: Iterable[EvidenceSpan],
    retrieved_citation_ids: Iterable[str],
    semantic_label: str | None = None,
) -> PointerValidationResult:
    try:
        pointer = CitationPointer.parse(citation_id)
    except ValueError as exc:
        return PointerValidationResult(
            citation_id=str(citation_id or ""),
            status=PointerValidationStatus.MALFORMED_CITATION_ID,
            structurally_valid=False,
            details={"reason": str(exc)},
        )

    source_keys, span_keys = _index_spans(ledger_spans)
    if (pointer.dataset_id, pointer.source_id) not in source_keys:
        return PointerValidationResult(
            citation_id=pointer.to_id(),
            status=PointerValidationStatus.NONEXISTENT_CITATION_ID,
            structurally_valid=False,
            pointer=pointer,
            details={"missing": "source"},
        )

    candidates = span_keys.get((pointer.dataset_id, pointer.source_id, pointer.span_id), [])
    if not candidates:
        return PointerValidationResult(
            citation_id=pointer.to_id(),
            status=PointerValidationStatus.NONEXISTENT_CITATION_ID,
            structurally_valid=False,
            pointer=pointer,
            details={"missing": "span"},
        )

    snapshot_candidates = [span for span in candidates if span.snapshot_hash == pointer.snapshot_hash]
    if not snapshot_candidates:
        return PointerValidationResult(
            citation_id=pointer.to_id(),
            status=PointerValidationStatus.WRONG_SNAPSHOT_HASH,
            structurally_valid=False,
            pointer=pointer,
            details={"available_snapshot_hashes": sorted({span.snapshot_hash for span in candidates})},
        )

    if not any((span.span_hash or compute_span_hash(span.text)) == pointer.span_hash for span in snapshot_candidates):
        return PointerValidationResult(
            citation_id=pointer.to_id(),
            status=PointerValidationStatus.WRONG_SPAN_HASH,
            structurally_valid=False,
            pointer=pointer,
            details={"available_span_hashes": sorted({span.span_hash or compute_span_hash(span.text) for span in snapshot_candidates})},
        )

    if pointer.to_id() not in set(retrieved_citation_ids):
        return PointerValidationResult(
            citation_id=pointer.to_id(),
            status=PointerValidationStatus.CITATION_ID_NOT_IN_RETRIEVED_EVIDENCE,
            structurally_valid=False,
            pointer=pointer,
        )

    if semantic_label in {"unsupported", "contradictory", "insufficient_evidence"}:
        return PointerValidationResult(
            citation_id=pointer.to_id(),
            status=PointerValidationStatus.SEMANTICALLY_UNSUPPORTED,
            structurally_valid=True,
            semantic_status=semantic_label,
            pointer=pointer,
        )

    if semantic_label in {"partially_supported", "overclaim"}:
        return PointerValidationResult(
            citation_id=pointer.to_id(),
            status=PointerValidationStatus.OVERCLAIM_PARTIALLY_SUPPORTED,
            structurally_valid=True,
            semantic_status=semantic_label,
            pointer=pointer,
        )

    return PointerValidationResult(
        citation_id=pointer.to_id(),
        status=PointerValidationStatus.VALID,
        structurally_valid=True,
        semantic_status=semantic_label,
        pointer=pointer,
    )
