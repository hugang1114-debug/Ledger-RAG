import json
import subprocess
import sys
from pathlib import Path

from ledger_rag_gate8.provider_evidence_readiness import (
    EXPECTED_EVIDENCE_IDS,
    build_provider_evidence_readiness_summary,
    load_provider_evidence_inputs,
    parse_evidence_slots,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "configs" / "gate8" / "provider_evidence_registry.yaml"
PROVIDER_DECISION = ROOT / "configs" / "gate8" / "provider_decision.yaml"
CLI = ROOT / "scripts" / "check_gate8_provider_evidence_readiness.py"


def test_registry_contains_all_required_evidence_slots():
    inputs = load_provider_evidence_inputs(REGISTRY, PROVIDER_DECISION)

    assert {slot["evidence_id"] for slot in inputs.evidence_slots} == EXPECTED_EVIDENCE_IDS
    assert inputs.registry["authorized_to_run"] is False
    assert inputs.registry["provider_evidence_locked"] is False
    assert inputs.registry["provider_selected"] is False
    assert inputs.registry["provider"] == "unset"
    assert inputs.registry["model"] == "unset"


def test_default_summary_is_valid_but_not_ready():
    summary = build_provider_evidence_readiness_summary(
        load_provider_evidence_inputs(REGISTRY, PROVIDER_DECISION)
    )

    assert summary["gate"] == "gate8_main_comparison"
    assert summary["stage"] == "gate8i_provider_evidence_readiness"
    assert summary["provider_evidence_ready"] is False
    assert summary["authorized_to_run"] is False
    assert summary["provider_selected"] is False
    assert summary["provider"] == "unset"
    assert summary["model"] == "unset"
    assert summary["missing_evidence_ids"] == sorted(EXPECTED_EVIDENCE_IDS)
    assert summary["unreviewed_evidence_ids"] == sorted(EXPECTED_EVIDENCE_IDS)
    assert summary["validation_errors"] == []
    assert "provider_evidence_not_locked" in summary["blockers"]
    assert "provider_not_selected" in summary["blockers"]
    assert "model_not_selected" in summary["blockers"]


def test_parse_evidence_slots_reads_list_of_maps(tmp_path):
    registry = tmp_path / "registry.yaml"
    registry.write_text(
        "\n".join(
            [
                "evidence_slots:",
                "  - evidence_id: official_pricing_source",
                "    official_source_url: unset",
                "    evidence_status: missing",
                "  - evidence_id: official_model_docs_source",
                "    official_source_url: https://example.test/model-docs",
                "    evidence_status: reviewed",
                "blockers:",
                "  - provider_evidence_not_locked",
            ]
        ),
        encoding="utf-8",
    )

    slots = parse_evidence_slots(registry)

    assert slots == [
        {
            "evidence_id": "official_pricing_source",
            "official_source_url": "unset",
            "evidence_status": "missing",
        },
        {
            "evidence_id": "official_model_docs_source",
            "official_source_url": "https://example.test/model-docs",
            "evidence_status": "reviewed",
        },
    ]


def test_missing_evidence_slot_is_reported(tmp_path):
    registry = tmp_path / "provider_evidence_registry.yaml"
    provider_decision = tmp_path / "provider_decision.yaml"
    registry.write_text(
        "\n".join(
            [
                "gate: gate8_main_comparison",
                "stage: gate8i_provider_evidence_readiness",
                "authorized_to_run: false",
                "provider_evidence_locked: false",
                "provider_selected: false",
                "provider: unset",
                "model: unset",
                "evidence_slots:",
                "  - evidence_id: official_pricing_source",
                "    evidence_status: missing",
                "blockers:",
            ]
        ),
        encoding="utf-8",
    )
    provider_decision.write_text(
        "\n".join(
            [
                "selected: false",
                "provider: unset",
                "model: unset",
                "run_authorized: false",
            ]
        ),
        encoding="utf-8",
    )

    summary = build_provider_evidence_readiness_summary(
        load_provider_evidence_inputs(registry, provider_decision)
    )

    assert "official_model_docs_source" in summary["missing_evidence_ids"]
    assert "provider_evidence_missing_slots" in summary["blockers"]


def test_provider_decision_references_registry_but_remains_unselected():
    summary = build_provider_evidence_readiness_summary(
        load_provider_evidence_inputs(REGISTRY, PROVIDER_DECISION)
    )

    assert summary["checked_configs"]["provider_decision"].replace("\\", "/").endswith(
        "configs/gate8/provider_decision.yaml"
    )
    assert summary["provider_decision_selected"] is False
    assert summary["provider_decision_authorized"] is False
    assert "provider_decision_unselected" in summary["blockers"]
    assert "provider_decision_not_authorized" in summary["blockers"]


def test_cli_default_mode_exits_zero_and_reports_not_ready():
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--registry",
            str(REGISTRY),
            "--provider-decision",
            str(PROVIDER_DECISION),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)

    assert payload["provider_evidence_ready"] is False
    assert payload["authorized_to_run"] is False
    assert payload["missing_evidence_ids"] == sorted(EXPECTED_EVIDENCE_IDS)
    assert payload["blockers"]


def test_cli_require_ready_exits_nonzero_while_blockers_remain():
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--registry",
            str(REGISTRY),
            "--provider-decision",
            str(PROVIDER_DECISION),
            "--require-ready",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["provider_evidence_ready"] is False
    assert "provider_evidence_not_locked" in payload["blockers"]
