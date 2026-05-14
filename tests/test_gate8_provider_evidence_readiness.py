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


CANDIDATE_REVIEWED_EVIDENCE_IDS = {
    "official_pricing_source",
    "official_model_docs_source",
    "official_terms_privacy_source",
    "model_id_version_source",
    "context_window_source",
    "output_limit_source",
    "rate_limit_or_throughput_source",
}


def _write_ready_registry(path, provider="openai", model="gpt-4.1"):
    lines = [
        "gate: gate8_main_comparison",
        "stage: gate8i_provider_evidence_readiness",
        "status: ready",
        "authorized_to_run: true",
        "provider_evidence_locked: true",
        "provider_selected: true",
        f"provider: {provider}",
        f"model: {model}",
        "evidence_slots:",
    ]
    for evidence_id in sorted(EXPECTED_EVIDENCE_IDS):
        lines.extend(
            [
                f"  - evidence_id: {evidence_id}",
                f"    official_source_url: https://example.test/{evidence_id}",
                "    checked_at: 2026-05-14",
                "    evidence_status: reviewed",
                "    reviewer: qa-review",
            ]
        )
    lines.append("blockers:")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_candidate_registry(path):
    lines = [
        "version: 1",
        "gate: gate8_main_comparison",
        "stage: gate8k_openai_provider_evidence_candidate_lock",
        "status: readiness_in_progress",
        "authorized_to_run: false",
        "purpose: non_executable_provider_evidence_registry",
        "provider_evidence_candidate_locked: true",
        "provider_candidate_selected: true",
        "candidate_provider: openai",
        "candidate_model: gpt-5.4-mini",
        "candidate_model_snapshot: gpt-5.4-mini-2026-03-17",
        "provider_evidence_locked: false",
        "provider_selected: false",
        "provider: unset",
        "model: unset",
        "candidate_checked_at: 2026-05-14",
        "candidate_recheck_required_on_run_date: true",
        "context_window_tokens: 400000",
        "max_output_tokens: 128000",
        "evidence_slots:",
    ]
    urls = {
        "official_pricing_source": "https://platform.openai.com/docs/pricing/",
        "official_model_docs_source": "https://developers.openai.com/api/docs/models/gpt-5.4-mini",
        "official_terms_privacy_source": "https://openai.com/policies/service-terms/",
        "model_id_version_source": "https://developers.openai.com/api/docs/models/gpt-5.4-mini",
        "context_window_source": "https://developers.openai.com/api/docs/models/gpt-5.4-mini",
        "output_limit_source": "https://developers.openai.com/api/docs/models/gpt-5.4-mini",
        "rate_limit_or_throughput_source": "https://developers.openai.com/api/docs/models",
    }
    for evidence_id in sorted(CANDIDATE_REVIEWED_EVIDENCE_IDS):
        lines.extend(
            [
                f"  - evidence_id: {evidence_id}",
                "    required_for: provider_candidate_validation",
                f"    official_source_url: {urls[evidence_id]}",
                "    checked_at: 2026-05-14",
                "    evidence_status: reviewed",
                "    reviewer: codex",
                "    notes: official_openai_candidate_source_checked_for_gate8k",
            ]
        )
    for evidence_id in ("api_key_or_runtime_availability_note", "cost_budget_approval_note"):
        lines.extend(
            [
                f"  - evidence_id: {evidence_id}",
                "    required_for: execution_authorization",
                "    official_source_url: unset",
                "    checked_at: unset",
                "    evidence_status: missing",
                "    reviewer: unset",
                "    notes: intentionally_unresolved_until_execution_freeze",
            ]
        )
    lines.extend(
        [
            "blockers:",
            "  - provider_evidence_not_locked",
            "  - provider_not_selected",
            "  - model_not_selected",
            "  - api_key_or_runtime_availability_note_missing",
            "  - cost_budget_approval_note_missing",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_candidate_provider_decision(path):
    path.write_text(
        "\n".join(
            [
                "version: 1",
                "gate: gate8_main_comparison",
                "stage: gate8k_provider_decision_candidate",
                "status: readiness_in_progress",
                "selected: false",
                "provider: unset",
                "model: unset",
                "candidate_provider: openai",
                "candidate_model: gpt-5.4-mini",
                "candidate_model_snapshot: gpt-5.4-mini-2026-03-17",
                "run_authorized: false",
            ]
        ),
        encoding="utf-8",
    )


def _write_provider_decision(path, provider, model):
    path.write_text(
        "\n".join(
            [
                "gate: gate8_main_comparison",
                "stage: gate8i_provider_decision",
                "selected: true",
                f"provider: {provider}",
                f"model: {model}",
                "run_authorized: true",
            ]
        ),
        encoding="utf-8",
    )


def test_registry_contains_all_required_evidence_slots():
    inputs = load_provider_evidence_inputs(REGISTRY, PROVIDER_DECISION)

    assert {slot["evidence_id"] for slot in inputs.evidence_slots} == EXPECTED_EVIDENCE_IDS
    assert inputs.registry["authorized_to_run"] is False
    assert inputs.registry["provider_evidence_candidate_locked"] is True
    assert inputs.registry["provider_candidate_selected"] is True
    assert inputs.registry["candidate_provider"] == "openai"
    assert inputs.registry["candidate_model"] == "gpt-5.4-mini"
    assert inputs.registry["candidate_model_snapshot"] == "gpt-5.4-mini-2026-03-17"
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
    assert summary["provider_candidate_ready"] is True
    assert summary["provider_evidence_ready"] is False
    assert summary["authorized_to_run"] is False
    assert summary["provider_selected"] is False
    assert summary["candidate_provider"] == "openai"
    assert summary["candidate_model"] == "gpt-5.4-mini"
    assert summary["candidate_model_snapshot"] == "gpt-5.4-mini-2026-03-17"
    assert summary["missing_candidate_evidence_ids"] == []
    assert summary["missing_evidence_ids"] == [
        "api_key_or_runtime_availability_note",
        "cost_budget_approval_note",
    ]
    assert summary["validation_errors"] == []
    assert "provider_evidence_not_locked" in summary["blockers"]
    assert "provider_decision_not_authorized" in summary["blockers"]


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


def test_provider_decision_requires_concrete_provider_and_model_when_selected(tmp_path):
    registry = tmp_path / "provider_evidence_registry.yaml"
    provider_decision = tmp_path / "provider_decision.yaml"
    _write_ready_registry(registry)
    _write_provider_decision(provider_decision, provider="unset", model="unset")

    summary = build_provider_evidence_readiness_summary(
        load_provider_evidence_inputs(registry, provider_decision)
    )

    assert summary["provider_evidence_ready"] is False
    assert "provider_decision_provider_unset" in summary["blockers"]
    assert "provider_decision_model_unset" in summary["blockers"]


def test_provider_decision_must_match_locked_registry_provider_and_model(tmp_path):
    registry = tmp_path / "provider_evidence_registry.yaml"
    provider_decision = tmp_path / "provider_decision.yaml"
    _write_ready_registry(registry, provider="openai", model="gpt-4.1")
    _write_provider_decision(provider_decision, provider="anthropic", model="claude-3-7-sonnet")

    summary = build_provider_evidence_readiness_summary(
        load_provider_evidence_inputs(registry, provider_decision)
    )

    assert summary["provider_evidence_ready"] is False
    assert "provider_decision_provider_mismatch" in summary["blockers"]
    assert "provider_decision_model_mismatch" in summary["blockers"]


def test_execution_ready_registry_does_not_require_candidate_fields(tmp_path):
    registry = tmp_path / "provider_evidence_registry.yaml"
    provider_decision = tmp_path / "provider_decision.yaml"
    _write_ready_registry(registry, provider="openai", model="gpt-4.1")
    _write_provider_decision(provider_decision, provider="openai", model="gpt-4.1")

    summary = build_provider_evidence_readiness_summary(
        load_provider_evidence_inputs(registry, provider_decision)
    )

    assert summary["provider_evidence_ready"] is True
    assert summary["provider_candidate_ready"] is False
    assert "provider_decision_candidate_provider_unset" not in summary["blockers"]
    assert "provider_decision_candidate_model_unset" not in summary["blockers"]
    assert "provider_decision_candidate_snapshot_unset" not in summary["blockers"]
    assert summary["candidate_blockers"] == []
    assert summary["candidate_provider"] == "unset"
    assert summary["candidate_model"] == "unset"
    assert summary["candidate_model_snapshot"] == "unset"
    assert "provider_evidence_candidate_not_locked" not in summary["blockers"]
    assert "provider_candidate_not_selected" not in summary["blockers"]
    assert "candidate_provider_unset" not in summary["blockers"]
    assert "candidate_model_unset" not in summary["blockers"]
    assert "candidate_snapshot_unset" not in summary["blockers"]
    assert "provider_candidate_missing_sources" not in summary["blockers"]
    assert "provider_candidate_unreviewed" not in summary["blockers"]


def test_execution_ready_registry_ignores_stale_decision_candidate_fields(tmp_path):
    registry = tmp_path / "provider_evidence_registry.yaml"
    provider_decision = tmp_path / "provider_decision.yaml"
    _write_ready_registry(registry, provider="openai", model="gpt-4.1")
    _write_provider_decision(provider_decision, provider="openai", model="gpt-4.1")
    provider_decision.write_text(
        provider_decision.read_text(encoding="utf-8")
        + "\n"
        + "\n".join(
            [
                "candidate_provider: openai",
                "candidate_model: gpt-5.4-mini",
                "candidate_model_snapshot: gpt-5.4-mini-2026-03-17",
            ]
        ),
        encoding="utf-8",
    )

    summary = build_provider_evidence_readiness_summary(
        load_provider_evidence_inputs(registry, provider_decision)
    )

    assert summary["provider_evidence_ready"] is True
    assert summary["provider_candidate_ready"] is False
    assert "provider_decision_candidate_provider_unset" not in summary["blockers"]
    assert "provider_decision_candidate_model_unset" not in summary["blockers"]
    assert "provider_decision_candidate_snapshot_unset" not in summary["blockers"]
    assert summary["candidate_blockers"] == []
    assert "provider_evidence_candidate_not_locked" not in summary["blockers"]
    assert "provider_candidate_not_selected" not in summary["blockers"]
    assert "candidate_provider_unset" not in summary["blockers"]
    assert "candidate_model_unset" not in summary["blockers"]
    assert "candidate_snapshot_unset" not in summary["blockers"]
    assert "provider_decision_candidate_provider_mismatch" not in summary["blockers"]
    assert "provider_decision_candidate_model_mismatch" not in summary["blockers"]
    assert "provider_decision_candidate_snapshot_mismatch" not in summary["blockers"]


def test_execution_ready_registry_with_retained_candidate_metadata_stays_ready(tmp_path):
    registry = tmp_path / "provider_evidence_registry.yaml"
    provider_decision = tmp_path / "provider_decision.yaml"
    _write_ready_registry(registry, provider="openai", model="gpt-4.1")
    _write_provider_decision(provider_decision, provider="openai", model="gpt-4.1")
    registry.write_text(
        registry.read_text(encoding="utf-8")
        + "\n"
        + "\n".join(
            [
                "provider_evidence_candidate_locked: true",
                "provider_candidate_selected: true",
                "candidate_provider: openai",
                "candidate_model: gpt-5.4-mini",
                "candidate_model_snapshot: gpt-5.4-mini-2026-03-17",
            ]
        ),
        encoding="utf-8",
    )

    summary = build_provider_evidence_readiness_summary(
        load_provider_evidence_inputs(registry, provider_decision)
    )

    assert summary["provider_evidence_ready"] is True
    assert summary["provider_candidate_ready"] is False


def test_candidate_locked_registry_reports_candidate_ready_but_not_execution_ready(tmp_path):
    registry = tmp_path / "provider_evidence_registry.yaml"
    provider_decision = tmp_path / "provider_decision.yaml"
    _write_candidate_registry(registry)
    _write_candidate_provider_decision(provider_decision)

    summary = build_provider_evidence_readiness_summary(
        load_provider_evidence_inputs(registry, provider_decision)
    )

    assert summary["provider_candidate_ready"] is True
    assert summary["provider_evidence_ready"] is False
    assert summary["provider_candidate_selected"] is True
    assert summary["candidate_provider"] == "openai"
    assert summary["candidate_model"] == "gpt-5.4-mini"
    assert summary["candidate_model_snapshot"] == "gpt-5.4-mini-2026-03-17"
    assert summary["missing_candidate_evidence_ids"] == []
    assert summary["missing_evidence_ids"] == [
        "api_key_or_runtime_availability_note",
        "cost_budget_approval_note",
    ]
    assert "provider_evidence_not_locked" in summary["blockers"]
    assert "provider_decision_not_authorized" in summary["blockers"]


def test_candidate_ready_ignores_missing_final_execution_schema_fields(tmp_path):
    registry = tmp_path / "provider_evidence_registry.yaml"
    provider_decision = tmp_path / "provider_decision.yaml"
    _write_candidate_registry(registry)
    _write_candidate_provider_decision(provider_decision)
    registry.write_text(
        "\n".join(
            line
            for line in registry.read_text(encoding="utf-8").splitlines()
            if not line.startswith(
                (
                    "authorized_to_run:",
                    "provider_evidence_locked:",
                    "provider_selected:",
                    "provider:",
                    "model:",
                )
            )
        ),
        encoding="utf-8",
    )
    provider_decision.write_text(
        "\n".join(
            line
            for line in provider_decision.read_text(encoding="utf-8").splitlines()
            if not line.startswith(
                (
                    "selected:",
                    "provider:",
                    "model:",
                    "run_authorized:",
                )
            )
        ),
        encoding="utf-8",
    )

    summary = build_provider_evidence_readiness_summary(
        load_provider_evidence_inputs(registry, provider_decision)
    )

    assert summary["provider_candidate_ready"] is True
    assert summary["provider_evidence_ready"] is False
    assert summary["validation_errors"]
    assert summary["candidate_validation_errors"] == []
    assert summary["candidate_blockers"] == []


def test_candidate_decision_must_include_candidate_fields(tmp_path):
    registry = tmp_path / "provider_evidence_registry.yaml"
    provider_decision = tmp_path / "provider_decision.yaml"
    _write_candidate_registry(registry)
    _write_candidate_provider_decision(provider_decision)
    provider_decision.write_text(
        "\n".join(
            line
            for line in provider_decision.read_text(encoding="utf-8").splitlines()
            if not line.startswith(
                (
                    "candidate_provider:",
                    "candidate_model:",
                    "candidate_model_snapshot:",
                )
            )
        ),
        encoding="utf-8",
    )

    summary = build_provider_evidence_readiness_summary(
        load_provider_evidence_inputs(registry, provider_decision)
    )

    assert summary["provider_candidate_ready"] is False
    assert "provider_decision_candidate_provider_unset" not in summary["blockers"]
    assert "provider_decision_candidate_model_unset" not in summary["blockers"]
    assert "provider_decision_candidate_snapshot_unset" not in summary["blockers"]
    assert "provider_decision_candidate_provider_unset" in summary["candidate_blockers"]
    assert "provider_decision_candidate_model_unset" in summary["candidate_blockers"]
    assert "provider_decision_candidate_snapshot_unset" in summary["candidate_blockers"]


def test_candidate_decision_must_match_registry_candidate(tmp_path):
    registry = tmp_path / "provider_evidence_registry.yaml"
    provider_decision = tmp_path / "provider_decision.yaml"
    _write_candidate_registry(registry)
    _write_candidate_provider_decision(provider_decision)
    provider_decision.write_text(
        provider_decision.read_text(encoding="utf-8").replace(
            "candidate_model: gpt-5.4-mini",
            "candidate_model: gpt-5.5",
        ),
        encoding="utf-8",
    )

    summary = build_provider_evidence_readiness_summary(
        load_provider_evidence_inputs(registry, provider_decision)
    )

    assert summary["provider_candidate_ready"] is False
    assert "provider_decision_candidate_model_mismatch" not in summary["blockers"]
    assert "provider_decision_candidate_model_mismatch" in summary["candidate_blockers"]


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
    assert payload["provider_candidate_ready"] is True
    assert payload["missing_candidate_evidence_ids"] == []
    assert payload["missing_evidence_ids"] == [
        "api_key_or_runtime_availability_note",
        "cost_budget_approval_note",
    ]
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
